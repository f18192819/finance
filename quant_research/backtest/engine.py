from dataclasses import asdict, dataclass
import math
import numpy as np
import pandas as pd
from ..data.validation import validate_bars
from ..indicators.technical import atr
from ..models import BacktestResult
from ..risk import RiskConfig, size_position, portfolio_rejection
from .costs import Costs, tick_round
from .metrics import performance_metrics


@dataclass
class Position:
    id: int
    signal: object
    instrument: object
    entry: float
    stop: float
    target: float
    tp1: float | None
    quantity: float
    original_quantity: float
    initial_risk: float
    entry_time: object
    entry_bar: int
    entry_fee: float
    pnl: float
    fees: float
    last_cost_time: object
    partial_done: bool = False


class BacktestEngine:
    """Chronological open/close event engine. Pending orders fill at subsequent opens.

    Cash stores realized equity; reserved margin is separate. Mark-to-market includes
    unrealized P&L. No borrowed/short sale proceeds are silently treated as free cash.
    """
    def __init__(self, risk=None, costs=None):
        self.risk = risk or RiskConfig.defaults()
        self.cost_overrides = costs or {}

    def run(self, datasets, instruments, signals, metadata=None):
        if not datasets:
            raise ValueError("At least one dataset required")
        currencies = {instruments[s].currency for s in datasets}
        if len(currencies) != 1:
            raise ValueError("Mixed currencies require verified point-in-time FX; disabled")
        costs, events, frames, signal_map = {}, [], {}, {}
        for symbol, bars in datasets.items():
            ins = instruments[symbol]
            validate_bars(bars, ins)
            if not ins.tradable:
                raise ValueError(f"{symbol} is research-only, not tradable")
            if ins.continuous:
                raise ValueError("Continuous futures require verified roll map; backtest rejected")
            if ins.market == "FUTURES" and not ins.expiry:
                raise ValueError("Dated futures require a verified expiry date")
            meta = (metadata or {}).get(symbol, {})
            cutoff = pd.Timestamp(meta.get("as_of",pd.Timestamp.now(tz="UTC")))
            if cutoff.tzinfo is None or (bars.timestamp > cutoff).any():
                raise ValueError("Input contains unclosed/future bars or missing as_of timezone")
            if meta.get("adjustment", "none") != "none":
                raise ValueError("Adjusted prices cannot be treated as actual fills; supply unadjusted execution bars")
            frame = bars.copy().reset_index(drop=True)
            if "open_time" not in frame:
                raise ValueError("Explicit exchange-local open_time required for chronological execution")
            if (frame.open_time >= frame.timestamp).any() or (frame.open_time.iloc[1:].reset_index(drop=True) < frame.timestamp.iloc[:-1].reset_index(drop=True)).any():
                raise ValueError("Invalid or overlapping bar intervals")
            frame["atr"] = atr(frame)
            frames[symbol] = frame
            costs[symbol] = self.cost_overrides.get(symbol) or Costs.for_market(ins.market)
            for i, row in frame.iterrows():
                events += [(row.open_time, 1, symbol, i), (row.timestamp, 0, symbol, i)]
        for signal in signals:
            if signal.symbol not in frames:
                raise ValueError("Signal has no instrument data")
            if signal.timestamp not in set(frames[signal.symbol].timestamp):
                raise ValueError("Signal timestamp is not a closed input bar")
            signal_map.setdefault((signal.symbol, signal.timestamp), []).append(signal)
        events.sort()  # close at T precedes next bar's open at T
        self.active_costs = costs
        self.cash = self.risk.initial_equity
        self.positions, self.fills, self.closed, self.rejections = {}, [], [], []
        pending, marks, equity_rows, intrabar_entries = {}, {}, [], set()
        loss_streak, week, week_equity, trade_id = 0, None, self.cash, 0

        def account():
            unrealized = sum(p.signal.direction * (marks.get(p.instrument.symbol, p.entry)-p.entry)*p.quantity*p.instrument.multiplier for p in self.positions.values())
            margin = sum(p.entry*p.quantity*p.instrument.multiplier*p.instrument.margin_rate for p in self.positions.values())
            gross = sum(abs(marks.get(p.instrument.symbol, p.entry)*p.quantity*p.instrument.multiplier) for p in self.positions.values())
            return self.cash+unrealized, margin, gross

        def reject(timestamp, signal, reason):
            self.rejections.append(dict(timestamp=timestamp, symbol=signal.symbol, strategy=signal.strategy, reason=reason))

        def can_exit(p, timestamp):
            days = (timestamp.tz_convert(p.instrument.timezone).date() - p.entry_time.tz_convert(p.instrument.timezone).date()).days
            return days >= p.instrument.settlement_days

        def close_position(key, base_price, timestamp, bar_index, reason, quantity=None):
            nonlocal loss_streak
            pos = self.positions[key]
            ins, cost, side = pos.instrument, costs[pos.instrument.symbol], pos.signal.direction
            qty = pos.quantity if quantity is None else min(quantity, pos.quantity)
            if qty <= 0:
                return
            # Targets are limit orders; adverse slippage cannot violate their limit.
            price = cost.fill(base_price, -side, ins.tick_size, limit=base_price if reason in ("TP1", "TP2") else None)
            fee = cost.fee(price, qty, ins.multiplier, -side)
            net = side*(price-pos.entry)*qty*ins.multiplier-fee
            self.cash += net
            pos.pnl += net
            pos.fees += fee
            pos.quantity = round(pos.quantity-qty, 10)
            self.fills.append(dict(trade_id=pos.id, timestamp=timestamp, symbol=ins.symbol, strategy=pos.signal.strategy,
                                   action="EXIT", side=-side, price=price, quantity=qty, fee=fee, reason=reason))
            if pos.quantity <= 1e-9:
                self.closed.append(dict(trade_id=pos.id, symbol=ins.symbol, strategy=pos.signal.strategy, direction=side,
                    signal_time=pos.signal.timestamp, entry_time=pos.entry_time, exit_time=timestamp, entry_price=pos.entry,
                    exit_price=price, quantity=pos.original_quantity, pnl=pos.pnl, fees=pos.fees, initial_risk=pos.initial_risk,
                    r_multiple=pos.pnl/pos.initial_risk, holding_bars=bar_index-pos.entry_bar+1, reason=reason,
                    regime=pos.signal.regime, signal_reasons="; ".join(pos.signal.reasons)))
                loss_streak = loss_streak+1 if pos.pnl < 0 else 0
                del self.positions[key]

        for timestamp, kind, symbol, i in events:
            row, ins, cost = frames[symbol].iloc[i], instruments[symbol], costs[symbol]
            current_week = timestamp.tz_convert("UTC").strftime("%G-%V")
            if current_week != week:
                week, week_equity = current_week, account()[0]
            if kind == 1:
                marks[symbol] = row.open
                # Stops gapped through execute at open, subject to T+1 and liquidity.
                for key, pos in list(self.positions.items()):
                    if key[0] == symbol and row.volume > 0 and row.high > row.low and can_exit(pos, timestamp):
                        if pos.signal.direction*(row.open-pos.stop) <= 0:
                            close_position(key, row.open, timestamp, i, "GAP_STOP")
                for key in sorted([k for k in pending if k[0] == symbol]):
                    signal, born_index = pending[key]
                    if i <= born_index:
                        continue
                    if i-born_index > signal.valid_bars:
                        reject(timestamp, signal, "Order expired")
                        del pending[key]
                        continue
                    if key in self.positions:
                        del pending[key]
                        continue
                    limit_price = tick_round(signal.entry,ins.tick_size,-signal.direction) if signal.order_type=="LIMIT" else None
                    intrabar = signal.order_type == "LIMIT" and not (row.open <= limit_price if signal.direction == 1 else row.open >= limit_price)
                    if intrabar and not row.low <= limit_price <= row.high:
                        continue
                    if row.volume <= 0 or row.high == row.low:
                        reject(timestamp, signal, "Zero volume or locked single-price bar")
                        continue
                    # Quantity is reserved using information at the open, even for an intrabar limit touch.
                    self._enter(signal, key, limit_price if intrabar else row.open, timestamp, i, ins, cost, account, week_equity, loss_streak, frames, reject, trade_id)
                    if key in self.positions:
                        trade_id += 1
                        if intrabar:
                            intrabar_entries.add((key,i))
                            self.fills[-1]["reason"] = "Intrabar limit touch; quantity reserved at open; exact fill time unknown"
                    del pending[key]
            else:
                marks[symbol] = row.close
                for key, pos in list(self.positions.items()):
                    if key[0] != symbol:
                        continue
                    side = pos.signal.direction
                    # Calendar accrual, including weekends, explicit null cost items remain disclosed.
                    days = max(0., (timestamp-pos.last_cost_time).total_seconds()/86400)
                    rate = ((cost.annual_borrow_bps or 0) if side < 0 and ins.market != "FUTURES" else 0) / 365.25
                    rate += (cost.annual_financing_bps or 0)/365.25 + (cost.funding_bps_daily or 0)
                    charge = abs(pos.entry*pos.quantity*ins.multiplier) * days*rate/10000
                    self.cash -= charge
                    pos.pnl -= charge
                    pos.fees += charge
                    pos.last_cost_time = timestamp
                    if charge:
                        self.fills.append(dict(trade_id=pos.id, timestamp=timestamp, symbol=symbol, strategy=pos.signal.strategy,
                                              action="CARRY", side=0, price=pos.entry, quantity=pos.quantity, fee=charge, reason="Calendar financing"))
                    if row.volume <= 0 or row.high == row.low or not can_exit(pos, timestamp):
                        if not can_exit(pos, timestamp) and (row.low <= pos.stop if side == 1 else row.high >= pos.stop):
                            reject(timestamp, pos.signal, "Stop deferred by settlement restriction (T+1)")
                        continue
                    stop_hit = row.low <= pos.stop if side == 1 else row.high >= pos.stop
                    target_hit = row.high >= pos.target if side == 1 else row.low <= pos.target
                    if stop_hit:
                        stop_base = pos.stop if (key,i) in intrabar_entries else min(row.open,pos.stop) if side==1 else max(row.open,pos.stop)
                        close_position(key, stop_base, timestamp, i, "STOP_FIRST" if target_hit else "STOP")
                        continue
                    if (key,i) not in intrabar_entries:
                        tp1_hit = pos.tp1 is not None and (row.high >= pos.tp1 if side==1 else row.low <= pos.tp1)
                        if tp1_hit and not pos.partial_done:
                            qty = math.floor(pos.original_quantity*pos.signal.partial_fraction/ins.lot_size)*ins.lot_size
                            if 0 < qty < pos.quantity:
                                close_position(key, pos.tp1, timestamp, i, "TP1", qty)
                            pos.partial_done = True
                        if target_hit and key in self.positions:
                            close_position(key, pos.target, timestamp, i, "TP2")
                            continue
                    if i == len(frames[symbol])-1:
                        close_position(key, row.close, timestamp, i, "END_OF_DATA")
                    elif ins.expiry and timestamp.tz_convert(ins.timezone).date() >= pd.Timestamp(ins.expiry).date():
                        close_position(key, row.close, timestamp, i, "CONTRACT_EXPIRY")
                    if key in self.positions and self.risk.trailing_atr > 0 and np.isfinite(row.atr):
                        proposed = row.close-side*row.atr*self.risk.trailing_atr
                        pos.stop = max(pos.stop, proposed) if side==1 else min(pos.stop, proposed)
                        pos.stop = tick_round(pos.stop, ins.tick_size, -side)
                for signal in signal_map.get((symbol, timestamp), []):
                    key = (symbol, signal.strategy)
                    if key not in self.positions:
                        pending[key] = (signal, i)
            # Holding-time/reversal market exits are decided at prior close and executed now.
            if kind == 1:
                for key, pos in list(self.positions.items()):
                    if key[0] == symbol and i-pos.entry_bar >= self.risk.max_holding_bars and can_exit(pos,timestamp) and row.volume>0 and row.high>row.low:
                        close_position(key, row.open, timestamp, i, "TIME_EXIT")
            equity, margin, gross = account()
            notionals = {}
            for pos in self.positions.values():
                asset = pos.instrument.symbol
                notionals[asset] = notionals.get(asset,0)+abs(marks.get(asset,pos.entry)*pos.quantity*pos.instrument.multiplier)
            hhi = sum((value/gross)**2 for value in notionals.values()) if gross>0 else 0
            equity_rows.append(dict(timestamp=timestamp, equity=equity, cash=self.cash, reserved_margin=margin,
                                    exposure=gross/equity if equity>0 else 0, open_positions=len(self.positions),concentration_hhi=hhi))
        curve = pd.DataFrame(equity_rows).drop_duplicates("timestamp", keep="last").reset_index(drop=True)
        trades, fills = pd.DataFrame(self.closed), pd.DataFrame(self.fills)
        metrics = performance_metrics(curve, trades, self.risk.initial_equity)
        metrics["open_positions_at_end"] = len(self.positions)
        metrics["unrealized_pnl_at_end"] = account()[0]-self.cash
        config = dict(risk=asdict(self.risk), costs={s:asdict(c) for s,c in costs.items()}, currency=next(iter(currencies)),
                      execution="next_bar_open; conservative stop-first; intrabar limit entry has no same-bar target",
                      assumptions=["OHLC cannot reveal intrabar path", "Zero-volume and single-price bars cannot fill",
                      "Final open position liquidated only if settlement permits", "No corporate action ledger; price returns only",
                      "No maintenance-margin liquidation model", "Current universe has survivorship bias"], data=metadata or {})
        return BacktestResult(metrics, curve, trades, fills, pd.DataFrame(self.rejections), pd.DataFrame([asdict(s) for s in signals]), config)

    def _enter(self, signal, key, base_price, timestamp, index, ins, cost, account, week_equity, loss_streak, frames, reject, trade_id):
        if signal.direction == -1 and (not ins.shortable or (ins.market != "FUTURES" and cost.annual_borrow_bps is None)):
            reject(timestamp, signal, "Shorting disabled or borrow costs unverified")
            return
        if ins.expiry and timestamp.tz_convert(ins.timezone).date() >= pd.Timestamp(ins.expiry).date():
            reject(timestamp, signal, "Contract at/past expiry")
            return
        side = signal.direction
        limit = tick_round(signal.entry, ins.tick_size, -side) if signal.order_type == "LIMIT" else None
        price = cost.fill(base_price, side, ins.tick_size, limit=limit)
        stop = tick_round(signal.stop, ins.tick_size, -side)
        target = tick_round(signal.target, ins.tick_size, -side)
        distance = side*(price-stop)
        if distance <= 0 or side*(target-price)/distance < signal.minimum_rr:
            reject(timestamp, signal, "Gap/rounding invalidates stop or minimum reward/risk")
            return
        equity, margin, gross = account()
        quantity, new_risk = size_position(equity, max(0,self.cash-margin), price, stop, side, ins, cost, self.risk)
        if quantity <= 0:
            reject(timestamp, signal, "Insufficient risk budget/margin for one lot")
            return
        fee = cost.fee(price,quantity,ins.multiplier,side)
        partial_qty = math.floor(quantity*signal.partial_fraction/ins.lot_size)*ins.lot_size if signal.tp1 is not None else 0
        tp1 = tick_round(signal.tp1,ins.tick_size,-side) if signal.tp1 is not None else target
        projected_reward = side*(target-price)*(quantity-partial_qty)*ins.multiplier
        projected_fees = fee + cost.fee(target,quantity-partial_qty,ins.multiplier,-side)
        if partial_qty:
            projected_reward += side*(tp1-price)*partial_qty*ins.multiplier
            projected_fees += cost.fee(tp1,partial_qty,ins.multiplier,-side)
        if (projected_reward-projected_fees)/new_risk < signal.minimum_rr:
            reject(timestamp,signal,"Net weighted reward/risk after partial exits and costs below minimum")
            return
        def remaining_risk(pos):
            costsafe = self.active_costs[pos.instrument.symbol]
            exit_price = costsafe.fill(pos.stop, -pos.signal.direction, pos.instrument.tick_size)
            return max(0,pos.signal.direction*(pos.entry-exit_price))*pos.quantity*pos.instrument.multiplier + costsafe.fee(exit_price,pos.quantity,pos.instrument.multiplier,-pos.signal.direction)
        open_risk = sum(remaining_risk(pos) for pos in self.positions.values())
        correlated = 0
        for pos in self.positions.values():
            linked = pos.instrument.group == ins.group
            if not linked:
                a = frames[ins.symbol].loc[lambda d: d.timestamp < timestamp].set_index("timestamp").close.pct_change(fill_method=None)
                b = frames[pos.instrument.symbol].loc[lambda d: d.timestamp < timestamp].set_index("timestamp").close.pct_change(fill_method=None)
                pair = pd.concat([a,b],axis=1).dropna().tail(self.risk.correlation_window)
                linked = len(pair)>=20 and abs(pair.iloc[:,0].corr(pair.iloc[:,1]))>=self.risk.correlation_threshold
            if linked:
                correlated += remaining_risk(pos)
        reason = portfolio_rejection(equity,new_risk,open_risk,correlated,week_equity,loss_streak,len(self.positions),
                                     (gross+quantity*price*ins.multiplier)/equity if equity>0 else float("inf"),self.risk)
        if reason:
            reject(timestamp, signal, reason)
            return
        self.cash -= fee
        self.positions[key] = Position(trade_id,signal,ins,price,stop,target,
            tick_round(signal.tp1,ins.tick_size,-side) if signal.tp1 is not None else None,
            quantity,quantity,new_risk,timestamp,index,fee,-fee,fee,timestamp)
        self.fills.append(dict(trade_id=trade_id,timestamp=timestamp,symbol=ins.symbol,strategy=signal.strategy,
                               action="ENTRY",side=side,price=price,quantity=quantity,fee=fee,reason="Next available bar"))
