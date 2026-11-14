from dataclasses import dataclass
import pandas as pd


@dataclass
class MarketState:
    state: str
    confidence: float
    timestamp: object
    reasons: list


def classify(row, adx_threshold=20):
    if pd.isna(row.ema_slow) or pd.isna(row.adx) or pd.isna(row.atr_low):
        return MarketState("UNKNOWN", 0, row.timestamp, ["Indicator warm-up incomplete"])
    bull = row.close > row.ema_slow and row.ema_fast > row.ema_slow
    bear = row.close < row.ema_slow and row.ema_fast < row.ema_slow
    strong = row.adx >= adx_threshold
    structure = row.structure_direction
    if row.atr_pct > row.atr_high and not strong:
        return MarketState("HIGH_VOLATILITY", .7, row.timestamp, ["ATR above prior 80th percentile", "ADX weak"])
    if row.atr_pct < row.atr_low and not strong:
        return MarketState("LOW_VOLATILITY", .7, row.timestamp, ["ATR below prior 20th percentile", "ADX weak"])
    if bull and strong and structure == 1:
        return MarketState("TREND_BULL", .9 if row.low_class == "HL" else .8, row.timestamp, ["Bullish EMA alignment", "ADX strong", "Bullish confirmed structure"])
    if bear and strong and structure == -1:
        return MarketState("TREND_BEAR", .9 if row.high_class == "LH" else .8, row.timestamp, ["Bearish EMA alignment", "ADX strong", "Bearish confirmed structure"])
    if not strong and not (bull or bear):
        return MarketState("RANGE", .7, row.timestamp, ["No EMA trend alignment", "ADX weak"])
    return MarketState("TRANSITION", .5, row.timestamp, ["Mixed trend/volatility/structure conditions"])


def add_regime(frame, threshold=20):
    d = frame.copy()
    states = [classify(r, threshold) for r in d.itertuples(index=False)]
    d["regime"] = [s.state for s in states]
    d["regime_confidence"] = [s.confidence for s in states]
    d["regime_reasons"] = ["; ".join(s.reasons) for s in states]
    return d

