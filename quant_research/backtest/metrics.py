import numpy as np
import pandas as pd


def performance_metrics(equity_curve, trades, initial_equity):
    if equity_curve.empty:
        raise ValueError("Empty equity curve")
    series = equity_curve.set_index("timestamp").equity
    total = series.iloc[-1]/initial_equity-1
    elapsed = (series.index[-1]-series.index[0]).total_seconds()/86400
    cagr = (series.iloc[-1]/initial_equity)**(365.25/elapsed)-1 if elapsed > 0 and series.iloc[-1] > 0 else None
    peak = np.maximum.accumulate(np.r_[initial_equity, series.to_numpy()])
    dd = 1-np.r_[initial_equity, series.to_numpy()]/peak
    max_dd = float(dd.max())
    # Calendar daily observations (weekends included); 365.25 scaling is consistent.
    daily = series.resample("D").last().ffill()
    daily = pd.concat([pd.Series([initial_equity], index=[daily.index[0]-pd.Timedelta(days=1)]), daily])
    returns = daily.pct_change(fill_method=None).dropna()
    std = returns.std(ddof=1)
    sharpe = float(returns.mean()/std*np.sqrt(365.25)) if len(returns)>1 and std>0 else None
    downside = np.sqrt(np.mean(np.minimum(returns, 0)**2)) if len(returns) else 0
    sortino = float(returns.mean()/downside*np.sqrt(365.25)) if downside>0 else None
    pnl = trades.pnl if not trades.empty else pd.Series(dtype=float)
    wins, losses = pnl[pnl>0], pnl[pnl<0]
    gross_profit, gross_loss = wins.sum(), -losses.sum()
    durations = equity_curve.timestamp.shift(-1).sub(equity_curve.timestamp).dt.total_seconds().fillna(0)
    exposure = float((equity_curve.exposure*durations).sum()/durations.sum()) if durations.sum()>0 else 0.
    time_in_market = float(((equity_curve.open_positions>0)*durations).sum()/durations.sum()) if durations.sum()>0 else 0.
    # Undefined / infinite ratios are null, never serialized as fabricated zeros.
    return dict(total_return=float(total), net_profit=float(series.iloc[-1]-initial_equity), annual_return=cagr, cagr=cagr,
        max_drawdown=max_dd, sharpe_ratio=sharpe, sortino_ratio=sortino,
        calmar_ratio=cagr/max_dd if max_dd and cagr is not None else None,
        recovery_factor=float((series.iloc[-1]-initial_equity)/(peak*dd).max()) if (peak*dd).max()>0 else None,
        profit_factor=float(gross_profit/gross_loss) if gross_loss>0 else None,
        gross_profit=float(gross_profit), gross_loss=float(gross_loss), expectancy=float(pnl.mean()) if len(pnl) else None,
        expectancy_r=float(trades.r_multiple.mean()) if len(pnl) else None,
        win_rate=float((pnl>0).mean()) if len(pnl) else None, average_win=float(wins.mean()) if len(wins) else None,
        average_loss=float(-losses.mean()) if len(losses) else None, total_trades=int(len(pnl)),
        average_holding_period=float(trades.holding_bars.mean()) if len(pnl) else None,
        exposure=exposure, exposure_definition="calendar-time-weighted gross notional/equity between event timestamps",
        time_in_market=time_in_market,max_concentration_hhi=float(equity_curve.concentration_hhi.max()) if "concentration_hhi" in equity_curve else None,
        return_units="fractions", expectancy_units="account_currency", holding_period_units="instrument_bars",
        ratio_note="null means undefined or insufficient sample; CAGR on short samples is unstable")

