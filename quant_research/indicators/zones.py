import numpy as np
import pandas as pd


def zone_features(bars, p):
    """Per-bar active-zone snapshots are causal; final ledger is for audit only."""
    zones, snapshots = [], []
    for i, bar in enumerate(bars.itertuples(index=False)):
        record = {f"{kind}_{side}_{edge}": np.nan for kind in ("ob", "fvg") for side in ("bull", "bear") for edge in ("low", "high")}
        record.update(zone_bull=False, zone_bear=False, ob_bull_touch=False, ob_bear_touch=False)
        for z in zones:
            if z["invalidated_at"] is not None:
                continue
            overlap = bar.low <= z["high"] and bar.high >= z["low"]
            if overlap and z["first_retest_at"] is None:
                z["first_retest_at"] = bar.timestamp
            if z["kind"] == "fvg":
                fill = (z["high"] - bar.low) / (z["high"] - z["low"]) if z["direction"] == 1 else (bar.high-z["low"])/(z["high"]-z["low"])
                z["fill_ratio"] = max(z["fill_ratio"], min(1., max(0., fill)))
                if z["fill_ratio"] >= 1:
                    z["fully_filled_at"] = bar.timestamp
            invalid = bar.close < z["low"] if z["direction"] == 1 else bar.close > z["high"]
            invalid |= z["kind"] == "fvg" and z["fill_ratio"] >= 1
            if invalid:
                z["invalidated_at"] = bar.timestamp
                continue
            side = "bull" if z["direction"] == 1 else "bear"
            record[f'{z["kind"]}_{side}_low'] = z["low"]
            record[f'{z["kind"]}_{side}_high'] = z["high"]
            if overlap:
                record[f"zone_{side}"] = True
                if z["kind"] == "ob":
                    record[f"ob_{side}_touch"] = True
        # New zones cannot be counted as retests on the candle creating them.
        new = []
        if bar.structure_event:
            side = bar.event_direction
            for j in range(i-1, max(-1, i-p.get("ob_lookback", 20)-1), -1):
                prev = bars.iloc[j]
                if side * (prev.close - prev.open) < 0:
                    new.append(("ob", side, prev.low, prev.high, prev.timestamp))
                    break
        if i >= 2:
            prev = bars.iloc[i-2]
            if bar.low > prev.high:
                new.append(("fvg", 1, prev.high, bar.low, bar.timestamp))
            if bar.high < prev.low:
                new.append(("fvg", -1, bar.high, prev.low, bar.timestamp))
        for kind, side, low, high, created in new:
            if high > low:
                zones.append(dict(id=len(zones), kind=kind, direction=side, low=float(low), high=float(high),
                                  created_at=created, confirmed_at=bar.timestamp, first_retest_at=None,
                                  invalidated_at=None, fully_filled_at=None, fill_ratio=0.))
        snapshots.append(record)
    return bars.join(pd.DataFrame(snapshots, index=bars.index)), pd.DataFrame(zones)

