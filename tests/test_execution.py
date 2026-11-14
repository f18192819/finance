from dataclasses import replace
import pytest
from quant_research.backtest import BacktestEngine
from quant_research.backtest.costs import Costs
from quant_research.models import Signal
from quant_research.risk import RiskConfig,size_position
from conftest import make_bars


ZERO=Costs(commission_bps=0,slippage_bps=0,spread_bps=0)


def signal(d,**kw):
    p=dict(timestamp=d.timestamp.iloc[0],symbol="TEST",strategy="test",direction=1,entry=100,stop=90,target=130,tp1=None)
    p.update(kw)
    return Signal(**p)


def run(d,ins,signals=None,risk=None,cost=ZERO,metadata=None):
    return BacktestEngine(risk or RiskConfig(initial_equity=100000),{"TEST":cost}).run({"TEST":d},{"TEST":ins},signals or [signal(d)],metadata)


def test_next_bar_entry_stop_first(instrument):
    d=make_bars([[100,140,80,100],[100,140,80,100],[100,102,98,100]])
    r=run(d,instrument)
    assert r.fills.iloc[0].timestamp==d.open_time.iloc[1]
    assert r.trades.iloc[0].reason=="STOP_FIRST"
    assert r.trades.iloc[0].pnl==-1000
    assert r.total_return==pytest.approx(-.01)


def test_partial_exit_exact_accounting(instrument):
    d=make_bars([[100,102,98,100],[100,116,99,110],[110,131,109,130]])
    r=run(d,instrument,[signal(d,tp1=115,partial_fraction=.5)])
    assert r.fills.quantity.tolist()==[100,50,50]
    assert r.trades.iloc[0].pnl==2250
    assert r.equity_curve.equity.iloc[-1]==102250
    assert r.total_trades==1


def test_entry_gap_rechecks_rr(instrument):
    d=make_bars([[100,101,99,100],[120,125,115,120]])
    r=run(d,instrument)
    assert r.fills.empty
    assert "Gap/rounding" in r.risk_events.reason.iloc[0]


def test_stop_gap_fills_open_not_stop(instrument):
    d=make_bars([[100,101,99,100],[100,102,98,100],[80,85,75,82]])
    r=run(d,instrument)
    assert r.trades.exit_price.iloc[0]==80
    assert r.trades.pnl.iloc[0]==-2000


def test_tplusone_defers_same_day_stop(instrument):
    d=make_bars([[100,102,98,100],[100,105,80,100],[85,100,80,95]])
    r=run(d,replace(instrument,settlement_days=1))
    assert r.trades.exit_time.iloc[0]==d.open_time.iloc[2]
    assert r.trades.pnl.iloc[0]==-1500
    assert r.risk_events.reason.str.contains(r"T\+1").any()


def test_zero_volume_and_single_price_no_fills(instrument):
    d=make_bars([[100,102,98,100],[100,100,100,100],[100,102,98,100]])
    d.loc[2,"volume"]=0
    r=run(d,instrument)
    assert r.fills.empty


def test_limit_intrabar_no_optimistic_target(instrument):
    d=make_bars([[100,102,98,100],[105,135,95,110],[110,112,108,110]])
    r=run(d,instrument,[signal(d,order_type="LIMIT")])
    assert r.fills.iloc[0].price==100
    assert "TP2" not in r.fills.reason.tolist()
    assert r.trades.pnl.iloc[0]==1000


def test_short_gate_and_symmetric_pnl(instrument):
    d=make_bars([[100,102,98,100],[100,105,69,75],[75,80,70,75]])
    s=signal(d,direction=-1,stop=110,target=70)
    assert run(d,instrument,[s]).fills.empty
    cost=replace(ZERO,annual_borrow_bps=0)
    result=run(d,replace(instrument,shortable=True),[s],cost=cost)
    assert result.trades.pnl.iloc[0]==3000


def test_costs_and_lot_budget(instrument):
    ins=replace(instrument,lot_size=10)
    cost=Costs(commission_bps=10,minimum_commission=5,slippage_bps=10,spread_bps=2)
    qty,risk=size_position(100000,100000,100,90,1,ins,cost,RiskConfig(initial_equity=100000))
    assert qty%10==0 and risk<=1000 and qty<100


def test_risk_group_blocks_second_strategy(instrument):
    d=make_bars([[100,102,98,100],[100,102,98,100],[100,102,98,100]])
    r=run(d,instrument,[signal(d,strategy="a"),signal(d,strategy="b")],risk=RiskConfig(initial_equity=100000,max_correlated_group_risk=.015))
    assert len(r.fills.loc[r.fills.action=="ENTRY"])==1
    assert r.risk_events.reason.str.contains("Correlated").any()


def test_adjustment_and_continuous_futures_rejected(instrument):
    d=make_bars([[100,102,98,100]]*3)
    with pytest.raises(ValueError,match="Adjusted"): run(d,instrument,metadata={"TEST":{"adjustment":"forward"}})
    with pytest.raises(ValueError,match="Continuous"): run(d,replace(instrument,market="FUTURES",continuous=True))


def test_mixed_currency_rejected(instrument):
    a=make_bars([[100,102,98,100]]*3)
    b=a.assign(symbol="OTHER")
    with pytest.raises(ValueError,match="currencies"):
        BacktestEngine().run({"TEST":a,"OTHER":b},{"TEST":instrument,"OTHER":replace(instrument,symbol="OTHER",currency="CNY")},[])


def test_weekly_loss_lock(instrument):
    d=make_bars([[100,102,98,100],[100,102,80,100],[100,102,98,100],[100,102,98,100]])
    r=run(d,instrument,[signal(d),signal(d,timestamp=d.timestamp.iloc[1])],risk=RiskConfig(initial_equity=100000,weekly_loss_limit=.005))
    assert r.total_trades==1
    assert r.risk_events.reason.str.contains("Weekly").any()


def test_last_day_tplusone_remains_marked_open(instrument):
    d=make_bars([[100,102,98,100],[100,110,98,105]])
    r=run(d,replace(instrument,settlement_days=1))
    assert r.total_trades==0 and r.metrics["open_positions_at_end"]==1
    assert r.metrics["unrealized_pnl_at_end"]==500


def test_trailing_stop_only_effective_next_bar(instrument):
    d=make_bars([[100,102,98,100]]*16+[[100,120,99,118],[118,120,110,112]])
    s=signal(d,timestamp=d.timestamp.iloc[15],target=200)
    r=run(d,instrument,[s],risk=RiskConfig(initial_equity=100000,trailing_atr=1))
    assert r.trades.exit_time.iloc[0]>=d.open_time.iloc[17]

