from dataclasses import dataclass, field
import math
from ..config import load_config


@dataclass
class Costs:
    commission_bps: float = 3
    minimum_commission: float = 0
    slippage_bps: float = 5
    spread_bps: float = 2
    exchange_bps: float = 0
    sell_tax_bps: float = 0
    annual_borrow_bps: float | None = None
    annual_financing_bps: float | None = None
    funding_bps_daily: float | None = None
    unmodeled: list = field(default_factory=list)

    def __post_init__(self):
        for name in ("commission_bps", "minimum_commission", "slippage_bps", "spread_bps", "exchange_bps", "sell_tax_bps"):
            if getattr(self, name) < 0:
                raise ValueError("Negative trading cost")

    @classmethod
    def for_market(cls, market, overrides=None):
        c = load_config("markets")
        return cls(**dict(c["DEFAULT"], **c.get(market, {}), **(overrides or {})))

    def fee(self, price, quantity, multiplier, side):
        value = abs(price * quantity * multiplier)
        return max(self.minimum_commission, value * self.commission_bps / 10000) + value * (self.exchange_bps + (self.sell_tax_bps if side < 0 else 0)) / 10000

    def fill(self, price, side, tick, limit=None):
        adjusted = price * (1 + side * (self.slippage_bps + self.spread_bps / 2) / 10000)
        adjusted = tick_round(adjusted, tick, side)
        if limit is not None:
            adjusted = min(adjusted, limit) if side == 1 else max(adjusted, limit)
        return adjusted


def tick_round(price, tick, side):
    value = price / tick
    return round((math.ceil(value - 1e-10) if side > 0 else math.floor(value + 1e-10)) * tick, 10)

