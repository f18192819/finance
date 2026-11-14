from dataclasses import asdict
import pandas as pd
import pytest
from quant_research.config import load_config
from quant_research.indicators import compute_features
from quant_research.strategies import make_strategy,STRATEGIES


@pytest.mark.parametrize("cut",[45,110,250,350])
def test_all_features_prefix_invariant(history,cut):
    p=load_config("strategies")["defaults"]
    full,pivots,zones=compute_features(history,p)
    prefix,pp,pz=compute_features(history.iloc[:cut].copy(),p)
    pd.testing.assert_frame_equal(full.iloc[:cut],prefix)
    if not pp.empty:
        pd.testing.assert_frame_equal(pivots.loc[pivots.confirmation_time<=history.timestamp.iloc[cut-1]].reset_index(drop=True),pp.reset_index(drop=True))
    if not pz.empty:
        columns=["kind","direction","low","high","created_at","confirmed_at"]
        pd.testing.assert_frame_equal(zones.loc[zones.confirmed_at<=history.timestamp.iloc[cut-1],columns].reset_index(drop=True),pz[columns].reset_index(drop=True))


@pytest.mark.parametrize("name",list(STRATEGIES))
def test_strategy_future_data_does_not_change_past_signals(history,name):
    p=dict(ema_fast=5,ema_slow=20,pivot_left=2,pivot_right=2,volume_multiplier=1,score_threshold=0)
    full=make_strategy(name,p).generate_signals(history)
    prefix=make_strategy(name,p).generate_signals(history.iloc[:300].copy())
    assert [asdict(s) for s in full if s.timestamp<=history.timestamp.iloc[299]]==[asdict(s) for s in prefix]


def test_strict_mtf_cannot_silently_fall_back(history):
    with pytest.raises(ValueError,match="actual 1H"):
        make_strategy("trend_following",{"mode":"multi_timeframe"}).generate_signals(history)


@pytest.mark.parametrize("name",list(STRATEGIES))
def test_parameters_independent_and_invalid_rejected(name):
    with pytest.raises(ValueError): make_strategy(name,{"pivot_right":0})
    a,b=make_strategy(name,{"target_r":4}),make_strategy(name)
    assert a.parameters["target_r"]!=b.parameters["target_r"]

