from dataclasses import replace
import pytest
from quant_research.data.prices import infer_price_map,map_signal_to_execution
from quant_research.models import Signal
from conftest import make_bars


def test_affine_price_map_includes_dividend_offset():
    adjusted=make_bars([[10,12,9,11]]).iloc[0]
    raw=make_bars([[21,25,19,23]]).iloc[0]
    scale,offset=infer_price_map(adjusted,raw)
    assert scale==pytest.approx(2) and offset==pytest.approx(1)
    s=Signal(adjusted.timestamp,"TEST","test",1,11,9,17)
    with pytest.raises(ValueError,match="point-in-time"): map_signal_to_execution(s,adjusted,raw)
    translated=map_signal_to_execution(s,adjusted,raw,point_in_time_verified=True)
    assert translated.entry==pytest.approx(23) and translated.stop==pytest.approx(19)


def test_non_affine_price_map_rejected():
    a=make_bars([[10,12,9,11]]).iloc[0]
    b=make_bars([[21,50,19,23]]).iloc[0]
    with pytest.raises(ValueError): infer_price_map(a,b)
