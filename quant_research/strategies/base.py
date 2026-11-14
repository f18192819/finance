from abc import ABC, abstractmethod
from copy import deepcopy
import numpy as np
import pandas as pd
from ..config import load_config
from ..decision import score_candidate
from ..indicators import compute_features
from ..models import Signal
from ..regime import add_regime
from ..data.resampler import align_confirmed


class BaseStrategy(ABC):
    name = "base"
    version = "1.0.0"

    def __init__(self, parameters=None):
        config = load_config("strategies")
        unknown = set(parameters or {}) - (set(config["defaults"]) | {"scoring_weights","volatility_lookback","ob_lookback"})
        if unknown:
            raise ValueError(f"Unknown strategy parameters: {sorted(unknown)}")
        self.parameters = deepcopy(dict(config["defaults"], **(parameters or {})))
        self.parameters.setdefault("scoring_weights",deepcopy(config["weights"]))
        self.validate_parameters()
        self.audit = []

    def get_parameters(self):
        return deepcopy(self.parameters)

    def validate_parameters(self):
        p = self.parameters
        if not 1 <= p["ema_fast"] < p["ema_slow"]:
            raise ValueError("EMA periods must satisfy 1 <= fast < slow")
        for k in ("atr_period", "pivot_left", "pivot_right", "internal_left", "internal_right", "range_lookback", "volume_period", "setup_expiry"):
            if not isinstance(p[k], int) or p[k] < 1:
                raise ValueError(f"{k} must be a positive integer")
        if p["target_r"] < p["minimum_rr"] or p["minimum_rr"] <= 0 or not 0 < p["tp1_r"] < p["target_r"]:
            raise ValueError("Invalid reward/risk targets")
        if not 0 <= p["partial_fraction"] < 1 or not 0 < p["max_stop_pct"] <= 1:
            raise ValueError("Invalid partial exit or stop percentage")
        if p["partial_fraction"]*p["tp1_r"]+(1-p["partial_fraction"])*p["target_r"] < p["minimum_rr"]:
            raise ValueError("Weighted partial-exit reward/risk below minimum_rr")
        if not 0 <= p["compression_quantile"] <= 1 or p["stop_atr_buffer"] < 0 or p["volume_multiplier"] <= 0:
            raise ValueError("Invalid threshold")
        if p["mode"] not in ("single_timeframe", "multi_timeframe"):
            raise ValueError("Unknown strategy mode")
        score_candidate({},weights=p["scoring_weights"],disabled=p["disabled_factors"])
        if not 0<=p["score_threshold"]<=100:
            raise ValueError("score_threshold must be between 0 and 100")

    def prepare(self, bars, context=None):
        d, self.pivots, self.zones = compute_features(bars, self.parameters)
        d = add_regime(d, self.parameters["adx_threshold"])
        if self.parameters["mode"] == "multi_timeframe":
            context = context or {}
            if not {"1D", "4H"}.issubset(context) or context.get("base_timeframe") != "1H":
                raise ValueError("Strict multi_timeframe mode requires actual 1H base plus closed 4H and 1D data")
            for frame,duration in ((bars,pd.Timedelta(hours=1)),(context["4H"],pd.Timedelta(hours=4))):
                if "open_time" not in frame or (frame.timestamp-frame.open_time).ne(duration).any():
                    raise ValueError("MTF input interval does not match actual 1H/4H duration")
            daily, _, _ = compute_features(context["1D"], self.parameters)
            h4, _, _ = compute_features(context["4H"], self.parameters)
            d = align_confirmed(d, daily, ["close", "ema_fast", "ema_slow"], "daily_")
            cols = ["structure_event", "event_direction", "structure_direction", "swing_low", "swing_high", "zone_bull", "zone_bear",
                    "ob_bull_low", "ob_bull_high", "ob_bear_low", "ob_bear_high", "fvg_bull_low", "fvg_bull_high", "fvg_bear_low", "fvg_bear_high"]
            d = align_confirmed(d, h4, cols, "h4_")
        self.audit = []
        self.features = d
        return d

    def trend(self, row, side):
        prefix = "daily_" if self.parameters["mode"] == "multi_timeframe" else ""
        close, fast, slow = [getattr(row, prefix + k) for k in ("close", "ema_fast", "ema_slow")]
        return side * (close - slow) > 0 and side * (fast - slow) > 0

    def candidate(self, row, side, stop, factors, reasons):
        p = self.parameters
        risk = side * (row.close - stop)
        rejection = []
        if not np.isfinite(risk) or risk <= 0:
            rejection.append("Invalid structure stop")
        elif risk / row.close > p["max_stop_pct"]:
            rejection.append("Stop distance exceeds max_stop_pct")
        if row.volume <= 0:
            rejection.append("No tradable volume")
        decision = score_candidate(factors, rejection, weights=p["scoring_weights"], disabled=p["disabled_factors"])
        self.audit.append(dict(timestamp=row.timestamp, strategy=self.name, direction=side, score=decision.score,
                               reasons=decision.reasons, rejected_conditions=decision.rejected_conditions))
        if rejection or decision.score < p["score_threshold"]:
            return None
        return Signal(row.timestamp, row.symbol, self.name, side, row.close, stop,
                      row.close + side * risk * p["target_r"], row.close + side * risk * p["tp1_r"],
                      p["partial_fraction"], score=decision.score, reasons=reasons + decision.reasons,
                      regime=row.regime, minimum_rr=p["minimum_rr"])

    @abstractmethod
    def generate_signals(self, data, context=None): ...
