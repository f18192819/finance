from .base import BaseStrategy


class Breakout(BaseStrategy):
    name = "breakout"

    def generate_signals(self, data, context=None):
        d = self.prepare(data, context)
        p, signals, setup = self.parameters, [], None
        # In strict MTF mode setups must be constructed on actual 4H bars, with 1H execution confirmation.
        if p["mode"] == "multi_timeframe":
            higher = Breakout(dict(p, mode="single_timeframe"))
            hsignals = higher.generate_signals(context["4H"])
            by_time = {s.timestamp: s for s in hsignals}
            eligible = None
            for row in d.itertuples(index=False):
                for timestamp in list(by_time):
                    if timestamp <= row.timestamp:
                        eligible = by_time.pop(timestamp)
                if eligible and (row.timestamp - eligible.timestamp).total_seconds() > 4 * 3600:
                    eligible = None
                if eligible and row.timestamp > eligible.timestamp and eligible.direction * (row.close-row.open) > 0:
                    s = self.candidate(row, eligible.direction, eligible.stop,
                        dict(trend=self.trend(row, eligible.direction), structure=True, zone=True, volume=row.relative_volume>=1, momentum=True),
                        ["Closed 4H compression breakout and later retest", "Subsequent 1H directional close"])
                    if s:
                        signals.append(s)
                    eligible = None
            return signals
        high = d.high.rolling(p["range_lookback"]).max().shift(1)
        low = d.low.rolling(p["range_lookback"]).min().shift(1)
        for i, row in enumerate(d.itertuples(index=False)):
            if i < 1:
                continue
            if setup:
                born, side, level, other = setup
                if i - born > p["setup_expiry"] or (side == 1 and row.close < other) or (side == -1 and row.close > other):
                    setup = None
                elif i > born:
                    touch = row.low <= level and row.close > level if side == 1 else row.high >= level and row.close < level
                    if touch and side * (row.close-row.open) > 0:
                        stop = (min(row.low, level) if side == 1 else max(row.high, level)) - side * row.atr * p["stop_atr_buffer"]
                        s = self.candidate(row, side, stop,
                            dict(trend=self.trend(row, side), structure=True, zone=True, volume=row.relative_volume>=1, momentum=True),
                            ["Prior volatility compression", "Close breakout with above-average volume", "Later range-edge retest and directional close"])
                        if s:
                            signals.append(s)
                        setup = None
            if setup is None and bool(d.compression.iloc[i-1]) and row.volume_breakout and row.regime not in ("UNKNOWN", "HIGH_VOLATILITY"):
                if row.close > high.iloc[i]:
                    setup = (i, 1, high.iloc[i], low.iloc[i])
                elif row.close < low.iloc[i]:
                    setup = (i, -1, low.iloc[i], high.iloc[i])
        return signals

