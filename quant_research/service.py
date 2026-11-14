from .backtest import BacktestEngine
from .research.experiments import ExperimentManager


def run_experiment(datasets,instruments,strategies,risk=None,costs=None,contexts=None,manager=None,label="",parent_id=None,signals=None):
    for ds in datasets.values():
        if not ds.metadata.get("source") or not ds.metadata.get("timeframe"):
            raise ValueError("Every experiment requires explicit data source and timeframe")
    generated = [] if signals is None else list(signals)
    if signals is None:
        for symbol,ds in datasets.items():
            for strategy in strategies:
                generated.extend(strategy.generate_signals(ds.bars,(contexts or {}).get(symbol)))
    result = BacktestEngine(risk,costs).run({s:d.bars for s,d in datasets.items()},instruments,generated,{s:d.metadata for s,d in datasets.items()})
    result.config["supplied_signals"] = signals is not None
    manager = manager or ExperimentManager()
    eid = manager.save(result,strategies,datasets,instruments,label,parent_id,contexts)
    return result,eid
