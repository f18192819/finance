import numpy as np
import pandas as pd


def structure_features(bars, p):
    left, right = p.get("pivot_left", 3), p.get("pivot_right", 3)
    if min(left, right) < 1:
        raise ValueError("Pivot confirmation windows must be >= 1")
    records, pivots = [], []
    high_pivot = low_pivot = None
    prior_high = prior_low = None
    high_class = low_class = ""
    direction = 0
    broken = set()
    for i, bar in enumerate(bars.itertuples(index=False)):
        # Features refer only to pivots confirmed BEFORE this candle began.
        hi = high_pivot[1] if high_pivot else np.nan
        lo = low_pivot[1] if low_pivot else np.nan
        scale = getattr(bar, "atr", np.nan)
        buffer = p.get("sweep_atr", .1) * scale
        sweep_up = bool(np.isfinite(hi) and bar.high > hi + buffer and bar.close < hi)
        sweep_down = bool(np.isfinite(lo) and bar.low < lo - buffer and bar.close > lo)
        event, event_side = "", 0
        for side, pivot, condition in [(1, high_pivot, bar.close > hi), (-1, low_pivot, bar.close < lo)]:
            key = (side, pivot[0]) if pivot else None
            if pivot and condition and key not in broken:
                if direction == side:
                    event = "BOS"
                else:
                    supported = (side == 1 and low_class == "HL") or (side == -1 and high_class == "LH")
                    event = "CHoCH+" if supported else "CHoCH"
                direction, event_side = side, side
                broken.add(key)
        record = dict(swing_high=hi, swing_low=lo, high_class=high_class, low_class=low_class,
                      structure_event=event, event_direction=event_side, structure_direction=direction,
                      sweep_high=sweep_up, sweep_low=sweep_down,
                      equal_high=bool(prior_high is not None and np.isfinite(scale) and abs(hi-prior_high) <= p.get("equal_tolerance_atr", .15)*scale),
                      equal_low=bool(prior_low is not None and np.isfinite(scale) and abs(lo-prior_low) <= p.get("equal_tolerance_atr", .15)*scale))
        j = i - right
        if j >= left:
            window = bars.iloc[j-left:i+1]
            candidate = bars.iloc[j]
            for kind, value, extreme in [("high", candidate.high, window.high.max()), ("low", candidate.low, window.low.min())]:
                # Strict extremum avoids duplicate pivots on plateaus.
                if value != extreme or (window[kind] == value).sum() != 1:
                    continue
                if kind == "high":
                    prior_high = high_pivot[1] if high_pivot else None
                    high_class = "HH" if prior_high is not None and value > prior_high else "LH" if prior_high is not None else "H"
                    high_pivot = (j, value)
                else:
                    prior_low = low_pivot[1] if low_pivot else None
                    low_class = "HL" if prior_low is not None and value > prior_low else "LL" if prior_low is not None else "L"
                    low_pivot = (j, value)
                pivots.append(dict(pivot_time=candidate.timestamp, confirmation_time=bar.timestamp, pivot_price=value, pivot_type=kind,
                                   label=high_class if kind == "high" else low_class))
        records.append(record)
    features = pd.DataFrame(records, index=bars.index)
    # Overwrite when calculating a second (internal) scale.
    result = bars.drop(columns=list(set(bars.columns) & set(features.columns))).join(features)
    return result, pd.DataFrame(pivots)

