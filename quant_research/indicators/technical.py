import numpy as np
import pandas as pd


def ema(values, period):
    if period < 1:
        raise ValueError("EMA period must be positive")
    return values.ewm(span=period, adjust=False, min_periods=period).mean()


def wilder(values, period):
    """Arithmetic seed of n valid observations, then (previous*(n-1)+current)/n."""
    if period < 1:
        raise ValueError("Wilder period must be positive")
    out = pd.Series(np.nan, index=values.index, dtype=float)
    seed, previous = [], np.nan
    for i, value in enumerate(values):
        if pd.isna(value):
            seed, previous = [], np.nan
            continue
        if np.isnan(previous):
            seed.append(value)
            if len(seed) == period:
                previous = float(np.mean(seed))
                out.iloc[i] = previous
        else:
            previous = (previous * (period - 1) + value) / period
            out.iloc[i] = previous
    return out


def atr(bars, period=14):
    prev = bars.close.shift(1)
    tr = pd.concat([bars.high - bars.low, (bars.high - prev).abs(), (bars.low - prev).abs()], axis=1).max(axis=1)
    return wilder(tr, period)


def rsi(close, period=14):
    delta = close.diff()
    gain = wilder(delta.clip(lower=0), period)
    loss = wilder(-delta.clip(upper=0), period)
    result = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
    result = result.mask((loss == 0) & (gain > 0), 100)
    return result.mask((loss == 0) & (gain == 0), 50)


def adx(bars, period=14):
    up, down = bars.high.diff(), -bars.low.diff()
    plus = up.where((up > down) & (up > 0), 0.)
    minus = down.where((down > up) & (down > 0), 0.)
    tr = atr(bars, period).replace(0, np.nan)
    p, m = 100 * wilder(plus, period) / tr, 100 * wilder(minus, period) / tr
    dx = (100 * (p - m).abs() / (p + m).replace(0, np.nan)).mask((p + m) == 0, 0)
    return pd.DataFrame({"di_plus": p, "di_minus": m, "adx": wilder(dx, period)})


def technical_features(bars, p):
    d = bars.copy()
    for n in (20, 50, 200):
        d[f"ema{n}"] = ema(d.close, n)
    for n in (50, 200):
        d[f"sma{n}"] = d.close.rolling(n).mean()
    d["ema_fast"] = ema(d.close, p.get("ema_fast", 50))
    d["ema_slow"] = ema(d.close, p.get("ema_slow", 200))
    period = p.get("atr_period", 14)
    d["atr"] = atr(d, period)
    d["atr_pct"] = d.atr / d.close
    d["historical_volatility"] = np.log(d.close).diff().rolling(20).std()  # per-bar, no invented annualization
    mean, std = d.close.rolling(20).mean(), d.close.rolling(20).std(ddof=0)
    d["bb_width"] = 4 * std / mean
    d["rsi"] = rsi(d.close, period)
    d["macd"] = ema(d.close, 12) - ema(d.close, 26)
    d["macd_signal"] = ema(d.macd, 9)
    d["roc"] = d.close.pct_change(10, fill_method=None)
    d["volume_sma"] = d.volume.rolling(p.get("volume_period", 20)).mean().shift(1)
    d["relative_volume"] = d.volume / d.volume_sma.replace(0, np.nan)
    d["volume_breakout"] = d.relative_volume >= p.get("volume_multiplier", 1.5)
    d["obv"] = (np.sign(d.close.diff()).fillna(0) * d.volume).cumsum()
    # Group by explicit trading session when supplied; otherwise VWAP remains unavailable.
    if "session_id" in d:
        typical = (d.high + d.low + d.close) / 3
        d["vwap"] = (typical * d.volume).groupby(d.session_id).cumsum() / d.volume.groupby(d.session_id).cumsum().replace(0, np.nan)
    else:
        d["vwap"] = np.nan
    d = pd.concat([d, adx(d, period)], axis=1)
    history = p.get("volatility_lookback", 100)
    d["atr_low"] = d.atr_pct.rolling(history, min_periods=20).quantile(.2).shift(1)
    d["atr_high"] = d.atr_pct.rolling(history, min_periods=20).quantile(.8).shift(1)
    d["compression"] = d.bb_width <= d.bb_width.rolling(history, min_periods=20).quantile(p.get("compression_quantile", .3)).shift(1)
    return d

