"""Artificial deterministic fixtures only. Never published as historical market data."""
import numpy as np
import pandas as pd
import pytest
from quant_research.models import Instrument,Dataset


@pytest.fixture
def instrument():
    return Instrument("TEST","SYNTHETIC TEST ONLY","US_STOCK",currency="USD",timezone="UTC",lot_size=1,
                      settlement_days=0,group="TEST",sessions=(("09:00","16:00"),))


def make_bars(ohlc,symbol="TEST",start="2024-01-01",freq="D"):
    dates = pd.date_range(start,periods=len(ohlc),freq=freq,tz="UTC")
    d = pd.DataFrame(ohlc,columns=["open","high","low","close"],dtype=float)
    d["timestamp"] = dates + pd.Timedelta(hours=16)
    d["open_time"] = dates + pd.Timedelta(hours=9)
    d["volume"],d["amount"],d["symbol"] = 1000.,100000.,symbol
    return d


@pytest.fixture
def history():
    rng = np.random.default_rng(2026)
    close = 100*np.exp(np.cumsum(rng.normal(.0002,.018,420)))
    opening = np.r_[close[0],close[:-1]]
    high = np.maximum(close,opening)*(1+rng.uniform(.001,.02,len(close)))
    low = np.minimum(close,opening)*(1-rng.uniform(.001,.02,len(close)))
    d = make_bars(np.column_stack([opening,high,low,close]))
    d["volume"] = rng.uniform(100,10000,len(d))
    return d


@pytest.fixture
def dataset(history):
    return Dataset(history,{"source":"SYNTHETIC_UNIT_TEST_ONLY","timeframe":"1D","adjustment":"none","universe_basis":"synthetic_test_fixture"})

