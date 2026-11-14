from dataclasses import asdict
from itertools import product
import numpy as np
import pandas as pd
from ..backtest.engine import BacktestEngine
from ..models import Dataset
from ..strategies import make_strategy
from ..service import run_experiment


def parameter_grid(grid):
    keys = list(grid)
    return [dict(zip(keys,values)) for values in product(*(grid[k] for k in keys))]


def sensitivity(dataset,instrument,strategy_name,grid,base_parameters=None,risk=None,manager=None):
    rows = []
    for params in parameter_grid(grid):
        strategy = make_strategy(strategy_name,dict(base_parameters or {},**params))
        result,eid = run_experiment({instrument.symbol:dataset},{instrument.symbol:instrument},[strategy],risk,manager=manager,label="parameter_sensitivity")
        rows.append(dict(**params,**result.metrics,experiment_id=eid))
    return pd.DataFrame(rows)


def ablation(dataset,instrument,strategy_name,parameters=None,risk=None,manager=None):
    rows = []
    for removed in (None,"trend","structure","zone","volume","momentum"):
        p = dict(parameters or {},disabled_factors=[] if removed is None else [removed])
        strategy = make_strategy(strategy_name,p)
        result,eid = run_experiment({instrument.symbol:dataset},{instrument.symbol:instrument},[strategy],risk,manager=manager,label="score_ablation")
        rows.append(dict(removed=removed or "baseline",experiment_id=eid,**result.metrics))
    return pd.DataFrame(rows)


def walk_forward(dataset,instrument,strategy_name,grid,folds,parameters=None,risk=None,manager=None,min_trades=5):
    """Select solely on training; OOS folds cannot overlap. Warm-up history never traded in OOS."""
    rows, last_test_end = [], None
    for train_start,train_end,test_start,test_end in folds:
        ts,te,vs,ve = [pd.Timestamp(v,tz="UTC") for v in (train_start,train_end,test_start,test_end)]
        if len(train_end)==10:
            te += pd.Timedelta(days=1)-pd.Timedelta(nanoseconds=1)
        if len(test_end)==10:
            ve += pd.Timedelta(days=1)-pd.Timedelta(nanoseconds=1)
        if not ts<te<vs<ve or (last_test_end is not None and vs<=last_test_end):
            raise ValueError("Invalid or overlapping walk-forward folds")
        last_test_end = ve
        bars = dataset.bars
        train = bars.loc[(bars.timestamp>=ts)&(bars.timestamp<=te)].reset_index(drop=True)
        test = bars.loc[(bars.timestamp>=vs)&(bars.timestamp<=ve)].reset_index(drop=True)
        if train.empty or test.empty:
            raise ValueError("No actual data in requested train/test range")
        training = sensitivity(Dataset(train,dataset.metadata),instrument,strategy_name,grid,parameters,risk,manager)
        eligible = training.loc[training.total_trades>=min_trades].copy()
        if eligible.empty:
            rows.append(dict(train_start=str(ts),test_start=str(vs),status="INSUFFICIENT_TRAINING_TRADES"))
            continue
        eligible["objective"] = eligible.total_return - 2*eligible.max_drawdown
        best = eligible.sort_values(["objective","max_drawdown"],ascending=[False,True]).iloc[0]
        params = dict(parameters or {},**{k:best[k].item() if hasattr(best[k],"item") else best[k] for k in grid})
        strategy = make_strategy(strategy_name,params)
        history = bars.loc[(bars.timestamp>=ts)&(bars.timestamp<=ve)].reset_index(drop=True)
        all_signals = strategy.generate_signals(history)
        oos_signals = [s for s in all_signals if vs<=s.timestamp<=ve]
        test_meta = dict(dataset.metadata,walk_forward=dict(train_start=str(ts),train_end=str(te),test_start=str(vs),test_end=str(ve),selection="train total_return - 2*max_drawdown",selected_parameters=params))
        result,eid = run_experiment({instrument.symbol:Dataset(test,test_meta)},{instrument.symbol:instrument},[strategy],risk,manager=manager,label="walk_forward_oos",signals=oos_signals)
        rows.append(dict(train_start=str(ts),train_end=str(te),test_start=str(vs),test_end=str(ve),status="OOS",parameters=params,experiment_id=eid,**result.metrics))
    return pd.DataFrame(rows)


def monte_carlo(trades,initial_equity=1_000_000,simulations=1000,seed=42,method="bootstrap"):
    if trades.empty or len(trades)<2:
        raise ValueError("Monte Carlo requires at least two closed trades")
    if method not in ("bootstrap","permutation") or simulations<1:
        raise ValueError("Invalid Monte Carlo configuration")
    rng = np.random.default_rng(seed)
    pnl = trades.pnl.to_numpy(float)
    paths = np.empty((simulations,len(pnl)+1))
    for i in range(simulations):
        sample = rng.choice(pnl,len(pnl),replace=True) if method=="bootstrap" else rng.permutation(pnl)
        paths[i] = np.r_[initial_equity,initial_equity+np.cumsum(sample)]
    peaks = np.maximum.accumulate(paths,axis=1)
    drawdowns = (1-paths/peaks).max(axis=1)
    totals = paths[:,-1]/initial_equity-1
    summary = dict(method=method,seed=seed,simulations=simulations,loss_probability=float((totals<0).mean()),
                   return_quantiles=dict(zip(["5%","50%","95%"],np.quantile(totals,[.05,.5,.95]).tolist())),
                   drawdown_quantiles=dict(zip(["5%","50%","95%"],np.quantile(drawdowns,[.05,.5,.95]).tolist())),
                   assumptions="Fixed historical currency P&L; no compounding or portfolio overlap; IID bootstrap ignores dependence. Not a forecast.")
    return summary,pd.DataFrame(paths.T),pd.DataFrame(dict(total_return=totals,max_drawdown=drawdowns))


def correlation_analysis(datasets,instruments,window=60):
    returns = pd.concat({s:d.bars.set_index("timestamp").close.pct_change(fill_method=None) for s,d in datasets.items()},axis=1)
    corr = returns.tail(window).corr(min_periods=min(20,window))
    by_group = returns.T.groupby({s:instruments[s].group for s in returns.columns}).mean().T.corr()
    by_sector = returns.T.groupby({s:instruments[s].sector for s in returns.columns}).mean().T.corr()
    return dict(assets=corr,groups=by_group,sectors=by_sector,rolling=returns.rolling(window,min_periods=20).corr(),
                note="Aligned close-to-close returns; stale/non-overlapping calendars can make correlations unavailable")

