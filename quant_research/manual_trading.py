from dataclasses import asdict
from pathlib import Path
import json
import uuid
import duckdb
import pandas as pd
from .risk import RiskConfig,size_position
from .backtest.costs import Costs,tick_round


def trade_plan(signal,instrument,equity,risk=None,costs=None):
    risk, costs = risk or RiskConfig.defaults(), costs or Costs.for_market(instrument.market)
    if not instrument.tradable or instrument.continuous:
        raise ValueError("Instrument is not eligible for executable trade plans")
    if signal.direction < 0 and (not instrument.shortable or (instrument.market!="FUTURES" and costs.annual_borrow_bps is None)):
        raise ValueError("Shorting mechanism and borrow costs must be verified first")
    side = signal.direction
    entry = costs.fill(signal.entry,side,instrument.tick_size)
    stop = tick_round(signal.stop,instrument.tick_size,-side)
    quantity,amount = size_position(equity,equity,entry,stop,side,instrument,costs,risk)
    if side*(entry-stop)<=0 or side*(signal.target-entry)/abs(entry-stop)<signal.minimum_rr or quantity<=0:
        raise ValueError("Costs/rounding invalidate RR or available risk budget")
    return dict(plan_id=uuid.uuid4().hex,created_at=str(pd.Timestamp.now(tz="UTC")),signal=asdict(signal),symbol=instrument.symbol,
        currency=instrument.currency,entry_reference=entry,stop=stop,tp1=signal.tp1,tp2=signal.target,quantity=quantity,
        risk_amount=amount,risk_fraction=amount/equity if equity else None,mode="MANUAL_REVIEW_REQUIRED",
        checks=["Check live price and spread; recompute gap-adjusted RR", "Verify existing positions and correlated risk", "Check corporate actions, fees and tradability", "Check borrow availability if short"],
        note="Quantity assumes no existing positions; historical signal reference, not a live order. No broker connection.")


class TradingJournal:
    def __init__(self,path="outputs/journal.duckdb"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with duckdb.connect(str(self.path)) as con:
            con.execute("CREATE TABLE IF NOT EXISTS journal (id VARCHAR, created_at VARCHAR, symbol VARCHAR, status VARCHAR, notes VARCHAR, plan VARCHAR)")

    def add(self,plan,status,notes=""):
        if status not in ("WATCHING","ACCEPTED_MANUALLY","REJECTED","CLOSED_MANUALLY"):
            raise ValueError("Invalid journal status")
        with duckdb.connect(str(self.path)) as con:
            con.execute("INSERT INTO journal VALUES (?,?,?,?,?,?)",[uuid.uuid4().hex,str(pd.Timestamp.now(tz="UTC")),plan["symbol"],status,notes,json.dumps(plan,ensure_ascii=False,default=str)])

    def list(self):
        with duckdb.connect(str(self.path),read_only=True) as con:
            return con.execute("SELECT * FROM journal ORDER BY created_at DESC").df()

