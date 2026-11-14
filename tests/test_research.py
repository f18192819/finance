import pandas as pd
import pytest
from quant_research.decision import score_candidate
from quant_research.research.experiments import ExperimentManager
from quant_research.research.robustness import monte_carlo,walk_forward
from quant_research.service import run_experiment
from quant_research.strategies import make_strategy
from quant_research.manual_trading import TradingJournal


def test_hard_filter_precedes_score():
    d=score_candidate(dict(trend=True,structure=True,zone=True,volume=True,momentum=True),["Portfolio risk"])
    assert d.score==100 and d.category=="REJECTED"


def test_monte_carlo_deterministic_and_permutation_terminal_invariant():
    t=pd.DataFrame({"pnl":[100,-50,75,-40,200]})
    a,p,d=monte_carlo(t,1000,100,42,"permutation")
    assert d.total_return.nunique()==1
    b,pp,dd=monte_carlo(t,1000,100,42,"permutation")
    assert a==b
    pd.testing.assert_frame_equal(p,pp)


def test_experiment_reproducible_and_saved(dataset,instrument,tmp_path):
    manager=ExperimentManager(tmp_path)
    result,eid=run_experiment({"TEST":dataset},{"TEST":instrument},[make_strategy("breakout",dict(ema_fast=5,ema_slow=20))],manager=manager)
    replay,new_id=manager.reproduce(eid)
    pd.testing.assert_frame_equal(result.equity_curve,replay.equity_curve)
    assert result.metrics==replay.metrics
    assert (tmp_path/eid/"report.html").exists()
    assert manager.manifest(eid)["data_metadata"]["TEST"]["source"]=="SYNTHETIC_UNIT_TEST_ONLY"
    manager.mark_best(eid)
    assert len(manager.compare([eid,new_id]))==2


def test_walk_forward_rejects_leaking_split(dataset,instrument,tmp_path):
    with pytest.raises(ValueError,match="overlapping"):
        walk_forward(dataset,instrument,"breakout",{"target_r":[3]},[["2024-01-01","2024-06-01","2024-05-01","2024-12-31"]],manager=ExperimentManager(tmp_path))


def test_journal_has_no_execution_side_effect(tmp_path):
    journal=TradingJournal(tmp_path/"journal.duckdb")
    journal.add({"symbol":"TEST"},"WATCHING","Test only")
    assert journal.list().status.iloc[0]=="WATCHING"

