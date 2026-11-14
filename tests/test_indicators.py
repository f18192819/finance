import numpy as np
import pandas as pd
from quant_research.indicators.technical import wilder,atr,ema,rsi
from quant_research.indicators.structure import structure_features
from quant_research.indicators.zones import zone_features
from conftest import make_bars


def test_wilder_arithmetic_seed():
    result=wilder(pd.Series([1.,2.,3.,6.,9.]),3)
    np.testing.assert_allclose(result.iloc[2:],[2.,10/3,47/9])
    assert result.iloc[:2].isna().all()


def test_atr_gap_true_range():
    d=make_bars([[10,11,9,10],[14,15,13,14],[14,16,12,15]])
    np.testing.assert_allclose(atr(d,2).iloc[1:],[3.5,3.75])


def test_ema_recursive_and_rsi_edges():
    s=pd.Series([1.,2.,3.,4.,5.])
    assert ema(s,3).iloc[2]==2.25
    assert rsi(s,2).iloc[-1]==100
    assert rsi(-s,2).iloc[-1]==0
    assert rsi(pd.Series([1.]*10),2).iloc[-1]==50


def test_pivot_confirmation_not_backdated():
    d=make_bars([[10,11,9,10],[12,13,11,12],[15,16,14,15],[12,13,11,12],[10,11,9,10],[17,18,16,17]])
    f,p=structure_features(d,dict(pivot_left=2,pivot_right=2))
    high=p.loc[p.pivot_type=="high"].iloc[0]
    assert high.pivot_time==d.timestamp.iloc[2]
    assert high.confirmation_time==d.timestamp.iloc[4]
    assert f.swing_high.iloc[:5].isna().all()
    assert f.structure_event.iloc[5]=="CHoCH"


def test_fvg_created_after_third_close():
    d=make_bars([[10,11,9,10],[12,13,11,12],[15,16,14,15],[15,16,13,15],[12,13,10,12]])
    d["structure_event"]=""
    d["event_direction"]=0
    f,z=zone_features(d,{})
    assert not f.zone_bull.iloc[2]
    assert z.iloc[0].confirmed_at==d.timestamp.iloc[2]
    assert f.zone_bull.iloc[3]
    assert z.iloc[0].fully_filled_at==d.timestamp.iloc[4]


def test_order_block_requires_structure_break():
    d=make_bars([[12,13,10,11],[11,14,10,13],[13,16,12,15]])
    d["structure_event"]=""
    d["event_direction"]=0
    _,zones=zone_features(d,{})
    assert zones.empty or "ob" not in zones.kind.tolist()
    d.loc[2,"structure_event"]="BOS"
    d.loc[2,"event_direction"]=1
    _,zones=zone_features(d,{})
    ob=zones.loc[zones.kind=="ob"].iloc[0]
    assert ob.created_at==d.timestamp.iloc[0] and ob.confirmed_at==d.timestamp.iloc[2]

