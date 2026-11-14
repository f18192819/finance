from pathlib import Path
import html
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def equity_chart(curve):
    fig = go.Figure(go.Scatter(x=curve.timestamp,y=curve.equity,line=dict(color="#51ddba",width=2),fill="tozeroy",fillcolor="rgba(81,221,186,0.08)",name="Equity"))
    fig.update_layout(template="plotly_dark",title="Account equity · after costs",paper_bgcolor="#101826",plot_bgcolor="#101826",height=390,margin=dict(l=25,r=25,t=55,b=30))
    return fig


def candle_chart(bars,features=None):
    d = bars.tail(250)
    fig = go.Figure(go.Candlestick(x=d.timestamp,open=d.open,high=d.high,low=d.low,close=d.close,
        increasing_line_color="#51ddba",decreasing_line_color="#f27c91",name="OHLC"))
    if features is not None:
        f = features.tail(250)
        for col,color in [("ema_fast","#66aaff"),("ema_slow","#eebd6b")]:
            fig.add_trace(go.Scatter(x=f.timestamp,y=f[col],name=col,line=dict(color=color,width=1)))
        events = f.loc[f.structure_event!=""]
        fig.add_trace(go.Scatter(x=events.timestamp,y=events.close,mode="markers+text",text=events.structure_event,textposition="top center",name="Confirmed structure",marker=dict(color="#d8a0ff",size=6)))
    fig.update_layout(template="plotly_dark",paper_bgcolor="#101826",plot_bgcolor="#101826",xaxis_rangeslider_visible=False,height=470,margin=dict(l=15,r=15,t=25,b=20))
    return fig


def trade_breakdown(trades):
    if trades.empty:
        return {}
    d = trades.copy()
    d["year"] = pd.to_datetime(d.exit_time,utc=True).dt.year
    return {key:d.groupby(key).agg(trades=("pnl","count"),net_profit=("pnl","sum"),expectancy=("pnl","mean"),win_rate=("pnl",lambda x:(x>0).mean())) for key in ("strategy","symbol","regime","year")}


def sensitivity_heatmap(frame,x,y,metric="total_return"):
    matrix = frame.pivot_table(index=y,columns=x,values=metric,aggfunc="mean")
    return px.imshow(matrix,aspect="auto",color_continuous_scale="RdYlGn",title=f"{metric} · parameter sensitivity")


def export_report(result,folder,manifest):
    folder = Path(folder)
    metrics = pd.DataFrame([dict(metric=k,value=v) for k,v in result.metrics.items()]).to_html(index=False,escape=True)
    breakdown = "".join(f"<h2>{html.escape(k)}</h2>{v.to_html()}" for k,v in trade_breakdown(result.trades).items())
    # Embedded Plotly JS keeps report usable offline.
    chart = equity_chart(result.equity_curve).to_html(full_html=False,include_plotlyjs=True)
    report = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Quant Research · {html.escape(manifest['id'])}</title>
<style>body{{background:#0c111b;color:#e2eaf6;font:15px system-ui;max-width:1200px;margin:40px auto;padding:24px}}h1{{color:#51ddba}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:9px;border-bottom:1px solid #2a384d;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}.muted{{color:#98a9c0}}</style>
<h1>Multi-Market Quant Research</h1><p class="muted">Experiment {html.escape(manifest['id'])} · Research only · Manual execution</p>
<p>仅使用已记录来源的数据。零交易不代表正收益。收益为账户币种的价格收益，未建模项目见下方配置。</p>{chart}
<h2>Performance</h2>{metrics}{breakdown}<h2>Closed trades</h2>{result.trades.to_html(index=False,escape=True)}
<h2>Risk events</h2>{result.risk_events.to_html(index=False,escape=True)}<h2>Assumptions & reproducibility</h2>
<pre>{html.escape(json.dumps(manifest,ensure_ascii=False,indent=2,default=str))}</pre></html>'''
    (folder/"report.html").write_text(report,encoding="utf-8")
