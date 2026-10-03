import hashlib
import json
from collections.abc import Iterable
from datetime import date
from decimal import ROUND_HALF_UP, Context, Decimal, localcontext
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.common import NonNegativeDecimal, PositiveDecimal, UtcDateTime
from app.domain.markets.identifiers import SecurityId


class CorporateActionType(StrEnum):
    CASH_DIVIDEND = "CASH_DIVIDEND"
    STOCK_DIVIDEND = "STOCK_DIVIDEND"
    BONUS_SHARE = "BONUS_SHARE"
    RIGHTS_RELATED_EVENT = "RIGHTS_RELATED_EVENT"
    SPLIT_OR_SHARE_CHANGE = "SPLIT_OR_SHARE_CHANGE"
    MERGER_REORGANIZATION = "MERGER_REORGANIZATION"
    UNKNOWN_UNSUPPORTED = "UNKNOWN_UNSUPPORTED"


class CorporateActionCompleteness(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"


class RightsVariant(StrEnum):
    ORDINARY_NON_TRADABLE = "ORDINARY_NON_TRADABLE"
    TRADABLE = "TRADABLE"
    AUTOMATIC_COMPENSATION = "AUTOMATIC_COMPENSATION"
    MANDATORY_CONVERSION = "MANDATORY_CONVERSION"
    UNUSUAL_INSTRUMENT = "UNUSUAL_INSTRUMENT"


class RightsEventClass(StrEnum):
    STANDARD_DIRECT_SUBSCRIPTION_RIGHTS_ISSUE = "STANDARD_DIRECT_SUBSCRIPTION_RIGHTS_ISSUE"
    SEPARATELY_LISTED_TRADABLE_RIGHT = "SEPARATELY_LISTED_TRADABLE_RIGHT"
    TRANSFERABLE_RIGHTS_INSTRUMENT = "TRANSFERABLE_RIGHTS_INSTRUMENT"
    MANDATORY_CONVERSION = "MANDATORY_CONVERSION"
    CASH_SETTLED_RIGHT = "CASH_SETTLED_RIGHT"
    AUTOMATIC_COMPENSATION = "AUTOMATIC_COMPENSATION"
    RIGHTS_WITH_SEPARATE_MARKET_PRICE = "RIGHTS_WITH_SEPARATE_MARKET_PRICE"
    OTHER_NONSTANDARD_RIGHTS_INSTRUMENT = "OTHER_NONSTANDARD_RIGHTS_INSTRUMENT"


class EntitlementTradability(StrEnum):
    TRADABLE_CONFIRMED = "TRADABLE_CONFIRMED"
    NON_TRADABLE_CONFIRMED = "NON_TRADABLE_CONFIRMED"
    NOT_EVIDENCED = "NOT_EVIDENCED"


class CorporateAction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    security_id: SecurityId
    action_type: CorporateActionType
    announcement_date: date | None = None
    effective_date: date | None = None
    record_date: date | None = None
    ex_date: date | None = None
    payment_date: date | None = None
    listing_date: date | None = None
    cash_per_share: NonNegativeDecimal = Decimal(0)
    share_ratio: NonNegativeDecimal | None = None
    subscription_price: PositiveDecimal | None = None
    subscription_start_date: date | None = None
    subscription_end_date: date | None = None
    subscription_deadline: date | None = None
    eligible_share_basis: PositiveDecimal | None = None
    rights_variant: RightsVariant | None = None
    rights_event_class: RightsEventClass | None = None
    entitlement_tradability: EntitlementTradability = EntitlementTradability.NOT_EVIDENCED
    source_document: str | None = Field(default=None, min_length=1)
    source_url: str | None = Field(default=None, pattern=r"^https://\S+$")
    source_document_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    retrieved_at: UtcDateTime | None = None
    source_provider: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    source_record_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    completeness: CorporateActionCompleteness

    @model_validator(mode="after")
    def prevent_lookahead(self) -> "CorporateAction":
        if (
            self.announcement_date is not None
            and self.ex_date is not None
            and self.announcement_date > self.ex_date
        ):
            raise ValueError("announcement_date must not follow ex_date")
        if self.completeness is CorporateActionCompleteness.COMPLETE and self.ex_date is None:
            raise ValueError("complete corporate actions require an ex-date")
        return self

    def rights_metadata_gaps(self) -> tuple[str, ...]:
        """Metadata completeness is independent of no-subscription accounting safety."""
        required = (
            "announcement_date",
            "effective_date",
            "record_date",
            "ex_date",
            "subscription_start_date",
            "subscription_end_date",
            "subscription_deadline",
            "subscription_price",
            "share_ratio",
            "eligible_share_basis",
            "source_document",
            "source_url",
            "source_document_sha256",
            "retrieved_at",
        )
        return tuple(f"MISSING_{name.upper()}" for name in required if getattr(self, name) is None)

    def rights_issues(self) -> tuple[str, ...]:
        """Material identity/order/provenance only; tradability is not a policy gate."""
        required = (
            "ex_date",
            "effective_date",
            "source_document",
            "source_url",
            "source_document_sha256",
            "retrieved_at",
        )
        issues = [f"MISSING_{name.upper()}" for name in required if getattr(self, name) is None]
        if self.rights_event_class is None:
            issues.append("EVENT_STRUCTURE_NOT_ESTABLISHED")
        elif (
            self.rights_event_class
            is not RightsEventClass.STANDARD_DIRECT_SUBSCRIPTION_RIGHTS_ISSUE
        ):
            issues.append("EXPLICIT_UNSUPPORTED_VARIANT")
        # Preserve legacy explicit variant evidence; never silently overwrite it.
        if self.rights_variant not in (None, RightsVariant.ORDINARY_NON_TRADABLE):
            issues.append("EXPLICIT_UNSUPPORTED_VARIANT")
        if self.completeness is CorporateActionCompleteness.UNSUPPORTED:
            issues.append("EXPLICIT_UNSUPPORTED_VARIANT")
        if self.share_ratio is not None and self.share_ratio <= 0:
            issues.append("NON_POSITIVE_RATIO")
        if self.cash_per_share != 0:
            issues.append("UNSUPPORTED_CASH_COMPONENT")
        if self.effective_date != self.ex_date:
            issues.append("CONTRADICTORY_EFFECTIVE_DATE")
        dates = (self.record_date, self.subscription_start_date, self.subscription_end_date)
        known_dates = [value for value in dates if value is not None]
        if known_dates != sorted(known_dates):
            issues.append("CONTRADICTORY_SUBSCRIPTION_WINDOW")
        if (
            self.subscription_deadline is not None
            and self.subscription_end_date is not None
            and self.subscription_deadline != self.subscription_end_date
        ):
            issues.append("CONTRADICTORY_DEADLINE")
        if (
            self.ex_date is not None
            and self.subscription_end_date is not None
            and self.ex_date <= self.subscription_end_date
        ):
            issues.append("CONTRADICTORY_EX_DATE")
        if (
            self.listing_date is not None
            and self.ex_date is not None
            and self.listing_date < self.ex_date
        ):
            issues.append("CONTRADICTORY_LISTING_DATE")
        return tuple(issues)

    @property
    def rights_classification(self) -> str:
        issues = self.rights_issues()
        if "EXPLICIT_UNSUPPORTED_VARIANT" in issues:
            return "EXPLICIT_UNSUPPORTED_VARIANT"
        if issues:
            return "EVENT_IDENTITY_UNRESOLVED"
        if (
            self.rights_metadata_gaps()
            or self.completeness is not CorporateActionCompleteness.COMPLETE
        ):
            return "STANDARD_PARTIAL_BUT_ACCOUNTING_SAFE"
        return "STANDARD_COMPLETE"

    @property
    def event_checksum(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


def corporate_action_sort_key(action: CorporateAction) -> tuple[date, str, int, str]:
    """Pre-open: cash on old shares, then distributions, then declined rights.

    Unsupported structural events are validated before any session mutation.
    Exact event content breaks ties, never acquisition/input ordering.
    """
    precedence = {
        CorporateActionType.CASH_DIVIDEND: 0,
        CorporateActionType.STOCK_DIVIDEND: 1,
        CorporateActionType.BONUS_SHARE: 2,
        CorporateActionType.RIGHTS_RELATED_EVENT: 3,
        CorporateActionType.SPLIT_OR_SHARE_CHANGE: 4,
        CorporateActionType.MERGER_REORGANIZATION: 5,
        CorporateActionType.UNKNOWN_UNSUPPORTED: 6,
    }
    return (
        action.ex_date or date.max,
        str(action.security_id),
        precedence[action.action_type],
        action.model_dump_json(),
    )


class OrdinaryDistributionInputError(ValueError):
    code = "UNSUPPORTED_ORDINARY_DISTRIBUTION_INPUT"


def require_supported_corporate_action(action: CorporateAction) -> None:
    if action.action_type is CorporateActionType.RIGHTS_RELATED_EVENT:
        if issues := action.rights_issues():
            code = (
                "RIGHTS_EVENT_UNSUPPORTED_VARIANT"
                if "EXPLICIT_UNSUPPORTED_VARIANT" in issues
                else "EVENT_IDENTITY_UNRESOLVED"
            )
            raise ValueError(f"{code}:{action.security_id}:{action.ex_date}:{','.join(issues)}")
        return
    if action.completeness is not CorporateActionCompleteness.COMPLETE:
        raise ValueError("unsupported or incomplete corporate action")
    if action.action_type is CorporateActionType.CASH_DIVIDEND:
        if action.share_ratio not in (None, Decimal(0)):
            raise OrdinaryDistributionInputError("CASH_DIVIDEND_WITH_SHARE_RATIO_UNSUPPORTED")
        return
    if (
        action.action_type in {CorporateActionType.STOCK_DIVIDEND, CorporateActionType.BONUS_SHARE}
        and action.share_ratio is not None
        and action.share_ratio > 0
    ):
        if action.cash_per_share != 0:
            raise OrdinaryDistributionInputError("SHARE_DISTRIBUTION_WITH_CASH_UNSUPPORTED")
        return
    raise ValueError("unsupported corporate action type")


def cash_bonus_reference_price(
    previous_close: Decimal,
    *,
    cash_per_old_share: Decimal,
    aggregate_share_ratio: Decimal,
    minimum_tick: Decimal,
) -> Decimal:
    """Ordinary gross cash plus one aggregate distribution; not rights/conversions."""
    values = (previous_close, cash_per_old_share, aggregate_share_ratio, minimum_tick)
    if (
        not all(value.is_finite() for value in values)
        or previous_close <= cash_per_old_share
        or cash_per_old_share < 0
        or aggregate_share_ratio < 0
        or minimum_tick <= 0
    ):
        raise ValueError("INVALID_CASH_BONUS_REFERENCE_INPUT")
    with localcontext(Context(prec=50)):
        reference = (previous_close - cash_per_old_share) / (Decimal(1) + aggregate_share_ratio)
        rounded = (reference / minimum_tick).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        ) * minimum_tick
    if rounded <= 0:
        raise ValueError("INVALID_CASH_BONUS_REFERENCE_INPUT")
    return rounded


def require_unambiguous_ordinary_distributions(actions: Iterable[CorporateAction]) -> None:
    """Reject duplicate economic legs before accounting; receipt hashes are not identity."""
    identities: set[tuple[SecurityId, date | None, CorporateActionType]] = set()
    share_groups: set[tuple[SecurityId, date | None]] = set()
    for action in actions:
        if action.action_type not in {
            CorporateActionType.CASH_DIVIDEND,
            CorporateActionType.STOCK_DIVIDEND,
            CorporateActionType.BONUS_SHARE,
        }:
            continue
        require_supported_corporate_action(action)
        identity = (action.security_id, action.ex_date, action.action_type)
        if identity in identities:
            raise OrdinaryDistributionInputError("DUPLICATE_ORDINARY_DISTRIBUTION")
        identities.add(identity)
        if action.action_type is not CorporateActionType.CASH_DIVIDEND:
            group = (action.security_id, action.ex_date)
            if group in share_groups:
                # ponytail: one aggregate old-share ratio; separately modeled legs need
                # audited old-share allocation, not sequential multiplicative accounting.
                raise OrdinaryDistributionInputError("MULTIPLE_SHARE_DISTRIBUTIONS_UNSUPPORTED")
            share_groups.add(group)
