from dataclasses import replace
import json
import os
import subprocess
import sys
import pandas as pd
import pytest
from quant_research.models import Dataset,Signal
from quant_research.backtest import BacktestEngine
from quant_research.backtest.costs import Costs
from quant_research.risk import RiskConfig
from quant_research.research.experiments import ExperimentManager
from quant_research.research.robustness import walk_forward
from quant_research.service import run_experiment
from quant_research.strategies import make_strategy
from conftest import make_bars


def test_cli_csv_real_flow_with_explicit_synthetic_label(dataset,tmp_path):
    path=tmp_path/"synthetic_test_only.csv"
    dataset.bars.to_csv(path,index=False)
    result=subprocess.run([sys.executable,"-m","quant_research.cli","backtest","--symbol","510300","--csv",str(path),
        "--source","SYNTHETIC_INTEGRATION_TEST_ONLY","--strategy","breakout"],cwd=tmp_path,capture_output=True,text=True,
        encoding="utf-8",env=dict(os.environ,PYTHONIOENCODING="utf-8"),timeout=45)
    assert result.returncode==0,result.stderr
    manifests=list((tmp_path/"outputs").glob("*/manifest.json"))
    assert len(manifests)==1
    manifest=json.loads(manifests[0].read_text(encoding="utf-8"))
    assert "SYNTHETIC_INTEGRATION_TEST_ONLY" in manifest["data_metadata"]["510300"]["source"]


def test_recorded_signal_replay_is_exact(instrument,tmp_path):
    d=make_bars([[100,102,98,100],[100,115,98,110],[110,132,108,130]])
    ds=Dataset(d,dict(source="SYNTHETIC_TEST_ONLY",timeframe="1D",adjustment="none"))
    signal=Signal(d.timestamp.iloc[0],"TEST","test",1,100,90,130)
    manager=ExperimentManager(tmp_path)
    costs={"TEST":Costs(commission_bps=0,slippage_bps=0,spread_bps=0)}
    r,eid=run_experiment({"TEST":ds},{"TEST":instrument},[make_strategy("breakout")],
        RiskConfig(initial_equity=100000),costs=costs,manager=manager,signals=[signal])
    replay,_=manager.reproduce(eid)
    assert r.metrics==replay.metrics
    pd.testing.assert_frame_equal(r.trades,replay.trades)


def test_futures_multiplier_and_margin(instrument):
    ins=replace(instrument,market="FUTURES",multiplier=10,margin_rate=.1,expiry="2024-02-01",shortable=True)
    d=make_bars([[100,102,98,100],[100,102,98,100],[100,135,98,130]])
    s=Signal(d.timestamp.iloc[0],"TEST","test",1,100,90,130)
    r=BacktestEngine(RiskConfig(initial_equity=100000),{"TEST":Costs(commission_bps=0,slippage_bps=0,spread_bps=0)}).run({"TEST":d},{"TEST":ins},[s])
    assert r.trades.quantity.iloc[0]==10
    assert r.trades.pnl.iloc[0]==3000
    assert r.equity_curve.reserved_margin.max()==1000


def test_unclosed_input_rejected(instrument):
    d=make_bars([[100,102,98,100]]*3)
    with pytest.raises(ValueError,match="unclosed"):
        BacktestEngine().run({"TEST":d},{"TEST":instrument},[],{"TEST":{"as_of":"2024-01-02T12:00:00Z"}})


def test_walk_forward_runs_disjoint_test_and_replays(dataset,instrument,tmp_path):
    manager=ExperimentManager(tmp_path)
    table=walk_forward(dataset,instrument,"breakout",{"target_r":[3.]},
        [["2024-01-01","2024-08-31","2024-09-01","2024-12-31"]],parameters=dict(ema_fast=5,ema_slow=20),manager=manager,min_trades=0)
    assert table.status.iloc[0]=="OOS"
    eid=table.experiment_id.iloc[0]
    m=manager.manifest(eid)
    assert m["config"]["supplied_signals"]
    replay,_=manager.reproduce(eid)
    original=json.loads((tmp_path/eid/"metrics.json").read_text(encoding="utf-8"))
    assert original==replay.metrics
