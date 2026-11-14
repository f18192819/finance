from dataclasses import asdict
from datetime import date
import io
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from ..config import InstrumentRegistry,load_config
from ..data.provider import EfinanceProvider
from ..data.validation import import_csv
from ..manual_trading import TradingJournal,trade_plan
from ..reports import candle_chart,equity_chart,sensitivity_heatmap,trade_breakdown
from ..research.experiments import ExperimentManager
from ..research.robustness import sensitivity,ablation,walk_forward,monte_carlo,correlation_analysis
from ..risk import RiskConfig
from ..service import run_experiment
from ..strategies import STRATEGIES,make_strategy

NAMES = {"trend_following":"趋势延续", "breakout":"收缩突破", "liquidity_reversal":"流动性反转"}


def main():
    st.set_page_config(page_title="Meridian · Quant Research",page_icon="◈",layout="wide")
    st.markdown('''<style>.block-container{padding-top:2rem;max-width:1500px}h1{font-weight:650;letter-spacing:-1.5px}h3{letter-spacing:-.4px}[data-testid="stMetric"]{background:#151e2e;border:1px solid #253249;border-radius:10px;padding:18px}section[data-testid="stSidebar"]{border-right:1px solid #253249}.eyebrow{font-size:11px;letter-spacing:3px;color:#51ddba}.quiet{color:#8c9db6;font-size:14px}.hero{padding:8px 0 24px;border-bottom:1px solid #253249;margin-bottom:24px}.pill{display:inline-block;border:1px solid #365447;border-radius:20px;color:#51ddba;font-size:11px;padding:4px 10px;margin-top:10px}</style>''',unsafe_allow_html=True)
    registry,manager = InstrumentRegistry(),ExperimentManager()
    st.session_state.setdefault("datasets",{})
    st.session_state.setdefault("results",{})
    st.session_state.setdefault("params",{})
    with st.sidebar:
        st.markdown("### ◈ MERIDIAN")
        st.caption("MULTI-MARKET QUANT RESEARCH")
        st.divider()
        page = st.radio("工作空间",["研究总览","数据中心","市场扫描","策略实验室","历史回测","组合分析","交易记录与计划","系统设置"],label_visibility="collapsed")
        st.divider()
        st.markdown("**efinance** · 唯一在线行情源")
        st.caption("收盘确认 → 下一根执行\n\n人工交易模式 · 无实盘下单接口")
        st.caption("本地项目 · v0.1.0")
    st.markdown(f'<div class="hero"><div class="eyebrow">RESEARCH / {page}</div><h1>{page}</h1><div class="quiet">从可解释的市场结构，到可复现的交易研究。</div><span class="pill">MANUAL TRADING ONLY</span></div>',unsafe_allow_html=True)
    try:
        if page=="研究总览": overview(manager)
        elif page=="数据中心": data_center(registry)
        elif page=="市场扫描": scanner(registry)
        elif page=="策略实验室": strategy_lab(registry,manager)
        elif page=="历史回测": backtests(registry,manager)
        elif page=="组合分析": portfolio(registry,manager)
        elif page=="交易记录与计划": trading(registry,manager)
        else: settings()
    except Exception as exc:
        st.error(f"操作未完成：{exc}")
        with st.expander("错误详情"):
            st.exception(exc)


def overview(manager):
    records = manager.list()
    coverage = EfinanceProvider().get_supported_markets()
    a,b,c,d = st.columns(4)
    a.metric("已加载资产",len(st.session_state.datasets))
    b.metric("研究实验",len(records))
    c.metric("独立策略",3)
    d.metric("验证通过的数据样本",sum(r["status"]=="SUPPORTED" for r in coverage))
    st.write("")
    left,right = st.columns([1.6,1])
    with left:
        st.subheader("研究路径")
        st.markdown("1. **验证数据** — 检查真实覆盖、时区、复权和完整 K 线。\n2. **独立回测** — 比较三套策略及其成本、回撤与交易数量。\n3. **样本外验证** — 用 Walk Forward、参数敏感性和消融检验规则。\n4. **人工决策** — 查看信号原因、风险预算与交易计划。")
        if records.empty:
            st.info("暂无回测结果。请先在「数据中心」下载真实行情或导入来源明确的 CSV。")
        else:
            st.dataframe(records.drop(columns="metrics").head(8),use_container_width=True,hide_index=True)
    with right:
        st.subheader("数据能力状态")
        if coverage:
            st.dataframe(pd.DataFrame(coverage)[["market","timeframe","status"]],use_container_width=True,hide_index=True,height=300)
        else:
            st.warning("尚未检测数据源能力。首次初始化请执行下方检测。")
        if st.button("初始化 / 重新检测能力",use_container_width=True):
            with st.spinner("实测 efinance 样本；每个请求设有超时……"):
                EfinanceProvider(timeout=18,retries=0).probe()
            st.rerun()
    st.caption("策略参考 LuxAlgo Price Action Concepts 的公开概念，使用本项目独立规则实现。分数是规则评分，不是盈利概率。")


def data_center(registry):
    symbols = [i.symbol for i in registry.all()]
    cols = st.columns([2,1,1,1])
    symbol = cols[0].selectbox("资产",symbols,format_func=lambda s:f"{s} · {registry.get(s).name}")
    tf = cols[1].selectbox("周期",["1D","1H","4H","1W","1M"])
    start = cols[2].date_input("开始",date(2021,1,1))
    end = cols[3].date_input("结束",date(2025,12,31))
    ins = registry.get(symbol)
    st.caption(f"{ins.market} · {ins.currency} · {ins.timezone} · 最小数量 {ins.lot_size:g} · T+{ins.settlement_days}")
    online,offline = st.tabs(["efinance 在线行情","离线 CSV"])
    with online:
        adjustment = st.selectbox("价格方式",["none","forward","backward"],format_func=lambda x:{"none":"不复权 · 可用于成交模拟","forward":"前复权 · 仅指标研究","backward":"后复权 · 仅指标研究"}[x])
        refresh = st.checkbox("刷新 / 增量更新缓存")
        if st.button("获取并校验行情",type="primary"):
            with st.spinner("获取、校验并保存数据快照……"):
                ds = EfinanceProvider().get_historical_data(symbol,str(start),str(end),tf,adjustment,refresh)
                st.session_state.datasets[symbol] = ds
            st.success(f"已加载 {len(ds.bars)} 根真实 K 线")
    with offline:
        st.caption("字段：timestamp, open, high, low, close, volume, amount。timestamp 为交易所当地收盘时刻；日线可使用日期。4H/周/月还需显式 open_time。")
        source = st.text_input("来源名称",placeholder="例如：用户导出的券商历史行情")
        file = st.file_uploader("CSV 文件",type=["csv"])
        if st.button("导入并验证 CSV",disabled=file is None):
            ds = import_csv(io.BytesIO(file.getvalue()),ins,tf,source)
            st.session_state.datasets[symbol] = ds
            st.success(f"已导入 {len(ds.bars)} 根 K 线，来源：{ds.metadata['source']}")
    if symbol in st.session_state.datasets:
        ds = st.session_state.datasets[symbol]
        st.plotly_chart(candle_chart(ds.bars),use_container_width=True)
        st.dataframe(ds.bars.tail(12),hide_index=True,use_container_width=True)
        with st.expander("来源与数据质量记录"):
            st.json(ds.metadata)


def need_data():
    if not st.session_state.datasets:
        st.info("请先在「数据中心」加载并校验数据。")
        return False
    return True


def scanner(registry):
    if not need_data(): return
    strategy_name = st.selectbox("扫描策略",list(STRATEGIES),format_func=NAMES.get)
    if st.button("扫描已加载资产",type="primary"):
        rows = []
        for symbol,ds in st.session_state.datasets.items():
            strategy = make_strategy(strategy_name,st.session_state.params)
            signals = strategy.generate_signals(ds.bars)
            last = strategy.features.iloc[-1]
            latest = signals[-1] if signals else None
            rows.append(dict(symbol=symbol,as_of=last.timestamp,regime=last.regime,confidence=last.regime_confidence,
                signal_time=latest.timestamp if latest else None,direction=latest.direction if latest else None,
                score=latest.score if latest else None,is_current_bar=bool(latest and latest.timestamp==last.timestamp),
                reasons="; ".join(latest.reasons) if latest else "无完整规则链信号"))
        st.session_state.scan = pd.DataFrame(rows)
    if "scan" in st.session_state:
        st.dataframe(st.session_state.scan,use_container_width=True,hide_index=True)
        st.caption("历史最新信号不等于当前可执行信号。is_current_bar 只表示与数据末根一致，不保证行情实时。")


def strategy_lab(registry,manager):
    st.markdown("**趋势延续**：趋势 → BOS → OB/FVG 回踩 → 收盘确认。  \n**收缩突破**：波动收缩 → 放量收盘突破 → 后续回踩。  \n**流动性反转**：扫前高/前低 → 收复 → CHoCH → OB 回踩确认。")
    name = st.selectbox("策略",list(STRATEGIES),format_func=NAMES.get)
    initial = dict(load_config("strategies")["defaults"],**st.session_state.params)
    text = st.text_area("可复现实验参数（JSON）",json.dumps(initial,ensure_ascii=False,indent=2),height=280)
    if st.button("校验并保存参数"):
        params = json.loads(text)
        make_strategy(name,params)
        st.session_state.params = params
        st.success("参数已通过校验")
    st.caption("默认 single_timeframe 是明确命名的单周期研究变体。严格 1D/4H/1H 联合模式通过 CLI/Python API 提供真实多周期输入，缺失时拒绝执行。")
    if not need_data(): return
    symbol = st.selectbox("研究资产",list(st.session_state.datasets))
    ds,ins = st.session_state.datasets[symbol],registry.get(symbol)
    tab1,tab2,tab3 = st.tabs(["参数敏感性","评分消融","Walk Forward"])
    with tab1:
        grid_text = st.text_input("参数网格 JSON",'{"target_r": [2.5, 3.0], "stop_atr_buffer": [0.1, 0.3]}')
        if st.button("运行参数实验"):
            grid = json.loads(grid_text)
            with st.spinner("运行并逐个保存实验……"):
                table = sensitivity(ds,ins,name,grid,st.session_state.params,manager=manager)
            st.dataframe(table,use_container_width=True)
            if len(grid)>=2:
                x,y = list(grid)[:2]
                st.plotly_chart(sensitivity_heatmap(table,x,y),use_container_width=True)
    with tab2:
        st.caption("逐个移除评分因素并重新归一化权重；策略结构条件保持其明确定义。")
        if st.button("运行评分消融"):
            with st.spinner("运行六组消融实验……"):
                st.dataframe(ablation(ds,ins,name,st.session_state.params,manager=manager),use_container_width=True)
    with tab3:
        folds_text = st.text_area("训练 / 测试区间 JSON",'[["2021-01-01", "2023-12-31", "2024-01-01", "2024-12-31"], ["2022-01-01", "2024-12-31", "2025-01-01", "2025-12-31"]]')
        if st.button("运行滚动样本外测试"):
            with st.spinner("仅在训练期选择参数；测试期不参与调参……"):
                table = walk_forward(ds,ins,name,json.loads(grid_text),json.loads(folds_text),st.session_state.params,manager=manager)
            st.dataframe(table,use_container_width=True)


def show_result(result,eid,manager):
    m = result.metrics
    cols = st.columns(4)
    cols[0].metric("净收益",f"{m['total_return']:.2%}")
    cols[1].metric("最大回撤",f"{m['max_drawdown']:.2%}")
    cols[2].metric("已完成交易",m["total_trades"])
    cols[3].metric("Profit Factor","—" if m["profit_factor"] is None else f"{m['profit_factor']:.2f}")
    st.plotly_chart(equity_chart(result.equity_curve),use_container_width=True)
    tabs = st.tabs(["交易明细","执行与风险","全部指标","Monte Carlo"])
    with tabs[0]:
        st.dataframe(result.trades,use_container_width=True,hide_index=True)
        for key,table in trade_breakdown(result.trades).items():
            with st.expander(f"按 {key} 分析"):
                st.dataframe(table,use_container_width=True)
    with tabs[1]:
        st.dataframe(result.fills,use_container_width=True,hide_index=True)
        st.dataframe(result.risk_events,use_container_width=True,hide_index=True)
        st.json(result.config)
    with tabs[2]: st.json(m)
    with tabs[3]:
        method = st.selectbox("抽样方法",["bootstrap","permutation"],key=f"mc_{eid}")
        if st.button("计算 Monte Carlo",key=f"run_mc_{eid}"):
            summary,paths,dist = monte_carlo(result.trades,result.config["risk"]["initial_equity"],method=method)
            st.json(summary)
            st.line_chart(paths.iloc[:,:30])
            st.bar_chart(dist.max_drawdown.value_counts(bins=20,sort=False).rename_axis("drawdown").reset_index(name="count").assign(drawdown=lambda x:x.drawdown.astype(str)).set_index("drawdown"))
    st.caption(f"实验 ID：{eid}")
    report = manager.root/eid/"report.html"
    if report.exists():
        st.download_button("下载完整 HTML 报告",report.read_bytes(),file_name=f"{eid}.html",mime="text/html")


def backtests(registry,manager):
    if not need_data(): return
    a,b,c = st.columns([2,2,1])
    symbol = a.selectbox("资产",list(st.session_state.datasets))
    names = b.multiselect("独立回测策略",list(STRATEGIES),default=["trend_following"],format_func=NAMES.get)
    initial = c.number_input("初始权益",min_value=1000.,value=1000000.,step=10000.)
    if st.button("运行并保存回测",type="primary",disabled=not names):
        for name in names:
            with st.spinner(f"运行 {NAMES[name]}……"):
                result,eid = run_experiment({symbol:st.session_state.datasets[symbol]},{symbol:registry.get(symbol)},
                    [make_strategy(name,st.session_state.params)],RiskConfig.defaults(initial_equity=initial),manager=manager)
                st.session_state.results[name] = (result,eid)
    if st.session_state.results:
        name = st.selectbox("查看独立策略结果",list(st.session_state.results),format_func=NAMES.get)
        result,eid = st.session_state.results[name]
        show_result(result,eid,manager)


def portfolio(registry,manager):
    if not need_data(): return
    symbols = st.multiselect("组合资产（必须同币种）",list(st.session_state.datasets),default=list(st.session_state.datasets))
    names = st.multiselect("组合策略",list(STRATEGIES),default=["trend_following"],format_func=NAMES.get)
    if st.button("分析相关性",disabled=len(symbols)<2):
        report = correlation_analysis({s:st.session_state.datasets[s] for s in symbols},{s:registry.get(s) for s in symbols})
        for key in ("assets","groups","sectors"):
            st.write(key)
            st.dataframe(report[key],use_container_width=True)
        st.caption(report["note"])
    if st.button("运行共享资金组合回测",type="primary",disabled=not symbols or not names):
        result,eid = run_experiment({s:st.session_state.datasets[s] for s in symbols},{s:registry.get(s) for s in symbols},
            [make_strategy(name,st.session_state.params) for name in names],manager=manager,label="portfolio")
        st.session_state.portfolio_result = (result,eid)
    if "portfolio_result" in st.session_state:
        result,eid = st.session_state.portfolio_result
        show_result(result,eid,manager)


def trading(registry,manager):
    if need_data():
        symbol = st.selectbox("交易计划资产",list(st.session_state.datasets))
        name = st.selectbox("信号策略",list(STRATEGIES),format_func=NAMES.get)
        if st.button("生成最新历史信号计划"):
            signals = make_strategy(name,st.session_state.params).generate_signals(st.session_state.datasets[symbol].bars)
            if signals:
                st.session_state.plan = trade_plan(signals[-1],registry.get(symbol),RiskConfig.defaults().initial_equity)
            else:
                st.info("没有满足完整规则链的信号。")
        if "plan" in st.session_state:
            st.json(st.session_state.plan)
            status = st.selectbox("人工记录状态",["WATCHING","ACCEPTED_MANUALLY","REJECTED","CLOSED_MANUALLY"])
            notes = st.text_area("交易日志")
            if st.button("保存日志（不下单）"):
                TradingJournal().add(st.session_state.plan,status,notes)
                st.success("日志已保存")
    st.subheader("人工交易日志")
    st.dataframe(TradingJournal().list(),use_container_width=True,hide_index=True)
    st.subheader("历史实验比较")
    records = manager.list()
    ids = st.multiselect("选择实验",records.id.tolist())
    if ids:
        st.dataframe(manager.compare(ids),use_container_width=True)
        if st.button("标记首个选中实验为重点研究"):
            manager.mark_best(ids[0])
        if st.button("复制并复现实验"):
            result,eid = manager.reproduce(ids[0])
            st.success(f"复现已保存：{eid}")


def settings():
    st.markdown("交易规则、成本和风险阈值保存在项目 `config/` 中。成本数值是明确的研究假设；未建模项会进入每份报告。")
    for name in ("settings","risk","markets","instruments"):
        with st.expander(name,expanded=name=="risk"):
            st.json(load_config(name))
    st.markdown("策略参考：[市场结构](https://docs.luxalgo.com/platform/algos/price-action-concepts/market-structures) · [订单块](https://docs.luxalgo.com/platform/algos/price-action-concepts/order-blocks) · [FVG](https://docs.luxalgo.com/platform/algos/price-action-concepts/imbalances)")
