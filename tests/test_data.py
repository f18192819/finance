from dataclasses import replace
import pandas as pd
import pytest
from quant_research.data.validation import validate_bars,normalize,import_csv,DataValidationError
from quant_research.data.resampler import resample,align_confirmed
from quant_research.data.storage import ParquetStore,data_hash
from quant_research.models import Dataset
from conftest import make_bars


@pytest.mark.parametrize("column,value",[("high",1),("low",10000),("volume",-1),("close",float("nan")),("amount",float("inf"))])
def test_invalid_ohlcv_rejected(history,column,value):
    history.loc[0,column]=value
    with pytest.raises(DataValidationError): validate_bars(history)


def test_duplicate_unsorted_rejected(history):
    with pytest.raises(DataValidationError): validate_bars(pd.concat([history,history.iloc[:1]]))
    with pytest.raises(DataValidationError): validate_bars(history.iloc[::-1])


def test_warnings_do_not_delete(history):
    history.loc[5,"volume"]=0
    issues=validate_bars(history)
    assert any(i["type"]=="zero_volume_suspension_candidate" for i in issues)
    assert len(history)==420


def test_unclosed_daily_excluded(instrument):
    raw=pd.DataFrame(dict(timestamp=["2024-01-01","2024-01-02"],open=[100,101],high=[102,103],low=[99,100],close=[101,102],volume=[1,2],amount=[100,200]))
    bars,issues=normalize(raw,instrument,"1D",pd.Timestamp("2024-01-02 15:00",tz="UTC"))
    assert len(bars)==1
    assert any(i["type"]=="unfinished_bar" for i in issues)


def hourly(instrument,periods=8):
    d=make_bars([[100,102,98,101]]*periods)
    d["timestamp"]=pd.date_range("2024-01-01 10:00",periods=periods,freq="h",tz="UTC")
    d["open_time"]=d.timestamp-pd.Timedelta(hours=1)
    return d


def test_four_hour_complete_only(instrument):
    d=hourly(instrument,6)
    result,issues=resample(d,"4H",instrument)
    assert len(result)==1
    assert result.timestamp.iloc[0]==d.timestamp.iloc[3]
    assert result.volume.iloc[0]==4000
    assert issues[0]["count"]==2


def test_no_aggregation_across_lunch(instrument):
    ins=replace(instrument,sessions=(("09:00","11:00"),("13:00","15:00")))
    d=hourly(ins,4)
    d["timestamp"]=pd.to_datetime(["2024-01-01 10:00Z","2024-01-01 11:00Z","2024-01-01 14:00Z","2024-01-01 15:00Z"])
    d["open_time"]=d.timestamp-pd.Timedelta(hours=1)
    with pytest.raises(ValueError,match="no complete"): resample(d,"4H",ins)


def test_monthly_release_after_period_end(history,instrument):
    result,_=resample(history.iloc[:31],"1M",instrument,as_of=pd.Timestamp("2024-02-01",tz="UTC"))
    assert result.timestamp.iloc[0]==pd.Timestamp("2024-02-01",tz="UTC")
    with pytest.raises(ValueError): resample(history.iloc[:30],"1M",instrument,as_of=pd.Timestamp("2024-01-30",tz="UTC"))


def test_mtf_never_joins_unclosed_bar():
    base=pd.DataFrame({"timestamp":pd.to_datetime(["2024-01-01 12:00Z","2024-01-01 16:00Z"])})
    higher=pd.DataFrame({"timestamp":pd.to_datetime(["2024-01-01 16:00Z"]),"close":[42]})
    joined=align_confirmed(base,higher,["close"],"d_")
    assert pd.isna(joined.d_close.iloc[0]) and joined.d_close.iloc[1]==42


def test_cache_snapshot_and_tamper_detection(dataset,tmp_path):
    store=ParquetStore(tmp_path)
    saved=store.save("test",dataset)
    assert data_hash(store.load("test").bars)==data_hash(dataset.bars)
    path=tmp_path/saved.metadata["parquet"]
    changed=dataset.bars.copy()
    changed.loc[0,"volume"]+=1
    changed.to_parquet(path,index=False)
    with pytest.raises(ValueError,match="checksum"): store.load("test")


def test_offline_source_cannot_impersonate_efinance(instrument,tmp_path):
    with pytest.raises(ValueError,match="source"): import_csv(tmp_path/"none.csv",instrument,"1D","efinance")


def test_nav_not_ohlcv(instrument):
    with pytest.raises(DataValidationError): normalize(pd.DataFrame({"鏃ユ湡":["2024-01-01"],"鍗曚綅鍑€鍊?:[1.]}),instrument,"1D")

