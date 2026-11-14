from dataclasses import dataclass, field, asdict
from enum import StrEnum
from typing import Any
import math
import pandas as pd


class Market(StrEnum):
    A_SHARE = "A_SHARE"
    US_STOCK = "US_STOCK"
    ETF = "ETF"
    FUTURES = "FUTURES"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    COMMODITY = "COMMODITY"
    INDEX = "INDEX"


class Coverage(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class Instrument:
    symbol: str
    name: str
    market: str
    currency: str = "CNY"
    timezone: str = "Asia/Shanghai"
    provider_symbol: str = ""
    lot_size: float = 100
    tick_size: float = 0.01
    multiplier: float = 1
    margin_rate: float = 1
    shortable: bool = False
    settlement_days: int = 1
    group: str = "CN_EQUITY"
    sector: str = "UNKNOWN"
    sessions: tuple = (("09:30", "11:30"), ("13:00", "15:00"))
    continuous: bool = False
    expiry: str | None = None
    tradable: bool = True
    volume_unit: str = "provider_units"

    def __post_init__(self):
        Market(self.market)
        if not all(math.isfinite(v) and v > 0 for v in (self.lot_size,self.tick_size,self.multiplier,self.margin_rate)):
            raise ValueError("Instrument units must be positive")
        if self.margin_rate > 1 or self.settlement_days < 0:
            raise ValueError("Invalid margin/settlement")


@dataclass
class Dataset:
    bars: pd.DataFrame
    metadata: dict


@dataclass
class Signal:
    timestamp: pd.Timestamp
    symbol: str
    strategy: str
    direction: int
    entry: float
    stop: float
    target: float
    tp1: float | None = None
    partial_fraction: float = 0.5
    order_type: str = "MARKET"
    valid_bars: int = 1
    score: float = 0
    reasons: list[str] = field(default_factory=list)
    regime: str = "UNKNOWN"
    minimum_rr: float = 2

    def __post_init__(self):
        if not all(math.isfinite(v) and v > 0 for v in (self.entry,self.stop,self.target,self.minimum_rr)):
            raise ValueError("Signal price/RR values must be positive and finite")
        if self.direction not in (-1, 1) or self.order_type not in ("MARKET", "LIMIT"):
            raise ValueError("Invalid direction/order type")
        if self.valid_bars < 1 or not 0 <= self.partial_fraction < 1:
            raise ValueError("Invalid expiry/partial fraction")
        if self.direction * (self.entry - self.stop) <= 0 or self.direction * (self.target - self.entry) <= 0:
            raise ValueError("Stop/target on wrong side")
        if self.tp1 is not None and (not math.isfinite(self.tp1) or not 0 < self.direction*(self.tp1-self.entry) < self.direction*(self.target-self.entry)):
            raise ValueError("TP1 must lie between entry and final target")


@dataclass
class BacktestResult:
    metrics: dict
    equity_curve: pd.DataFrame
    trades: pd.DataFrame
    fills: pd.DataFrame
    risk_events: pd.DataFrame
    signals: pd.DataFrame
    config: dict

    def __getattr__(self, name: str) -> Any:
        if name in self.metrics:
            return self.metrics[name]
        raise AttributeError(name)


def as_record(value):
    return asdict(value)

