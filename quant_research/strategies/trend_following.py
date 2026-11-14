import numpy as np
from .base import BaseStrategy


class TrendFollowing(BaseStrategy):
    name = "trend_following"

    def generate_signals(self, data, context=None):
        d = self.prepare(data, context)
        p, signals, setup = self.parameters, [], None
        prefix = "h4_" if p["mode"] == "multi_timeframe" else ""
        last_event = None
        for i, row in enumerate(d.itertuples(index=False)):
            event, side = getattr(row, prefix + "structure_event"), getattr(row, prefix + "event_direction")
            marker = (event, side, getattr(row, prefix + "swing_high"), getattr(row, prefix + "swing_low"))
            if event == "BOS" and side in (-1, 1) and marker != last_event:
                setup = (i, int(side))
                last_event = marker
            if setup is None:
                continue
            born, side = setup
            if i - born > p["setup_expiry"]:
                setup = None
                continue
            if i <= born or not self.trend(row, side) or row.regime not in ("TREND_BULL", "TREND_BEAR", "TRANSITION"):
                continue
            suffix = "bull" if side == 1 else "bear"
            bounds = []
            for kind in ("ob", "fvg"):
                lo, hi = getattr(row, f"{prefix}{kind}_{suffix}_low"), getattr(row, f"{prefix}{kind}_{suffix}_high")
                if np.isfinite(lo) and row.low <= hi and row.high >= lo and (row.close >= lo if side == 1 else row.close <= hi):
                    bounds.append(lo if side == 1 else hi)
            # Explicit alternative to CHoCH: directional candle closing beyond previous candle's extreme.
            previous = d.iloc[i-1]
            confirm = row.close > previous.high if side == 1 else row.close < previous.low
            if not bounds or not confirm:
                continue
            edge = min(bounds) if side == 1 else max(bounds)
            stop = edge - side * p["stop_atr_buffer"] * row.atr
            factors = dict(trend=True, structure=True, zone=True, volume=row.relative_volume >= 1, momentum=confirm)
            signal = self.candidate(row, side, stop, factors, ["Trend aligned", "Confirmed BOS followed by OB/FVG retest", "Close beyond previous candle extreme", f"mode={p['mode']}"])
            if signal:
                signals.append(signal)
                setup = None
        return signals
