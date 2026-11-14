from dataclasses import dataclass
import math
from .config import load_config


@dataclass
class RiskConfig:
    initial_equity: float = 1_000_000
    risk_per_trade: float = .01
    max_single_trade_risk: float = .01
    max_correlated_group_risk: float = .02
    max_total_open_risk: float = .04
    weekly_loss_limit: float = .04
    consecutive_loss_review_threshold: int = 4
    max_gross_exposure: float = 1
    max_positions: int = 8
    correlation_threshold: float = .8
    correlation_window: int = 60
    trailing_atr: float = 0
    max_holding_bars: int = 60

    def __post_init__(self):
        for k in ("risk_per_trade", "max_single_trade_risk", "max_correlated_group_risk", "max_total_open_risk", "weekly_loss_limit"):
            if not 0 < getattr(self, k) <= 1:
                raise ValueError(f"Invalid {k}")
        if self.initial_equity <= 0 or self.max_positions < 1 or self.max_gross_exposure <= 0 or self.max_holding_bars < 1:
            raise ValueError("Invalid capital/position limits")

    @classmethod
    def defaults(cls, **overrides):
        return cls(**dict(load_config("risk"), **overrides))


def size_position(equity, available_margin, entry, stop, direction, instrument, costs, risk_config):
    if equity <= 0 or direction * (entry-stop) <= 0:
        return 0., 0.
    stop_fill = costs.fill(stop, -direction, instrument.tick_size)
    loss_per_unit = max(0, direction * (entry-stop_fill)) * instrument.multiplier
    rate_fee = entry * instrument.multiplier * (2 * (costs.commission_bps + costs.exchange_bps) + costs.sell_tax_bps) / 10000
    budget = equity * min(risk_config.risk_per_trade, risk_config.max_single_trade_risk)
    quantity = max(0, (budget - 2*costs.minimum_commission) / (loss_per_unit + rate_fee)) if loss_per_unit+rate_fee else 0
    margin_per_unit = entry * instrument.multiplier * instrument.margin_rate
    quantity = min(quantity, max(0, available_margin-costs.minimum_commission) / (margin_per_unit + rate_fee))
    quantity = math.floor(quantity / instrument.lot_size) * instrument.lot_size
    # Actual minimum fees + price rounding must remain inside budget.
    while quantity > 0:
        risk = loss_per_unit * quantity + costs.fee(entry, quantity, instrument.multiplier, direction) + costs.fee(stop_fill, quantity, instrument.multiplier, -direction)
        margin = margin_per_unit * quantity + costs.fee(entry, quantity, instrument.multiplier, direction)
        if risk <= budget + 1e-7 and margin <= available_margin + 1e-7:
            return float(quantity), float(risk)
        quantity -= instrument.lot_size
    return 0., 0.


def portfolio_rejection(equity, new_risk, open_risk, correlated_risk, weekly_start_equity, consecutive_losses, positions, gross, risk):
    if equity <= 0:
        return "Account equity non-positive"
    if positions >= risk.max_positions:
        return "Maximum position count reached"
    if weekly_start_equity > 0 and equity / weekly_start_equity - 1 <= -risk.weekly_loss_limit:
        return "Weekly mark-to-market loss limit reached"
    if consecutive_losses >= risk.consecutive_loss_review_threshold:
        return "Consecutive losses require manual review (new entries locked for this run)"
    if open_risk + new_risk > equity * risk.max_total_open_risk + 1e-7:
        return "Total open risk exceeded"
    if correlated_risk + new_risk > equity * risk.max_correlated_group_risk + 1e-7:
        return "Correlated group risk exceeded"
    if gross > risk.max_gross_exposure + 1e-9:
        return "Gross exposure exceeded"
    return None

