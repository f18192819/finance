from .base import BaseStrategy


class LiquidityReversal(BaseStrategy):
    name = "liquidity_reversal"

    def generate_signals(self, data, context=None):
        d = self.prepare(data, context)
        p, signals, setup = self.parameters, [], None
        for i, row in enumerate(d.itertuples(index=False)):
            if setup:
                born, side, extreme, changed = setup
                if i-born > p["setup_expiry"] or (side==1 and row.close<extreme) or (side==-1 and row.close>extreme):
                    setup = None
                elif i > born:
                    if changed is None and row.structure_event in ("CHoCH", "CHoCH+") and row.event_direction == side:
                        setup = (born, side, extreme, i)
                    elif changed is not None and i > changed:
                        touch = row.ob_bull_touch if side == 1 else row.ob_bear_touch
                        confirm = row.close > d.high.iloc[i-1] if side == 1 else row.close < d.low.iloc[i-1]
                        if touch and confirm:
                            stop = extreme - side * row.atr * p["stop_atr_buffer"]
                            factors = dict(trend=self.trend(row, side), structure=True, zone=True, volume=row.relative_volume>=1, momentum=True)
                            if p["mode"] == "multi_timeframe" and getattr(row, "h4_structure_direction") != side:
                                continue
                            s = self.candidate(row, side, stop, factors,
                                ["Sweep of previously confirmed pivot; close reclaimed level", "Subsequent CHoCH", "Later valid order block retest and close confirmation"])
                            if s:
                                signals.append(s)
                            setup = None
            if setup is None and row.regime not in ("UNKNOWN", "HIGH_VOLATILITY"):
                if row.sweep_low and not row.sweep_high:
                    setup = (i, 1, row.low, None)
                elif row.sweep_high and not row.sweep_low:
                    setup = (i, -1, row.high, None)
        return signals
