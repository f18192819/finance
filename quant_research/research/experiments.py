from dataclasses import asdict
from pathlib import Path
import hashlib
import importlib.metadata
import json
import platform
import uuid
import zipfile
import duckdb
import pandas as pd
from ..data.storage import data_hash, write_json


class ExperimentManager:
    def __init__(self, root="outputs"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = self.root / "experiments.duckdb"
        with duckdb.connect(str(self.db)) as con:
            con.execute("CREATE TABLE IF NOT EXISTS experiments (id VARCHAR PRIMARY KEY, created_at VARCHAR, fingerprint VARCHAR, strategy VARCHAR, metadata VARCHAR, metrics VARCHAR, best BOOLEAN DEFAULT FALSE)")
            con.execute("CREATE TABLE IF NOT EXISTS trade_records (experiment_id VARCHAR, trade_id BIGINT, record VARCHAR)")

    def save(self, result, strategies, datasets, instruments, label="", parent_id=None, contexts=None):
        versions = {name: importlib.metadata.version(name) for name in ("efinance", "numpy", "pandas", "duckdb")}
        code_root = Path(__file__).resolve().parents[1]
        source_hash = hashlib.sha256(b"".join(p.read_bytes() for p in sorted(code_root.rglob("*.py")))).hexdigest()
        manifest = dict(label=label, parent_id=parent_id, strategies=[dict(name=s.name,version=s.version,parameters=s.get_parameters()) for s in strategies],
                        instruments={k:asdict(v) for k,v in instruments.items()}, config=result.config,
                        data_versions={k:data_hash(v.bars) for k,v in datasets.items()}, dependencies=versions, source_hash=source_hash,
                        python_version=platform.python_version(),
                        context_versions={symbol:{tf:data_hash(value) if isinstance(value,pd.DataFrame) else value for tf,value in context.items()} for symbol,context in (contexts or {}).items()})
        canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, default=str)
        fingerprint = hashlib.sha256(canonical.encode()).hexdigest()
        eid = pd.Timestamp.now(tz="UTC").strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:8]
        folder = self.root/eid
        folder.mkdir()
        with zipfile.ZipFile(folder/"source_snapshot.zip","w",zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(code_root.rglob("*.py")):
                archive.write(path,Path("quant_research")/path.relative_to(code_root))
            for path in sorted((code_root.parent/"config").glob("*")):
                if path.is_file():
                    archive.write(path,Path("config")/path.name)
        for name in ("equity_curve", "trades", "fills", "risk_events", "signals"):
            frame = getattr(result,name)
            frame.to_parquet(folder/f"{name}.parquet",index=False)
            frame.to_csv(folder/f"{name}.csv",index=False,encoding="utf-8-sig")
        for symbol, ds in datasets.items():
            safe = hashlib.sha256(symbol.encode()).hexdigest()[:16]
            ds.bars.to_parquet(folder/f"input_{safe}.parquet",index=False)
            manifest.setdefault("input_files",{})[symbol] = f"input_{safe}.parquet"
            manifest.setdefault("data_metadata",{})[symbol] = ds.metadata
        for symbol,context in (contexts or {}).items():
            context_meta = {}
            for timeframe,value in context.items():
                if isinstance(value,pd.DataFrame):
                    safe = hashlib.sha256(f"{symbol}:{timeframe}".encode()).hexdigest()[:16]
                    filename = f"context_{safe}.parquet"
                    value.to_parquet(folder/filename,index=False)
                    context_meta[timeframe] = dict(file=filename,hash=data_hash(value))
                else:
                    context_meta[timeframe] = value
            manifest.setdefault("contexts",{})[symbol] = context_meta
        manifest.update(id=eid, fingerprint=fingerprint, created_at=str(pd.Timestamp.now(tz="UTC")))
        write_json(folder/"manifest.json",manifest)
        write_json(folder/"metrics.json",result.metrics)
        with duckdb.connect(str(self.db)) as con:
            con.execute("INSERT INTO experiments VALUES (?,?,?,?,?,?,false)",[eid,manifest["created_at"],fingerprint,",".join(s.name for s in strategies),json.dumps(manifest,default=str),json.dumps(result.metrics,default=str)])
            if not result.trades.empty:
                con.executemany("INSERT INTO trade_records VALUES (?,?,?)",[(eid,int(row.trade_id),json.dumps(row._asdict(),default=str)) for row in result.trades.itertuples(index=False)])
        from ..reports import export_report
        export_report(result,folder,manifest)
        return eid

    def list(self):
        with duckdb.connect(str(self.db),read_only=True) as con:
            return con.execute("SELECT id,created_at,strategy,best,metrics FROM experiments ORDER BY created_at DESC").df()

    def manifest(self,eid):
        with duckdb.connect(str(self.db),read_only=True) as con:
            row = con.execute("SELECT metadata FROM experiments WHERE id=?",[eid]).fetchone()
        if row is None:
            raise ValueError("Unknown experiment")
        return json.loads(row[0])

    def mark_best(self,eid):
        self.manifest(eid)
        with duckdb.connect(str(self.db)) as con:
            con.execute("UPDATE experiments SET best=true WHERE id=?",[eid])

    def compare(self,ids):
        rows = []
        for eid in ids:
            self.manifest(eid)
            rows.append(dict(id=eid,**json.loads((self.root/eid/"metrics.json").read_text(encoding="utf-8"))))
        return pd.DataFrame(rows)

    def reproduce(self,eid):
        from ..models import Dataset, Instrument
        from ..models import Signal
        from ..strategies import make_strategy
        from ..service import run_experiment
        from ..risk import RiskConfig
        from ..backtest.costs import Costs
        m = self.manifest(eid)
        instruments = {s:Instrument(**v) for s,v in m["instruments"].items()}
        datasets = {s:Dataset(pd.read_parquet(self.root/eid/file),m["data_metadata"][s]) for s,file in m["input_files"].items()}
        if any(data_hash(v.bars)!=m["data_versions"][s] for s,v in datasets.items()):
            raise ValueError("Experiment input checksum mismatch")
        strategies = [make_strategy(s["name"],s["parameters"]) for s in m["strategies"]]
        contexts = {}
        for symbol,context in m.get("contexts",{}).items():
            contexts[symbol] = {}
            for timeframe,value in context.items():
                if isinstance(value,dict) and "file" in value:
                    frame = pd.read_parquet(self.root/eid/value["file"])
                    if data_hash(frame)!=value["hash"]:
                        raise ValueError("Context snapshot checksum mismatch")
                    contexts[symbol][timeframe] = frame
                else:
                    contexts[symbol][timeframe] = value
        signals = None
        if m["config"].get("supplied_signals"):
            recorded = pd.read_parquet(self.root/eid/"signals.parquet")
            signals = []
            for row in recorded.to_dict("records"):
                row["reasons"] = list(row["reasons"])
                if pd.isna(row.get("tp1")):
                    row["tp1"] = None
                signals.append(Signal(**row))
        return run_experiment(datasets,instruments,strategies,RiskConfig(**m["config"]["risk"]),
                              costs={s:Costs(**v) for s,v in m["config"]["costs"].items()},manager=self,parent_id=eid,contexts=contexts,signals=signals)

