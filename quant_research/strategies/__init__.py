from .trend_following import TrendFollowing
from .breakout import Breakout
from .liquidity_reversal import LiquidityReversal

STRATEGIES = {s.name: s for s in (TrendFollowing, Breakout, LiquidityReversal)}


def make_strategy(name, parameters=None):
    return STRATEGIES[name](parameters)

