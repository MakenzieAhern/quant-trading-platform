from datetime import datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Any

from app.domain.market import Bar
from app.domain.markets import CorporateAction, CorporateActionType
from app.domain.markets.corporate_actions import require_supported_corporate_action
from app.domain.trading import Fill, OrderSide, PortfolioSnapshot, Position
from app.event import Event, EventBus, EventType

PORTFOLIO_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
ZERO = Decimal(0)
RIGHTS_ISSUE_POLICY = "CN_A_RIGHTS_ISSUE_POLICY_V1"
RIGHTS_ENTITLEMENT_POLICY = "NO_SUBSCRIPTION_NO_MONETIZATION_V1"
RIGHTS_ISSUE_PARTICIPATION = "DECLINE_SUBSCRIPTION"


class PortfolioError(ValueError):
    """Raised when portfolio events violate chronological or numeric contracts."""


class PortfolioEngine:
    """Record fills and completed-Bar marks without making trading decisions."""

    def __init__(self, event_bus: EventBus, initial_cash: Decimal) -> None:
        if not isinstance(initial_cash, Decimal):
            raise TypeError("initial_cash must be a Decimal instance")
        if not initial_cash.is_finite() or initial_cash <= ZERO:
            raise ValueError("initial_cash must be positive and finite")
        self._event_bus = event_bus
        self._initial_cash = initial_cash
        self._cash = initial_cash
        self._positions: dict[str, Position] = {}
        self._marks: dict[str, Decimal] = {}
        self._snapshots: list[PortfolioSnapshot] = []
        self._cumulative_commission = ZERO
        self._running_peak = initial_cash
        self._last_event_timestamp: datetime | None = None
        self._event_bus.subscribe(EventType.ORDER_FILLED, self._on_fill)
        self._event_bus.subscribe(EventType.MARKET_DATA, self._on_market_data)

    @property
    def initial_cash(self) -> Decimal:
        return self._initial_cash

    @property
    def cash(self) -> Decimal:
        return self._cash

    @property
    def positions(self) -> tuple[Position, ...]:
        return tuple(self._positions[symbol] for symbol in sorted(self._positions))

    @property
    def snapshots(self) -> tuple[PortfolioSnapshot, ...]:
        return tuple(self._snapshots)

    @property
    def latest_snapshot(self) -> PortfolioSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None

    @property
    def marks(self) -> dict[str, Decimal]:
        return {symbol: self._marks[symbol] for symbol in sorted(self._marks)}

    @property
    def cumulative_commission(self) -> Decimal:
        return self._cumulative_commission

    def apply_fill(self, fill: Fill) -> Position:
        self._require_chronological(fill.timestamp, "fill")
        current = self._positions.get(fill.symbol)
        current_quantity = current.quantity if current is not None else ZERO
        current_average = current.average_price if current is not None else ZERO
        current_realized = current.realized_pnl if current is not None else ZERO
        signed_fill_quantity = fill.quantity if fill.side is OrderSide.BUY else -fill.quantity

        with localcontext(PORTFOLIO_CONTEXT):
            notional = fill.quantity * fill.price
            cash_change = -notional if fill.side is OrderSide.BUY else notional
            updated_cash = self._cash + cash_change - fill.commission
            updated_commission = self._cumulative_commission + fill.commission
            new_quantity = current_quantity + signed_fill_quantity
            new_average, realized_change = self._cost_basis_after_fill(
                current_quantity,
                current_average,
                signed_fill_quantity,
                fill.price,
            )
            realized = current_realized + realized_change
            mark = self._marks.get(fill.symbol, fill.price)
            unrealized = new_quantity * (mark - new_average) if new_quantity else ZERO

        updated = Position(
            symbol=fill.symbol,
            quantity=new_quantity,
            average_price=new_average,
            market_price=mark,
            unrealized_pnl=unrealized,
            realized_pnl=realized,
        )
        self._cash = updated_cash
        self._cumulative_commission = updated_commission
        self._positions[fill.symbol] = updated
        self._last_event_timestamp = fill.timestamp
        return updated

    def mark_to_market(self, bar: Bar) -> PortfolioSnapshot:
        self._require_chronological(bar.timestamp, "market data")

        self._marks[bar.symbol] = bar.close
        current = self._positions.get(bar.symbol)
        if current is not None:
            with localcontext(PORTFOLIO_CONTEXT):
                unrealized = current.quantity * (bar.close - current.average_price)
            self._positions[bar.symbol] = current.model_copy(
                update={"market_price": bar.close, "unrealized_pnl": unrealized}
            )

        with localcontext(PORTFOLIO_CONTEXT):
            positions = self.positions
            market_value = sum(
                (position.quantity * position.market_price for position in positions), ZERO
            )
            unrealized_pnl = sum((position.unrealized_pnl for position in positions), ZERO)
            realized_pnl = sum((position.realized_pnl for position in positions), ZERO)
            equity = self._cash + market_value
            running_peak = max(self._running_peak, equity)
            drawdown = equity / running_peak - Decimal(1)

        snapshot = PortfolioSnapshot(
            timestamp=bar.timestamp,
            cash=self._cash,
            positions=positions,
            market_value=market_value,
            equity=equity,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            cumulative_commission=self._cumulative_commission,
            drawdown=drawdown,
        )
        self._running_peak = running_peak
        self._last_event_timestamp = bar.timestamp
        self._snapshots.append(snapshot)
        self._event_bus.publish(
            Event(EventType.PORTFOLIO_UPDATED, snapshot, occurred_at=snapshot.timestamp)
        )
        return snapshot

    def apply_corporate_action(
        self, symbol: str, action: CorporateAction, timestamp: datetime
    ) -> Position | None:
        """Apply only complete, economically reconstructable long-position events."""
        self._require_chronological(timestamp, "corporate action")
        try:
            require_supported_corporate_action(action)
        except ValueError as exc:
            raise PortfolioError(str(exc)) from exc
        current = self._positions.get(symbol)
        if action.action_type is CorporateActionType.RIGHTS_RELATED_EVENT:
            if current is not None and current.quantity < ZERO:
                raise PortfolioError("rights policy is long-only")
            # Decline subscription: no entitlement asset, cash, shares, orders or fills.
            self._last_event_timestamp = timestamp
            return current
        if current is None or current.quantity <= ZERO:
            return current
        if action.action_type is CorporateActionType.CASH_DIVIDEND:
            self._cash += current.quantity * action.cash_per_share
            self._last_event_timestamp = timestamp
            return current
        if action.action_type in {
            CorporateActionType.STOCK_DIVIDEND,
            CorporateActionType.BONUS_SHARE,
        }:
            assert action.share_ratio is not None
            quantity = current.quantity * (Decimal(1) + action.share_ratio)
            average_price = current.average_price / (Decimal(1) + action.share_ratio)
            updated = current.model_copy(
                update={
                    "quantity": quantity,
                    "average_price": average_price,
                    "unrealized_pnl": quantity * (current.market_price - average_price),
                }
            )
            self._positions[symbol] = updated
            self._last_event_timestamp = timestamp
            return updated
        raise PortfolioError("unsupported corporate action type")

    def reset(self) -> None:
        self._cash = self._initial_cash
        self._positions.clear()
        self._marks.clear()
        self._snapshots.clear()
        self._cumulative_commission = ZERO
        self._running_peak = self._initial_cash
        self._last_event_timestamp = None

    def _require_chronological(self, timestamp: datetime, event_name: str) -> None:
        if self._last_event_timestamp is not None and timestamp < self._last_event_timestamp:
            raise PortfolioError(f"{event_name} cannot move portfolio time backwards")

    @staticmethod
    def _cost_basis_after_fill(
        current_quantity: Decimal,
        current_average: Decimal,
        signed_fill_quantity: Decimal,
        fill_price: Decimal,
    ) -> tuple[Decimal, Decimal]:
        if current_quantity == ZERO:
            return fill_price, ZERO
        if (current_quantity > ZERO) == (signed_fill_quantity > ZERO):
            new_quantity = current_quantity + signed_fill_quantity
            weighted_cost = (
                abs(current_quantity) * current_average + abs(signed_fill_quantity) * fill_price
            )
            return weighted_cost / abs(new_quantity), ZERO

        closing_quantity = min(abs(current_quantity), abs(signed_fill_quantity))
        if current_quantity > ZERO:
            realized = closing_quantity * (fill_price - current_average)
        else:
            realized = closing_quantity * (current_average - fill_price)
        new_quantity = current_quantity + signed_fill_quantity
        if new_quantity == ZERO:
            return ZERO, realized
        if (new_quantity > ZERO) != (current_quantity > ZERO):
            return fill_price, realized
        return current_average, realized

    def _on_fill(self, event: Event[Any]) -> None:
        if not isinstance(event.payload, Fill):
            raise TypeError("ORDER_FILLED event payload must be a Fill")
        self.apply_fill(event.payload)

    def _on_market_data(self, event: Event[Any]) -> None:
        if not isinstance(event.payload, Bar):
            raise TypeError("MARKET_DATA event payload must be a Bar")
        self.mark_to_market(event.payload)
