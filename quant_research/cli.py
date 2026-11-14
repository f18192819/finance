import argparse
import json
from pathlib import Path
from .config import InstrumentRegistry
from .data.provider import EfinanceProvider
from .data.validation import import_csv
from .data.storage import write_json
from .research.experiments import ExperimentManager
from .research.robustness import sensitivity,monte_carlo,walk_forward,ablation
from .strategies import STRATEGIES,make_strategy
from .service import run_experiment


def main(argv=None):
    parser = argparse.ArgumentParser(description="Multi-Market Quant Research 路 efinance only 路 manual trading")
    sub = parser.add_subparsers(dest="command",required=True)
    probe = sub.add_parser("probe")
    probe.add_argument("--start",default="2025-01-01")
    probe.add_argument("--end",default="2025-12-31")
    for cmd in ("download","backtest","sensitivity","ablation","walk-forward"):
        p = sub.add_parser(cmd)
        p.add_argument("--symbol",default="510300")
        p.add_argument("--start",default="2021-01-01")
        p.add_argument("--end",default="2025-12-31")
        p.add_argument("--timeframe",choices=["1H","4H","1D","1W","1M"],default="1D")
        p.add_argument("--csv",type=Path)
        p.add_argument("--source",default="user_provided_csv")
        p.add_argument("--refresh",action="store_true")
        if cmd!="download":
            p.add_argument("--strategy",choices=list(STRATEGIES),default="trend_following")
            p.add_argument("--parameters",type=Path,help="JSON parameter object")
        if cmd in ("sensitivity","walk-forward"):
            p.add_argument("--grid",type=Path,required=True)
        if cmd=="walk-forward":
            p.add_argument("--folds",type=Path,required=True,help="JSON array of [train_start,train_end,test_start,test_end]")
    sub.add_parser("experiments")
    rep = sub.add_parser("reproduce")
    rep.add_argument("id")
    mc = sub.add_parser("monte-carlo")
    mc.add_argument("id")
    mc.add_argument("--seed",type=int,default=42)
    mc.add_argument("--method",choices=["bootstrap","permutation"],default="bootstrap")
    args = parser.parse_args(argv)
    manager = ExperimentManager()
    try:
        if args.command=="probe":
            print(json.dumps(EfinanceProvider().probe(args.start,args.end),ensure_ascii=False,indent=2))
            return
        if args.command=="experiments":
            print(manager.list().to_string(index=False))
            return
        if args.command=="reproduce":
            result,eid = manager.reproduce(args.id)
            print(eid,json.dumps(result.metrics,ensure_ascii=False))
            return
        if args.command=="monte-carlo":
            import pandas as pd
            manifest = manager.manifest(args.id)
            trades = pd.read_parquet(manager.root/args.id/"trades.parquet")
            summary,paths,distribution = monte_carlo(trades,manifest["config"]["risk"]["initial_equity"],seed=args.seed,method=args.method)
            write_json(manager.root/args.id/f"mc_{args.method}_{args.seed}.json",summary)
            distribution.to_csv(manager.root/args.id/f"mc_{args.method}_{args.seed}.csv",index=False)
            print(json.dumps(summary,ensure_ascii=False,indent=2))
            return
        ins = InstrumentRegistry().get(args.symbol)
        ds = import_csv(args.csv,ins,args.timeframe,args.source) if args.csv else EfinanceProvider().get_historical_data(args.symbol,args.start,args.end,args.timeframe,refresh=args.refresh)
        if args.command=="download":
            print(json.dumps(ds.metadata,ensure_ascii=False,indent=2,default=str))
            return
        params = json.loads(args.parameters.read_text(encoding="utf-8")) if args.parameters else {}
        if args.command=="backtest":
            strategy = make_strategy(args.strategy,params)
            contexts = None
            if strategy.parameters["mode"]=="multi_timeframe":
                if args.csv:
                    raise ValueError("CLI strict MTF needs online context or use Python API with explicit CSV contexts")
                provider = EfinanceProvider()
                contexts = {ins.symbol:{tf:provider.get_historical_data(ins.symbol,args.start,args.end,tf).bars for tf in ("1D","4H")}}
                contexts[ins.symbol]["base_timeframe"] = args.timeframe
            result,eid = run_experiment({ins.symbol:ds},{ins.symbol:ins},[strategy],contexts=contexts,manager=manager)
            print(f"Experiment: {eid}\nReport: {manager.root/eid/'report.html'}")
            print(json.dumps(result.metrics,ensure_ascii=False,indent=2))
        else:
            if args.command=="ablation":
                table = ablation(ds,ins,args.strategy,params,manager=manager)
            else:
                grid = json.loads(args.grid.read_text(encoding="utf-8"))
                if args.command=="sensitivity":
                    table = sensitivity(ds,ins,args.strategy,grid,params,manager=manager)
                else:
                    folds = json.loads(args.folds.read_text(encoding="utf-8"))
                    table = walk_forward(ds,ins,args.strategy,grid,folds,params,manager=manager)
            table.to_csv(manager.root/f"{args.command}.csv",index=False,encoding="utf-8-sig")
            print(table.to_string(index=False))
    except Exception as exc:
        parser.exit(1,f"ERROR: {exc}\n")


if __name__=="__main__":
    main()

