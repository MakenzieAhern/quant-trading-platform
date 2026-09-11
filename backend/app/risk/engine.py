from collections.abc import Mapping
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import TypedDict

from app.domain.risk import OrderProposal, RiskConfig, RiskDecision, RiskReasonCode
from app.domain.trading import OrderSide, OrderType, PortfolioSnapshot

RISK_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
ZERO = Decimal(0)


class _DecisionDiagnostics(TypedDict):
    risk_increasing: bool
    reference_price: Decimal
    order_notional: Decimal
    projected_position_quantity: Decimal
    projected_symbol_exposure: Decimal
    projected_gross_exposure: Decimal
    projected_net_exposure: Decimal
    projected_gross_leverage: Decimal | None
    projected_cash: Decimal
    estimated_transaction_cost: Decimal


class RiskEngine:
    """Pure pre-trade evaluator using only observed state and explicit reservations."""

    def __init__(self, config: RiskConfig | None = None) -> None:
        self._config = config or RiskConfig()

    @property
    def config(self) -> RiskConfig:
        return self._config

    def evaluate(
        self,
        proposal: OrderProposal,
        snapshot: PortfolioSnapshot | None,
        marks: Mapping[str, Decimal],
        *,
        reserved_quantities: Mapping[str, Decimal] | None = None,
        reserved_cash_delta: Decimal = ZERO,
        reserved_buying_power: Decimal = ZERO,
        estimated_transaction_cost: Decimal = ZERO,
    ) -> RiskDecision:
        if proposal.quantity <= ZERO:
            return self._reject(
                proposal, RiskReasonCode.INVALID_QUANTITY, "quantity must be positive"
            )
        if proposal.order_type is not OrderType.MARKET and not (
            self._config.allow_limit_orders
            and proposal.order_type is OrderType.LIMIT
            and proposal.limit_price is not None
        ):
            return self._reject(
                proposal,
                RiskReasonCode.UNSUPPORTED_ORDER_TYPE,
                "order type is not enabled or limit price is missing",
            )
        if snapshot is None:
            return self._reject(
                proposal,
                RiskReasonCode.INVALID_PORTFOLIO_STATE,
                "a current portfolio snapshot is required",
            )
        if not self._is_non_negative_finite_decimal(estimated_transaction_cost):
            return self._reject(
                proposal,
                RiskReasonCode.INVALID_PORTFOLIO_STATE,
                "estimated transaction cost must be non-negative and finite",
            )
        if not self._is_finite_decimal(reserved_cash_delta):
            return self._reject(
                proposal,
                RiskReasonCode.INVALID_PORTFOLIO_STATE,
                "reserved cash delta must be finite",
            )
        if not self._is_non_negative_finite_decimal(reserved_buying_power):
            return self._reject(
                proposal,
                RiskReasonCode.INVALID_PORTFOLIO_STATE,
                "reserved buying power must be non-negative and finite",
            )

        actual_quantities = self._snapshot_quantities(snapshot)
        if actual_quantities is None:
            return self._reject(
                proposal,
                RiskReasonCode.INVALID_PORTFOLIO_STATE,
                "portfolio positions must have unique symbols",
            )
        quantities = dict(actual_quantities)
        for symbol, quantity in (reserved_quantities or {}).items():
            if not self._is_finite_decimal(quantity):
                return self._reject(
                    proposal,
                    RiskReasonCode.INVALID_PORTFOLIO_STATE,
                    f"reserved quantity for {symbol} must be finite",
                )
            quantities[symbol] = quantities.get(symbol, ZERO) + quantity

        reference_price = marks.get(proposal.symbol)
        if not self._is_positive_finite_decimal(reference_price):
            return self._reject(
                proposal,
                RiskReasonCode.INVALID_PORTFOLIO_STATE,
                f"a positive observed mark is required for {proposal.symbol}",
            )
        assert reference_price is not None
        if proposal.order_type is OrderType.LIMIT and proposal.side is OrderSide.BUY:
            assert proposal.limit_price is not None
            reference_price = max(reference_price, proposal.limit_price)

        with localcontext(RISK_CONTEXT):
            actual_exposures = self._calculate_exposures(actual_quantities, marks, proposal.symbol)
            if actual_exposures is None:
                return self._reject(
                    proposal,
                    RiskReasonCode.INVALID_PORTFOLIO_STATE,
                    "every non-flat position requires a positive observed mark",
                )
            _, _, actual_net_exposure = actual_exposures
            if (
                snapshot.market_value != actual_net_exposure
                or snapshot.equity != snapshot.cash + actual_net_exposure
            ):
                return self._reject(
                    proposal,
                    RiskReasonCode.INVALID_PORTFOLIO_STATE,
                    "portfolio snapshot is inconsistent with observed marks",
                )

        with localcontext(RISK_CONTEXT):
            current_quantity = quantities.get(proposal.symbol, ZERO)
            signed_quantity = (
                proposal.quantity if proposal.side is OrderSide.BUY else -proposal.quantity
            )
            projected_quantity = current_quantity + signed_quantity
            risk_reducing = self._is_genuinely_risk_reducing(current_quantity, projected_quantity)
            risk_increasing = not risk_reducing
            order_notional = proposal.quantity * reference_price

            projected_quantities = dict(quantities)
            projected_quantities[proposal.symbol] = projected_quantity
            exposures = self._calculate_exposures(projected_quantities, marks, proposal.symbol)
            if exposures is None:
                return self._reject(
                    proposal,
                    RiskReasonCode.INVALID_PORTFOLIO_STATE,
                    "every non-flat projected position requires a positive observed mark",
                    risk_increasing=risk_increasing,
                    reference_price=reference_price,
                    order_notional=order_notional,
                    projected_position_quantity=projected_quantity,
                    estimated_transaction_cost=estimated_transaction_cost,
                )
            symbol_exposure, gross_exposure, net_exposure = exposures
            effective_cash = snapshot.cash + reserved_cash_delta
            trade_cash_delta = (
                -order_notional if proposal.side is OrderSide.BUY else order_notional
            ) - estimated_transaction_cost
            projected_cash = effective_cash + trade_cash_delta
            projected_equity = projected_cash + net_exposure
            leverage = gross_exposure / snapshot.equity if snapshot.equity > ZERO else None

        diagnostics: _DecisionDiagnostics = {
            "risk_increasing": risk_increasing,
            "reference_price": reference_price,
            "order_notional": order_notional,
            "projected_position_quantity": projected_quantity,
            "projected_symbol_exposure": symbol_exposure,
            "projected_gross_exposure": gross_exposure,
            "projected_net_exposure": net_exposure,
            "projected_gross_leverage": leverage,
            "projected_cash": projected_cash,
            "estimated_transaction_cost": estimated_transaction_cost,
        }

        if (
            self._config.max_order_notional is not None
            and order_notional > self._config.max_order_notional
        ):
            return self._reject(
                proposal,
                RiskReasonCode.ORDER_NOTIONAL_LIMIT,
                "order notional exceeds configured limit",
                **diagnostics,
            )
        if (
            self._config.max_position_quantity is not None
            and abs(projected_quantity) > self._config.max_position_quantity
            and risk_increasing
        ):
            return self._reject(
                proposal,
                RiskReasonCode.POSITION_LIMIT,
                "projected absolute position exceeds configured limit",
                **diagnostics,
            )
        if (
            self._config.max_symbol_exposure is not None
            and symbol_exposure > self._config.max_symbol_exposure
            and risk_increasing
        ):
            return self._reject(
                proposal,
                RiskReasonCode.SYMBOL_EXPOSURE_LIMIT,
                "projected symbol exposure exceeds configured limit",
                **diagnostics,
            )
        if (
            self._config.max_gross_exposure is not None
            and gross_exposure > self._config.max_gross_exposure
            and risk_increasing
        ):
            return self._reject(
                proposal,
                RiskReasonCode.GROSS_EXPOSURE_LIMIT,
                "projected gross exposure exceeds configured limit",
                **diagnostics,
            )
        if (snapshot.equity <= ZERO or projected_equity <= ZERO) and risk_increasing:
            return self._reject(
                proposal,
                RiskReasonCode.INVALID_PORTFOLIO_STATE,
                "risk-increasing proposals require positive projected equity",
                **diagnostics,
            )
        if (
            self._config.max_leverage is not None
            and leverage is not None
            and leverage > self._config.max_leverage
            and risk_increasing
        ):
            return self._reject(
                proposal,
                RiskReasonCode.LEVERAGE_LIMIT,
                "projected gross leverage exceeds configured limit",
                **diagnostics,
            )
        required_buying_power = order_notional + estimated_transaction_cost
        available_buying_power = snapshot.cash - reserved_buying_power
        if (
            self._config.enforce_buying_power
            and proposal.side is OrderSide.BUY
            and required_buying_power > available_buying_power
            and risk_increasing
        ):
            return self._reject(
                proposal,
                RiskReasonCode.INSUFFICIENT_BUYING_POWER,
                "estimated purchase cost exceeds available cash",
                **diagnostics,
            )
        if (
            self._config.max_drawdown is not None
            and snapshot.drawdown < self._config.max_drawdown
            and risk_increasing
        ):
            return self._reject(
                proposal,
                RiskReasonCode.DRAWDOWN_LIMIT,
                "current drawdown breaches configured limit",
                **diagnostics,
            )

        return RiskDecision(
            proposal_id=proposal.proposal_id,
            approved=True,
            reason_code=RiskReasonCode.APPROVED,
            message="proposal approved",
            timestamp=proposal.signal_timestamp,
            **diagnostics,
        )

    @staticmethod
    def _snapshot_quantities(snapshot: PortfolioSnapshot) -> dict[str, Decimal] | None:
        quantities: dict[str, Decimal] = {}
        for position in snapshot.positions:
            if position.symbol in quantities:
                return None
            quantities[position.symbol] = position.quantity
        return quantities

    @classmethod
    def _calculate_exposures(
        cls,
        quantities: Mapping[str, Decimal],
        marks: Mapping[str, Decimal],
        target_symbol: str,
    ) -> tuple[Decimal, Decimal, Decimal] | None:
        gross = ZERO
        net = ZERO
        symbol_exposure = ZERO
        for symbol in sorted(quantities):
            quantity = quantities[symbol]
            if quantity == ZERO:
                continue
            mark = marks.get(symbol)
            if not cls._is_positive_finite_decimal(mark):
                return None
            assert mark is not None
            value = quantity * mark
            gross += abs(value)
            net += value
            if symbol == target_symbol:
                symbol_exposure = abs(value)
        return symbol_exposure, gross, net

    @staticmethod
    def _is_genuinely_risk_reducing(current_quantity: Decimal, projected_quantity: Decimal) -> bool:
        if current_quantity == ZERO or abs(projected_quantity) >= abs(current_quantity):
            return False
        return projected_quantity == ZERO or (projected_quantity > ZERO) == (
            current_quantity > ZERO
        )

    @staticmethod
    def _is_finite_decimal(value: object) -> bool:
        return isinstance(value, Decimal) and value.is_finite()

    @staticmethod
    def _is_positive_finite_decimal(value: object) -> bool:
        return isinstance(value, Decimal) and value.is_finite() and value > ZERO

    @staticmethod
    def _is_non_negative_finite_decimal(value: object) -> bool:
        return isinstance(value, Decimal) and value.is_finite() and value >= ZERO

    @staticmethod
    def _reject(
        proposal: OrderProposal,
        reason_code: RiskReasonCode,
        message: str,
        *,
        risk_increasing: bool = True,
        reference_price: Decimal | None = None,
        order_notional: Decimal | None = None,
        projected_position_quantity: Decimal | None = None,
        projected_symbol_exposure: Decimal | None = None,
        projected_gross_exposure: Decimal | None = None,
        projected_net_exposure: Decimal | None = None,
        projected_gross_leverage: Decimal | None = None,
        projected_cash: Decimal | None = None,
        estimated_transaction_cost: Decimal | None = None,
    ) -> RiskDecision:
        return RiskDecision(
            proposal_id=proposal.proposal_id,
            approved=False,
            reason_code=reason_code,
            message=message,
            timestamp=proposal.signal_timestamp,
            risk_increasing=risk_increasing,
            reference_price=reference_price,
            order_notional=order_notional,
            projected_position_quantity=projected_position_quantity,
            projected_symbol_exposure=projected_symbol_exposure,
            projected_gross_exposure=projected_gross_exposure,
            projected_net_exposure=projected_net_exposure,
            projected_gross_leverage=projected_gross_leverage,
            projected_cash=projected_cash,
            estimated_transaction_cost=estimated_transaction_cost,
        )
