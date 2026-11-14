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

NAMES = {"trend_following":"瓒嬪娍寤剁画", "breakout":"鏀剁缉绐佺牬", "liquidity_reversal":"娴佸姩鎬у弽杞?}


def main():
    st.set_page_config(page_title="Meridian 路 Quant Research",page_icon="鈼?,layout="wide")
    st.markdown('''<style>.block-container{padding-top:2rem;max-width:1500px}h1{font-weight:650;letter-spacing:-1.5px}h3{letter-spacing:-.4px}[data-testid="stMetric"]{background:#151e2e;border:1px solid #253249;border-radius:10px;padding:18px}section[data-testid="stSidebar"]{border-right:1px solid #253249}.eyebrow{font-size:11px;letter-spacing:3px;color:#51ddba}.quiet{color:#8c9db6;font-size:14px}.hero{padding:8px 0 24px;border-bottom:1px solid #253249;margin-bottom:24px}.pill{display:inline-block;border:1px solid #365447;border-radius:20px;color:#51ddba;font-size:11px;padding:4px 10px;margin-top:10px}</style>''',unsafe_allow_html=True)
    registry,manager = InstrumentRegistry(),ExperimentManager()
    st.session_state.setdefault("datasets",{})
    st.session_state.setdefault("results",{})
    st.session_state.setdefault("params",{})
    with st.sidebar:
        st.markdown("### 鈼?MERIDIAN")
        st.caption("MULTI-MARKET QUANT RESEARCH")
        st.divider()
        page = st.radio("宸ヤ綔绌洪棿",["鐮旂┒鎬昏","鏁版嵁涓績","甯傚満鎵弿","绛栫暐瀹為獙瀹?,"鍘嗗彶鍥炴祴","缁勫悎鍒嗘瀽","浜ゆ槗璁板綍涓庤鍒?,"绯荤粺璁剧疆"],label_visibility="collapsed")
        st.divider()
        st.markdown("**efinance** 路 鍞竴鍦ㄧ嚎琛屾儏婧?)
        st.caption("鏀剁洏纭 鈫?涓嬩竴鏍规墽琛孿n\n浜哄伐浜ゆ槗妯″紡 路 鏃犲疄鐩樹笅鍗曟帴鍙?)
        st.caption("鏈湴椤圭洰 路 v0.1.0")
    st.markdown(f'<div class="hero"><div class="eyebrow">RESEARCH / {page}</div><h1>{page}</h1><div class="quiet">浠庡彲瑙ｉ噴鐨勫競鍦虹粨鏋勶紝鍒板彲澶嶇幇鐨勪氦鏄撶爺绌躲€?/div><span class="pill">MANUAL TRADING ONLY</span></div>',unsafe_allow_html=True)
    try:
        if page=="鐮旂┒鎬昏": overview(manager)
        elif page=="鏁版嵁涓績": data_center(registry)
        elif page=="甯傚満鎵弿": scanner(registry)
        elif page=="绛栫暐瀹為獙瀹?: strategy_lab(registry,manager)
        elif page=="鍘嗗彶鍥炴祴": backtests(registry,manager)
        elif page=="缁勫悎鍒嗘瀽": portfolio(registry,manager)
        elif page=="浜ゆ槗璁板綍涓庤鍒?: trading(registry,manager)
        else: settings()
    except Exception as exc:
        st.error(f"鎿嶄綔鏈畬鎴愶細{exc}")
        with st.expander("閿欒璇︽儏"):
            st.exception(exc)


def overview(manager):
    records = manager.list()
    coverage = EfinanceProvider().get_supported_markets()
    a,b,c,d = st.columns(4)
    a.metric("宸插姞杞借祫浜?,len(st.session_state.datasets))
    b.metric("鐮旂┒瀹為獙",len(records))
    c.metric("鐙珛绛栫暐",3)
    d.metric("楠岃瘉閫氳繃鐨勬暟鎹牱鏈?,sum(r["status"]=="SUPPORTED" for r in coverage))
    st.write("")
    left,right = st.columns([1.6,1])
    with left:
        st.subheader("鐮旂┒璺緞")
        st.markdown("1. **楠岃瘉鏁版嵁** 鈥?妫€鏌ョ湡瀹炶鐩栥€佹椂鍖恒€佸鏉冨拰瀹屾暣 K 绾裤€俓n2. **鐙珛鍥炴祴** 鈥?姣旇緝涓夊绛栫暐鍙婂叾鎴愭湰銆佸洖鎾や笌浜ゆ槗鏁伴噺銆俓n3. **鏍锋湰澶栭獙璇?* 鈥?鐢?Walk Forward銆佸弬鏁版晱鎰熸€у拰娑堣瀺妫€楠岃鍒欍€俓n4. **浜哄伐鍐崇瓥** 鈥?鏌ョ湅淇″彿鍘熷洜銆侀闄╅绠椾笌浜ゆ槗璁″垝銆?)
        if records.empty:
            st.info("鏆傛棤鍥炴祴缁撴灉銆傝鍏堝湪銆屾暟鎹腑蹇冦€嶄笅杞界湡瀹炶鎯呮垨瀵煎叆鏉ユ簮鏄庣‘鐨?CSV銆?)
        else:
            st.dataframe(records.drop(columns="metrics").head(8),use_container_width=True,hide_index=True)
    with right:
        st.subheader("鏁版嵁鑳藉姏鐘舵€?)
        if coverage:
            st.dataframe(pd.DataFrame(coverage)[["market","timeframe","status"]],use_container_width=True,hide_index=True,height=300)
        else:
            st.warning("灏氭湭妫€娴嬫暟鎹簮鑳藉姏銆傞娆″垵濮嬪寲璇锋墽琛屼笅鏂规娴嬨€?)
        if st.button("鍒濆鍖?/ 閲嶆柊妫€娴嬭兘鍔?,use_container_width=True):
            with st.spinner("瀹炴祴 efinance 鏍锋湰锛涙瘡涓姹傝鏈夎秴鏃垛€︹€?):
                EfinanceProvider(timeout=18,retries=0).probe()
            st.rerun()
    st.caption("绛栫暐鍙傝€?LuxAlgo Price Action Concepts 鐨勫叕寮€姒傚康锛屼娇鐢ㄦ湰椤圭洰鐙珛瑙勫垯瀹炵幇銆傚垎鏁版槸瑙勫垯璇勫垎锛屼笉鏄泩鍒╂鐜囥€?)


def data_center(registry):
    symbols = [i.symbol for i in registry.all()]
    cols = st.columns([2,1,1,1])
    symbol = cols[0].selectbox("璧勪骇",symbols,format_func=lambda s:f"{s} 路 {registry.get(s).name}")
    tf = cols[1].selectbox("鍛ㄦ湡",["1D","1H","4H","1W","1M"])
    start = cols[2].date_input("寮€濮?,date(2021,1,1))
    end = cols[3].date_input("缁撴潫",date(2025,12,31))
    ins = registry.get(symbol)
    st.caption(f"{ins.market} 路 {ins.currency} 路 {ins.timezone} 路 鏈€灏忔暟閲?{ins.lot_size:g} 路 T+{ins.settlement_days}")
    online,offline = st.tabs(["efinance 鍦ㄧ嚎琛屾儏","绂荤嚎 CSV"])
    with online:
        adjustment = st.selectbox("浠锋牸鏂瑰紡",["none","forward","backward"],format_func=lambda x:{"none":"涓嶅鏉?路 鍙敤浜庢垚浜ゆā鎷?,"forward":"鍓嶅鏉?路 浠呮寚鏍囩爺绌?,"backward":"鍚庡鏉?路 浠呮寚鏍囩爺绌?}[x])
        refresh = st.checkbox("鍒锋柊 / 澧為噺鏇存柊缂撳瓨")
        if st.button("鑾峰彇骞舵牎楠岃鎯?,type="primary"):
            with st.spinner("鑾峰彇銆佹牎楠屽苟淇濆瓨鏁版嵁蹇収鈥︹€?):
                ds = EfinanceProvider().get_historical_data(symbol,str(start),str(end),tf,adjustment,refresh)
                st.session_state.datasets[symbol] = ds
            st.success(f"宸插姞杞?{len(ds.bars)} 鏍圭湡瀹?K 绾?)
    with offline:
        st.caption("瀛楁锛歵imestamp, open, high, low, close, volume, amount銆倀imestamp 涓轰氦鏄撴墍褰撳湴鏀剁洏鏃跺埢锛涙棩绾垮彲浣跨敤鏃ユ湡銆?H/鍛?鏈堣繕闇€鏄惧紡 open_time銆?)
        source = st.text_input("鏉ユ簮鍚嶇О",placeholder="渚嬪锛氱敤鎴峰鍑虹殑鍒稿晢鍘嗗彶琛屾儏")
        file = st.file_uploader("CSV 鏂囦欢",type=["csv"])
        if st.button("瀵煎叆骞堕獙璇?CSV",disabled=file is None):
            ds = import_csv(io.BytesIO(file.getvalue()),ins,tf,source)
            st.session_state.datasets[symbol] = ds
            st.success(f"宸插鍏?{len(ds.bars)} 鏍?K 绾匡紝鏉ユ簮锛歿ds.metadata['source']}")
    if symbol in st.session_state.datasets:
        ds = st.session_state.datasets[symbol]
        st.plotly_chart(candle_chart(ds.bars),use_container_width=True)
        st.dataframe(ds.bars.tail(12),hide_index=True,use_container_width=True)
        with st.expander("鏉ユ簮涓庢暟鎹川閲忚褰?):
            st.json(ds.metadata)


def need_data():
    if not st.session_state.datasets:
        st.info("璇峰厛鍦ㄣ€屾暟鎹腑蹇冦€嶅姞杞藉苟鏍￠獙鏁版嵁銆?)
        return False
    return True


def scanner(registry):
    if not need_data(): return
    strategy_name = st.selectbox("鎵弿绛栫暐",list(STRATEGIES),format_func=NAMES.get)
    if st.button("鎵弿宸插姞杞借祫浜?,type="primary"):
        rows = []
        for symbol,ds in st.session_state.datasets.items():
            strategy = make_strategy(strategy_name,st.session_state.params)
            signals = strategy.generate_signals(ds.bars)
            last = strategy.features.iloc[-1]
            latest = signals[-1] if signals else None
            rows.append(dict(symbol=symbol,as_of=last.timestamp,regime=last.regime,confidence=last.regime_confidence,
                signal_time=latest.timestamp if latest else None,direction=latest.direction if latest else None,
                score=latest.score if latest else None,is_current_bar=bool(latest and latest.timestamp==last.timestamp),
                reasons="; ".join(latest.reasons) if latest else "鏃犲畬鏁磋鍒欓摼淇″彿"))
        st.session_state.scan = pd.DataFrame(rows)
    if "scan" in st.session_state:
        st.dataframe(st.session_state.scan,use_container_width=True,hide_index=True)
        st.caption("鍘嗗彶鏈€鏂颁俊鍙蜂笉绛変簬褰撳墠鍙墽琛屼俊鍙枫€俰s_current_bar 鍙〃绀轰笌鏁版嵁鏈牴涓€鑷达紝涓嶄繚璇佽鎯呭疄鏃躲€?)


def strategy_lab(registry,manager):
    st.markdown("**瓒嬪娍寤剁画**锛氳秼鍔?鈫?BOS 鈫?OB/FVG 鍥炶俯 鈫?鏀剁洏纭銆? \n**鏀剁缉绐佺牬**锛氭尝鍔ㄦ敹缂?鈫?鏀鹃噺鏀剁洏绐佺牬 鈫?鍚庣画鍥炶俯銆? \n**娴佸姩鎬у弽杞?*锛氭壂鍓嶉珮/鍓嶄綆 鈫?鏀跺 鈫?CHoCH 鈫?OB 鍥炶俯纭銆?)
    name = st.selectbox("绛栫暐",list(STRATEGIES),format_func=NAMES.get)
    initial = dict(load_config("strategies")["defaults"],**st.session_state.params)
    text = st.text_area("鍙鐜板疄楠屽弬鏁帮紙JSON锛?,json.dumps(initial,ensure_ascii=False,indent=2),height=280)
    if st.button("鏍￠獙骞朵繚瀛樺弬鏁?):
        params = json.loads(text)
        make_strategy(name,params)
        st.session_state.params = params
        st.success("鍙傛暟宸查€氳繃鏍￠獙")
    st.caption("榛樿 single_timeframe 鏄槑纭懡鍚嶇殑鍗曞懆鏈熺爺绌跺彉浣撱€備弗鏍?1D/4H/1H 鑱斿悎妯″紡閫氳繃 CLI/Python API 鎻愪緵鐪熷疄澶氬懆鏈熻緭鍏ワ紝缂哄け鏃舵嫆缁濇墽琛屻€?)
    if not need_data(): return
    symbol = st.selectbox("鐮旂┒璧勪骇",list(st.session_state.datasets))
    ds,ins = st.session_state.datasets[symbol],registry.get(symbol)
    tab1,tab2,tab3 = st.tabs(["鍙傛暟鏁忔劅鎬?,"璇勫垎娑堣瀺","Walk Forward"])
    with tab1:
        grid_text = st.text_input("鍙傛暟缃戞牸 JSON",'{"target_r": [2.5, 3.0], "stop_atr_buffer": [0.1, 0.3]}')
        if st.button("杩愯鍙傛暟瀹為獙"):
            grid = json.loads(grid_text)
            with st.spinner("杩愯骞堕€愪釜淇濆瓨瀹為獙鈥︹€?):
                table = sensitivity(ds,ins,name,grid,st.session_state.params,manager=manager)
            st.dataframe(table,use_container_width=True)
            if len(grid)>=2:
                x,y = list(grid)[:2]
                st.plotly_chart(sensitivity_heatmap(table,x,y),use_container_width=True)
    with tab2:
        st.caption("閫愪釜绉婚櫎璇勫垎鍥犵礌骞堕噸鏂板綊涓€鍖栨潈閲嶏紱绛栫暐缁撴瀯鏉′欢淇濇寔鍏舵槑纭畾涔夈€?)
        if st.button("杩愯璇勫垎娑堣瀺"):
            with st.spinner("杩愯鍏粍娑堣瀺瀹為獙鈥︹€?):
                st.dataframe(ablation(ds,ins,name,st.session_state.params,manager=manager),use_container_width=True)
    with tab3:
        folds_text = st.text_area("璁粌 / 娴嬭瘯鍖洪棿 JSON",'[["2021-01-01", "2023-12-31", "2024-01-01", "2024-12-31"], ["2022-01-01", "2024-12-31", "2025-01-01", "2025-12-31"]]')
        if st.button("杩愯婊氬姩鏍锋湰澶栨祴璇?):
            with st.spinner("浠呭湪璁粌鏈熼€夋嫨鍙傛暟锛涙祴璇曟湡涓嶅弬涓庤皟鍙傗€︹€?):
                table = walk_forward(ds,ins,name,json.loads(grid_text),json.loads(folds_text),st.session_state.params,manager=manager)
            st.dataframe(table,use_container_width=True)


def show_result(result,eid,manager):
    m = result.metrics
    cols = st.columns(4)
    cols[0].metric("鍑€鏀剁泭",f"{m['total_return']:.2%}")
    cols[1].metric("鏈€澶у洖鎾?,f"{m['max_drawdown']:.2%}")
    cols[2].metric("宸插畬鎴愪氦鏄?,m["total_trades"])
    cols[3].metric("Profit Factor","鈥? if m["profit_factor"] is None else f"{m['profit_factor']:.2f}")
    st.plotly_chart(equity_chart(result.equity_curve),use_container_width=True)
    tabs = st.tabs(["浜ゆ槗鏄庣粏","鎵ц涓庨闄?,"鍏ㄩ儴鎸囨爣","Monte Carlo"])
    with tabs[0]:
        st.dataframe(result.trades,use_container_width=True,hide_index=True)
        for key,table in trade_breakdown(result.trades).items():
            with st.expander(f"鎸?{key} 鍒嗘瀽"):
                st.dataframe(table,use_container_width=True)
    with tabs[1]:
        st.dataframe(result.fills,use_container_width=True,hide_index=True)
        st.dataframe(result.risk_events,use_container_width=True,hide_index=True)
        st.json(result.config)
    with tabs[2]: st.json(m)
    with tabs[3]:
        method = st.selectbox("鎶芥牱鏂规硶",["bootstrap","permutation"],key=f"mc_{eid}")
        if st.button("璁＄畻 Monte Carlo",key=f"run_mc_{eid}"):
            summary,paths,dist = monte_carlo(result.trades,result.config["risk"]["initial_equity"],method=method)
            st.json(summary)
            st.line_chart(paths.iloc[:,:30])
            st.bar_chart(dist.max_drawdown.value_counts(bins=20,sort=False).rename_axis("drawdown").reset_index(name="count").assign(drawdown=lambda x:x.drawdown.astype(str)).set_index("drawdown"))
    st.caption(f"瀹為獙 ID锛歿eid}")
    report = manager.root/eid/"report.html"
    if report.exists():
        st.download_button("涓嬭浇瀹屾暣 HTML 鎶ュ憡",report.read_bytes(),file_name=f"{eid}.html",mime="text/html")


def backtests(registry,manager):
    if not need_data(): return
    a,b,c = st.columns([2,2,1])
    symbol = a.selectbox("璧勪骇",list(st.session_state.datasets))
    names = b.multiselect("鐙珛鍥炴祴绛栫暐",list(STRATEGIES),default=["trend_following"],format_func=NAMES.get)
    initial = c.number_input("鍒濆鏉冪泭",min_value=1000.,value=1000000.,step=10000.)
    if st.button("杩愯骞朵繚瀛樺洖娴?,type="primary",disabled=not names):
        for name in names:
            with st.spinner(f"杩愯 {NAMES[name]}鈥︹€?):
                result,eid = run_experiment({symbol:st.session_state.datasets[symbol]},{symbol:registry.get(symbol)},
                    [make_strategy(name,st.session_state.params)],RiskConfig.defaults(initial_equity=initial),manager=manager)
                st.session_state.results[name] = (result,eid)
    if st.session_state.results:
        name = st.selectbox("鏌ョ湅鐙珛绛栫暐缁撴灉",list(st.session_state.results),format_func=NAMES.get)
        result,eid = st.session_state.results[name]
        show_result(result,eid,manager)


def portfolio(registry,manager):
    if not need_data(): return
    symbols = st.multiselect("缁勫悎璧勪骇锛堝繀椤诲悓甯佺锛?,list(st.session_state.datasets),default=list(st.session_state.datasets))
    names = st.multiselect("缁勫悎绛栫暐",list(STRATEGIES),default=["trend_following"],format_func=NAMES.get)
    if st.button("鍒嗘瀽鐩稿叧鎬?,disabled=len(symbols)<2):
        report = correlation_analysis({s:st.session_state.datasets[s] for s in symbols},{s:registry.get(s) for s in symbols})
        for key in ("assets","groups","sectors"):
            st.write(key)
            st.dataframe(report[key],use_container_width=True)
        st.caption(report["note"])
    if st.button("杩愯鍏变韩璧勯噾缁勫悎鍥炴祴",type="primary",disabled=not symbols or not names):
        result,eid = run_experiment({s:st.session_state.datasets[s] for s in symbols},{s:registry.get(s) for s in symbols},
            [make_strategy(name,st.session_state.params) for name in names],manager=manager,label="portfolio")
        st.session_state.portfolio_result = (result,eid)
    if "portfolio_result" in st.session_state:
        result,eid = st.session_state.portfolio_result
        show_result(result,eid,manager)


def trading(registry,manager):
    if need_data():
        symbol = st.selectbox("浜ゆ槗璁″垝璧勪骇",list(st.session_state.datasets))
        name = st.selectbox("淇″彿绛栫暐",list(STRATEGIES),format_func=NAMES.get)
        if st.button("鐢熸垚鏈€鏂板巻鍙蹭俊鍙疯鍒?):
            signals = make_strategy(name,st.session_state.params).generate_signals(st.session_state.datasets[symbol].bars)
            if signals:
                st.session_state.plan = trade_plan(signals[-1],registry.get(symbol),RiskConfig.defaults().initial_equity)
            else:
                st.info("娌℃湁婊¤冻瀹屾暣瑙勫垯閾剧殑淇″彿銆?)
        if "plan" in st.session_state:
            st.json(st.session_state.plan)
            status = st.selectbox("浜哄伐璁板綍鐘舵€?,["WATCHING","ACCEPTED_MANUALLY","REJECTED","CLOSED_MANUALLY"])
            notes = st.text_area("浜ゆ槗鏃ュ織")
            if st.button("淇濆瓨鏃ュ織锛堜笉涓嬪崟锛?):
                TradingJournal().add(st.session_state.plan,status,notes)
                st.success("鏃ュ織宸蹭繚瀛?)
    st.subheader("浜哄伐浜ゆ槗鏃ュ織")
    st.dataframe(TradingJournal().list(),use_container_width=True,hide_index=True)
    st.subheader("鍘嗗彶瀹為獙姣旇緝")
    records = manager.list()
    ids = st.multiselect("閫夋嫨瀹為獙",records.id.tolist())
    if ids:
        st.dataframe(manager.compare(ids),use_container_width=True)
        if st.button("鏍囪棣栦釜閫変腑瀹為獙涓洪噸鐐圭爺绌?):
            manager.mark_best(ids[0])
        if st.button("澶嶅埗骞跺鐜板疄楠?):
            result,eid = manager.reproduce(ids[0])
            st.success(f"澶嶇幇宸蹭繚瀛橈細{eid}")


def settings():
    st.markdown("浜ゆ槗瑙勫垯銆佹垚鏈拰椋庨櫓闃堝€间繚瀛樺湪椤圭洰 `config/` 涓€傛垚鏈暟鍊兼槸鏄庣‘鐨勭爺绌跺亣璁撅紱鏈缓妯￠」浼氳繘鍏ユ瘡浠芥姤鍛娿€?)
    for name in ("settings","risk","markets","instruments"):
        with st.expander(name,expanded=name=="risk"):
            st.json(load_config(name))
    st.markdown("绛栫暐鍙傝€冿細[甯傚満缁撴瀯](https://docs.luxalgo.com/platform/algos/price-action-concepts/market-structures) 路 [璁㈠崟鍧梋(https://docs.luxalgo.com/platform/algos/price-action-concepts/order-blocks) 路 [FVG](https://docs.luxalgo.com/platform/algos/price-action-concepts/imbalances)")

