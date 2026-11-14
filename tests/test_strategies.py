import pandas as pd
import numpy as np
from quant_research.strategies import make_strategy
from conftest import make_bars


def prepared(ohlc):
    d=make_bars(ohlc)
    defaults=dict(ema_fast=90,ema_slow=80,atr=2,regime="TREND_BULL",structure_event="",event_direction=0,
                  swing_high=110,swing_low=80,relative_volume=2,ob_bull_low=np.nan,ob_bull_high=np.nan,
                  ob_bear_low=np.nan,ob_bear_high=np.nan,fvg_bull_low=np.nan,fvg_bull_high=np.nan,
                  fvg_bear_low=np.nan,fvg_bear_high=np.nan,compression=False,volume_breakout=True,
                  sweep_low=False,sweep_high=False,ob_bull_touch=False,ob_bear_touch=False)
    for k,v in defaults.items(): d[k]=v
    return d


def test_trend_needs_prior_bos_retest_and_later_close():
    d=prepared([[100,103,99,102],[102,112,101,111],[105,114,100,113],[113,115,110,114]])
    d.loc[1,["structure_event","event_direction"]]=["BOS",1]
    d.loc[2,["ob_bull_low","ob_bull_high"]]=[100,105]
    strategy=make_strategy("trend_following")
    strategy.prepare=lambda data,context:data
    signals=strategy.generate_signals(d)
    assert len(signals)==1 and signals[0].timestamp==d.timestamp.iloc[2]
    d.loc[1,"structure_event"]=""
    assert strategy.generate_signals(d)==[]


def test_breakout_waits_for_retest():
    d=prepared([[99,101,98,100],[100,102,99,101],[101,108,100,107],[102,108,101,106]])
    d.loc[1,"compression"]=True
    strategy=make_strategy("breakout",dict(range_lookback=2))
    strategy.prepare=lambda data,context:data
    signals=strategy.generate_signals(d)
    assert len(signals)==1 and signals[0].timestamp==d.timestamp.iloc[3]
    assert strategy.generate_signals(d.iloc[:3])==[]


def test_reversal_needs_choch_after_sweep_and_subsequent_ob_retest():
    d=prepared([[100,102,98,100],[99,101,95,100],[100,104,99,103],[102,107,100,106]])
    d.loc[1,"sweep_low"]=True
    d.loc[2,["structure_event","event_direction"]]=["CHoCH",1]
    d.loc[3,"ob_bull_touch"]=True
    strategy=make_strategy("liquidity_reversal")
    strategy.prepare=lambda data,context:data
    signals=strategy.generate_signals(d)
    assert len(signals)==1 and signals[0].timestamp==d.timestamp.iloc[3]
    d.loc[2,"structure_event"]=""
    assert strategy.generate_signals(d)==[]

