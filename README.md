# Meridian 路 Multi-Market Quant Research System

鍩轰簬 **efinance** 鐨勬湰鍦?Swing Trading 鐮旂┒骞冲彴銆備笁濂楃嫭绔嬬瓥鐣ャ€侀€愭牴 K 绾夸笌缁勫悎鍥炴祴銆佹牱鏈鐮旂┒銆佸疄楠屽揩鐓у拰浜哄伐浜ゆ槗璁″垝銆傚彧杈呭姪浜哄伐浜ゆ槗锛屾病鏈夊疄鐩樹笅鍗曟帴鍙ｃ€?
## 鍚姩

鏈洰褰曞凡寤虹珛 `.venv` 骞跺畨瑁呴」鐩€侾owerShell锛?
```powershell
cd C:\data\Automatic\Windows\finance
.\start.ps1
```

鎵撳紑 **http://127.0.0.1:8501**銆備篃鍙洿鎺ヨ繍琛岋細

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

鏂扮幆澧冨畨瑁咃紙Python 3.11+锛屾湰娆￠獙璇?Python 3.12.7锛夛細

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe -m pytest
```

鏈鏈湴铏氭嫙鐜浣跨敤 `--system-site-packages` 澶嶇敤宸叉湁渚濊禆锛沗requirements.txt` 鍥哄畾浜嗗疄闄呴獙璇佺増鏈紝鏂版満鍣ㄥ彲鍒涘缓瀹屽叏闅旂鐜銆?
## 褰撳墠鏁版嵁楠岃瘉缁撴灉

2026-11-14 瀵瑰凡瀹夎 **efinance 0.5.5.2** 妫€鏌ュ疄闄呯鍚嶅苟鍙戣捣鐪熷疄璋冪敤銆傜綉椤垫枃妗ｆ樉绀?0.5.9锛屽洜姝ら€傞厤鍣ㄤ互鏈満婧愮爜鍜岀鍚嶄负鍑嗐€?
| 鎺ュ彛 | 鏈満瀹炴祴 | 鐢ㄩ€?/ 闄愬埗 |
|---|---|---|
| `stock.get_quote_history` | ERROR锛氱┖杩斿洖銆佽繛鎺ラ敊璇垨瓒呮椂 | 鍘嗗彶 K 绾垮皻鏈彇寰楁垚鍔熸牱鏈?|
| `stock.get_realtime_quotes(fs='ETF')` | 鎴愬姛锛?660 琛?| 浠呭疄鏃舵姤浠峰揩鐓э紝涓嶈兘鏇夸唬鍘嗗彶鍥炴祴 |
| `fund.get_quote_history('161725', pz=10)` | 鎴愬姛锛?0 琛?| 鍩洪噾鍑€鍊硷紝涓嶆槸 OHLCV锛岀姝吉閫犲紑楂樹綆鏀?|
| `futures.get_quote_history` | ERROR | 杩炵画鍚堢害鍙﹀绂佹鐩存帴鎵ц鍥炴祴 |
| `futures.get_realtime_quotes` | ERROR | 褰撳墠璇锋眰杩斿洖鏃犳晥鍝嶅簲 |
| `futures.get_futures_base_info` | ERROR | 褰撳墠璇锋眰杩斿洖鏃犳晥鍝嶅簲 |

瀹屾暣璇佹嵁鍦?[鎺ュ彛瀹¤](docs/efinance_api_audit.json) 鍜?[甯傚満鍛ㄦ湡鐭╅樀](docs/data_coverage.json)銆傝繍琛屾椂鏈€鏂扮煩闃靛湪 `data/metadata/coverage.json`銆俙SUPPORTED` 鍙剰鍛崇潃鎸囧畾鏍锋湰楠岃瘉鎴愬姛锛屼笉浠ｈ〃鏁翠釜甯傚満銆佸叏閮ㄦ棩鏈熷彲鐢ㄣ€?
**鍥犳鐩墠娌℃湁鐪熷疄鍘嗗彶琛屾儏鍥炴祴涓氱哗锛屼篃娌℃湁鈥滃凡楠岃瘉鐩堝埄鈥濈殑绛栫暐銆?* 鑷姩鍖栨祴璇曚娇鐢ㄦ槑纭爣璁扮殑浜哄伐娴嬭瘯澶瑰叿锛岄殧绂诲湪 `tests/` / 娴嬭瘯涓存椂鐩綍涓紱鐣岄潰涓嶅姞杞借櫄鏋勮鎯呫€傛暟鎹簮鎭㈠鍚庨噸鏂版娴嬫垨瀵煎叆鐪熷疄 CSV锛屽嵆鍙繍琛屽叏娴佺▼銆?
## 浣跨敤娴佺▼

1. **鏁版嵁涓績**锛氫笅杞戒笉澶嶆潈琛屾儏锛屾垨瀵煎叆甯︽潵婧愯鏄庣殑 CSV锛涙煡鐪嬪疄闄呭尯闂淬€佸畬鏁?K 绾裤€佹椂鍖哄拰寮傚父璁板綍銆?2. **绛栫暐瀹為獙瀹?*锛氱紪杈戝苟鏍￠獙 JSON 鍙傛暟銆備笁濂楄鍒欏垎鍒爺绌讹紝榛樿杩愯鏄庣‘鍛藉悕鐨?`single_timeframe` 鍙樹綋銆?3. **鍘嗗彶鍥炴祴**锛氶€夋嫨涓€濂楁垨澶氬绛栫暐锛屽垎鍒绠楁敹鐩娿€佸洖鎾ゃ€佹垚鏈€佷氦鏄撹褰曞強椋庨櫓鎷掑崟銆傛瘡娆¤繍琛岃嚜鍔ㄦ寔涔呭寲銆?4. **缁勫悎鍒嗘瀽**锛氬悓甯佺澶氳祫浜с€佸绛栫暐鍏变韩涓€浠借祫閲戣处鏈紱鏌ョ湅鐩稿叧鎬т笌闆嗕腑搴︺€傛贩鍚堝竵绉嶇洿鎺ユ嫆缁濄€?5. **绋冲仴鎬х爺绌?*锛氬弬鏁扮綉鏍笺€佷簩缁寸儹鍔涘浘銆佽瘎鍒嗗洜绱犳秷铻嶃€佹粴鍔ㄨ缁?/ 鏍锋湰澶栨祴璇曘€佸浐瀹氶殢鏈虹瀛愮殑 Monte Carlo銆?6. **浜ゆ槗璁板綍涓庤鍒?*锛氱敓鎴愭渶鏂板巻鍙蹭俊鍙风殑浜哄伐璁″垝锛岃褰曚汉宸ュ喅瀹氾紝姣旇緝瀹為獙銆佹爣璁伴噸鐐圭爺绌躲€佸鍒跺鐜般€?
鏈€鏂板巻鍙蹭俊鍙蜂笉淇濊瘉鏄綋鍓嶄俊鍙枫€備汉宸ヨ鍒掔殑鍙傝€冧粨浣嶅亣璁炬病鏈夊叾浠栨寔浠擄紝蹇呴』缁撳悎瀹為檯缁勫悎閲嶆柊纭銆?
## 鍛戒护琛?
```powershell
# 瀹炴祴甯傚満涓庡懆鏈熻鐩栵紱鍗曟璋冪敤鏈夎繘绋嬬骇纭秴鏃?.\.venv\Scripts\python.exe -m quant_research.cli probe --start 2025-01-01 --end 2025-12-31

# 棣栨涓嬭浇 / 缂撳瓨澶嶇敤锛?-refresh 璇锋眰鍒锋柊锛屼笉澶嶆潈妯″紡鍙閲忔洿鏂?.\.venv\Scripts\python.exe -m quant_research.cli download --symbol 510300 --start 2021-01-01 --end 2025-12-31

# 鐙珛绛栫暐鍥炴祴
.\.venv\Scripts\python.exe -m quant_research.cli backtest --symbol 510300 --strategy trend_following
.\.venv\Scripts\python.exe -m quant_research.cli backtest --symbol 510300 --strategy breakout
.\.venv\Scripts\python.exe -m quant_research.cli backtest --symbol 510300 --strategy liquidity_reversal

# 鐪熷疄绂荤嚎鏁版嵁锛堝繀椤绘彁渚涙潵婧愯鏄庯紱涓嶄細鏍囨垚 efinance锛?.\.venv\Scripts\python.exe -m quant_research.cli backtest --symbol 510300 --csv C:\path\real_history.csv --source broker_export --strategy breakout

# 鍙傛暟鏁忔劅鎬?/ Walk Forward / 娑堣瀺
.\.venv\Scripts\python.exe -m quant_research.cli sensitivity --symbol 510300 --strategy breakout --grid config/example_grid.json
.\.venv\Scripts\python.exe -m quant_research.cli walk-forward --symbol 510300 --strategy breakout --grid config/example_grid.json --folds config/example_folds.json
.\.venv\Scripts\python.exe -m quant_research.cli ablation --symbol 510300 --strategy breakout

.\.venv\Scripts\python.exe -m quant_research.cli experiments
.\.venv\Scripts\python.exe -m quant_research.cli reproduce EXPERIMENT_ID
.\.venv\Scripts\python.exe -m quant_research.cli monte-carlo EXPERIMENT_ID --method bootstrap --seed 42
```

鍛戒护澶辫触杩斿洖闈為浂閫€鍑虹爜锛屼笉闈欓粯鍒堕€犳垚鍔熺粨鏋溿€俙scripts/audit_efinance.py` 鍙噸鏂伴獙璇佸叚涓寚瀹氭帴鍙ｃ€?
## CSV 瑙勮寖涓庢椂闂磋涔?
鏈€浣庡瓧娈碉細`timestamp,open,high,low,close,volume,amount`銆俙symbol` 鐢卞凡閰嶇疆鐨勮祫浜х‘瀹氥€傜┖妯℃澘瑙?`docs/ohlcv_template.csv`銆?
- 鏃ョ嚎 `timestamp` 鍙负浜ゆ槗鏃ユ湡锛岀郴缁熸寜璧勪骇浜ゆ槗鎵€鏃跺尯鏄犲皠鍒板疄闄呮棩鐩樻敹鐩樻椂鍒伙紱淇濈暀鏄庣‘鐨?`open_time`銆?- 1H 鐨?`timestamp` 蹇呴』鏄敹鐩樻椂鍒伙紝鎸変氦鏄撴墍鏃舵楠岃瘉鏁村皬鏃?K 绾裤€備笉瓒?60 鍒嗛挓鐨勫熬娈垫槑纭帓闄わ紝涓嶆嫾鎺ャ€?- 绂荤嚎 4H/1W/1M 杩橀渶瑕?`open_time`锛屼袱涓椂闂村潎寤鸿浣跨敤甯︽椂鍖虹殑 ISO 8601銆?- 鍐呴儴缁熶竴涓?UTC銆傚睍绀?/ 鏃ュ巻鎸?`Instrument.timezone` 杞崲銆傛湭瀹屾垚 K 绾挎帓闄ゅ苟璁版暟銆?- 4H 鍙湪**鍚屼竴杩炵画浜ゆ槗鏃舵**鍐呯敱鍥涙牴杩炵画鏁村皬鏃?K 绾胯仛鍚堛€侫 鑲′笂鍗堛€佷笅鍗堝悇涓ゅ皬鏃讹紝榛樿涓嶈法鍗堜紤鎷兼帴锛屾墍浠ヨ瑙勫垯涓?A 鑲?4H 涓嶅彲鐢ㄣ€?- 鍛?/ 鏈堢敱鏃ョ嚎鑱氬悎锛屽湪璇ユ棩鍘嗗懆鏈熺粨鏉熷悗鎵嶅悜绛栫暐鍙戝竷锛屼繚瀹堥伩鍏嶆湭瀹屾垚鍛ㄦ湡娉勬紡銆備笉浼氭妸鏃ョ嚎鎻掑€兼垚灏忔椂绾裤€?- 鍋囨湡鏃ュ巻銆佸崐鏃ュ競涓庡鐩樹氦鏄撴棩鏄犲皠灏氭棤鍙潬浜ゆ槗鎵€鍘嗚〃锛涢厤缃笉鍖归厤鏃跺繀椤昏ˉ鍏呮椂娈垫垨绂佹璇ヨ祫浜х爺绌躲€傚垎閽熸繁搴︿緷鎹湡瀹炶繑鍥炶寖鍥达紝涓嶅亣璁惧骞村彲鐢ㄣ€?
## 绛栫暐瀹氫箟涓?LuxAlgo 鍙傝€?
鍙傝€?LuxAlgo 鐨勫叕寮€姒傚康锛?*鐙珛缂栧啓鍙鏌ョ殑瑙勫垯瀹炵幇**锛屼笉澹扮О澶嶅埢绉佹湁鎸囨爣銆佸弬鏁版垨鍘嗗彶涓氱哗銆傚師濮嬭祫鏂欙細

- [甯傚満缁撴瀯 / BOS / CHoCH / CHoCH+](https://docs.luxalgo.com/platform/algos/price-action-concepts/market-structures)
- [Order Blocks](https://docs.luxalgo.com/platform/algos/price-action-concepts/order-blocks)
- [Liquidity Concepts](https://docs.luxalgo.com/platform/algos/price-action-concepts/liquidity)
- [Imbalance / FVG](https://docs.luxalgo.com/platform/algos/price-action-concepts/imbalances)
- [efinance 瀹樻柟 API](https://efinance.readthedocs.io/en/latest/api.html) / [瀹樻柟婧愮爜](https://github.com/Micro-sheep/efinance)

鏈」鐩畾涔夛細鍙充晶 `pivot_right` 鏍规敹鐩樻墠纭鎽嗗姩鐐癸紱鍦ㄤ笅涓€鏍瑰紑濮嬩娇鐢ㄣ€傛柟鍚戦娆″缓绔嬭涓?CHoCH锛屽凡鏈夋柟鍚戜笂鐨勭粨鏋勭獊鐮磋涓?BOS銆侰HoCH+ 杩樿姹傚厛鍑虹幇 HL / LH 鐨勮“绔抗璞°€傚唴閮ㄧ粨鏋勪娇鐢ㄦ洿鐭獥鍙ｃ€傛墍鏈夋爣绛句繚瀛?`pivot_time` 鍜?`confirmation_time`锛涗笉鍦ㄥ師濮嬫瀬鍊兼椂鍒绘彁鍓嶄氦鏄撱€?
OB 涓虹‘璁ょ粨鏋勭獊鐮村墠鏈€杩戜竴鏍瑰弽鍚戣湣鐑涚殑楂樹綆鍖洪棿锛岀獊鐮存敹鐩樺悗鎵嶆垚绔嬶紱璁板綍纭銆佸洖韪╁拰鏀剁洏绌胯秺澶辨晥鏃堕棿銆侳VG 閲囩敤涓夋牴 K 绾块棿闅欙紝瀹屾暣鍥炶ˉ鍚庡け鏁堛€傛渶缁堝尯鍩熺敓鍛藉懆鏈熻〃鍙敤浜庡璁★紱绛栫暐浣跨敤閫愭椂鐐瑰揩鐓э紝涓嶈鏈潵鐨勫け鏁堟棩鏈熴€?
| 绛栫暐 | 蹇呴』渚濇鍙戠敓鐨勬潯浠?|
|---|---|
| 瓒嬪娍寤剁画 | EMA 瓒嬪娍涓€鑷?鈫?BOS 鈫?鍚庣画 OB/FVG 鍥炶俯 鈫?鏀剁洏绐佺牬鍓嶄竴鏍归珮 / 浣庣偣 |
| 鏀剁缉绐佺牬 | 鍓嶄竴鏍瑰凡澶勪簬 BB 瀹藉害鏀剁缉 鈫?鏀鹃噺鏀剁洏绐佺牬鍘嗗彶鍖洪棿 鈫?鍚庣画鍥炶俯鍖洪棿杈圭晫骞舵敹鐩樼‘璁?|
| 娴佸姩鎬у弽杞?| 鍒虹牬宸茬‘璁ゆ憜鍔ㄧ偣杈惧埌 ATR 鏈€灏忓箙搴︿笖鏀跺洖 鈫?鍚庣画 CHoCH 鈫?鍐嶅悗缁?OB 鍥炶俯骞舵敹鐩樼‘璁?|

榛樿姝㈢泩 TP1=1.5R銆乀P2=3R锛?0% 鍒嗘壒锛涘紩鎿庢寜瀹為檯浜ゆ槗鍗曚綅鍙栨暣锛屽苟閲嶆柊妫€鏌?*鎴愭湰鍚庣殑鍔犳潈鐩爣鏀剁泭 / 椋庨櫓**銆傛棩绾跨爺绌朵笉琚О浣?1D/4H/1H 瀹屾暣绛栫暐銆?
涓ユ牸澶氬懆鏈燂細鍙傛暟璁?`mode: multi_timeframe`锛岄€氳繃 CLI 浠?`--timeframe 1H` 杩愯鎴?Python API 鏄惧紡浼犲叆鐪熷疄 `1D`銆乣4H` 鏁版嵁鍜?`base_timeframe: 1H`銆傞珮鍛ㄦ湡鍙寜鏀剁洏鍙敤鏃堕棿 backward-asof 瀵归綈锛岀己澶辨垨闈炵湡瀹炴椂闀垮嵆鎷掔粷銆備笂涓嬫枃鏁版嵁涓€骞朵繚瀛橈紝鏀寔澶嶇幇銆傚鍛ㄦ湡绐佺牬浣跨敤宸插畬鎴?4H 瑙勫垯閾惧悗缁?1H 鏂瑰悜纭锛涘弽杞繕瑕佹眰宸插畬鎴?4H 缁撴瀯鏂瑰悜涓€鑷淬€?
## 鎴愪氦銆侀闄╀笌涓氱哗鍙ｅ緞

- 寮€鐩?/ 鏀剁洏浜嬩欢鎸夋椂闂存帓搴忋€傚悓涓€鏃跺埢鍏堝鐞嗕笂涓€鏍规敹鐩橈紝鍐嶅鐞嗕笅涓€鏍瑰紑鐩樸€傛棤淇″彿褰撴牴鏀剁洏鎴愪氦銆?- 甯備环鍗曞惈涓嶅埄婊戠偣銆佸崐浠峰樊銆佹渶灏忎环鏍煎崟浣嶅彇鏁达紱闄愪环鍗曚笉浼氳秺杩囬檺浠枫€傞檺浠蜂粎鐩樹腑瑙﹀強鏃讹紝鏁伴噺鎸夊紑鐩樹俊鎭鐣欙紝璁拌处鏃堕棿涓轰繚瀹堝紑鐩橀鐣欎唬鐞嗭紝鐪熷疄瑙﹀彂鏃跺埢鏈煡锛涚姝㈠悓鏍圭洰鏍囨鐩堬紝鍏佽鏈€涓嶅埄鐨勫悓鏍规鎹熴€?- 姝㈡崯閬囪烦绌烘寜鏇村樊寮€鐩樻垚浜わ紱鍚屾牴姝㈡崯涓庢鐩堥兘瑙﹁揪鏃跺厛姝㈡崯锛涢浂閲忔垨鍗曚环鏍奸攣瀹?K 绾夸笉鍏佽鎴愪氦銆備笉鑳芥ā鎷熺湡瀹炴定璺屽仠鎺掗槦銆?- T+1 鎸佷粨褰撴棩涓嶈兘鍗栧嚭锛涜嫢姝㈡崯鍥犳鏃犳硶鎵ц锛岃褰曢闄╀簨浠讹紝娆℃棩鍙兘鎵垮彈璺崇┖鎹熷け銆傛湯鏃ヤ粎鍦ㄥ彲浜ゆ槗涓旀弧瓒充氦鏀舵潯浠舵椂骞充粨锛屽惁鍒欎繚鐣欐湭瀹炵幇鎹熺泭銆?- 璧勯噾璐︽湰鐙珛璁板綍宸插疄鐜扮幇閲戙€佷繚璇侀噾鍗犵敤銆佹湭瀹炵幇鎹熺泭銆佽垂鐢ㄤ笌鍒嗘壒鍓╀綑鏁伴噺銆備粨浣嶈€冭檻鍚堢害涔樻暟銆佹墜鏁般€佷繚璇侀噾鍜屾垚鏈€?- 鍗曠瑪椋庨櫓銆佺浉鍏崇粍椋庨櫓銆佹€婚闄┿€佹€绘暈鍙ｃ€佹渶澶т粨浣嶆暟銆佸懆搴︾洴甯備簭鎹熷強杩炵画浜忔崯瀹℃煡鍧囧彲閰嶇疆銆傝繛缁簭鎹熷鏌ュ湪鏈杩愯涓攣瀹氭柊澧炰氦鏄擄紝涓嶅亣瑁呯郴缁熻嚜鍔ㄥ畬鎴愪汉宸ュ鏍搞€?- 鐩稿叧缁勪娇鐢ㄦ樉寮?group锛涗笉鍚岀粍涔嬮棿鍐嶆鏌ュ巻鍙叉粴鍔ㄦ敹鐩婄浉鍏虫€с€傝祫浜?/ 绫诲埆 / 琛屼笟鐩稿叧鎬у強鍚嶄箟浠撲綅 HHI 闆嗕腑搴﹀彲鏌ョ湅銆?- 鏀剁泭鐜?/ 鍥炴挙涓哄皬鏁版瘮渚嬶紝P&L / Expectancy 涓鸿处鎴峰竵绉嶉噾棰濓紝R 涓哄噣 P&L / 鍒濆鍚垚鏈闄┿€傛寔浠撴椂闀夸负鏍囩殑 K 绾挎暟锛孍xposure 涓烘棩鍘嗘椂闂村姞鏉冪殑鎬诲悕涔夋暈鍙?/ 鏉冪泭銆?- Sharpe / Sortino 浣跨敤鏃ュ巻鏃ユ敹鐩娿€侀浂鏃犻闄╂敹鐩婂熀绾裤€?65.25 骞村寲锛涘懆鏈墠鍚戞寔骞炽€侰AGR 浣跨敤瀹為檯鍘嗘椂銆傛棤浜ゆ槗鎴栧垎姣嶄负闆剁殑姣旂巼杩斿洖 null锛屼笉鍒堕€犳暟鍊笺€傜煭鏍锋湰 CAGR 涓嶇ǔ瀹氥€?
## 澶嶆潈銆佸悎绾﹀拰鏁版嵁鍋忓樊杈圭晫

涓嬭浇灞傛敮鎸佷笉澶嶆潈 / 鍓嶅鏉?/ 鍚庡鏉冦€?*鎵ц寮曟搸鎷掔粷鎶婂鏉?OHLC 褰撳疄闄呮垚浜や环銆?* `data/prices.py` 鎻愪緵鍚屾椂闂?OHLC 鐨勪豢灏勪环鏍兼槧灏勶紙鑰冭檻鍔犳€у垎绾㈠亸绉伙紝鑰岄潪閿欒鍦板彧鐢ㄦ敹鐩樻瘮鍊硷級锛涜皟鐢ㄦ柟蹇呴』鏄庣‘楠岃瘉鎸囨爣鍘嗗彶鐨?point-in-time 鍙敤鎬с€備环鏍兼槧灏勪笉绛変簬鍒嗙孩銆佹媶鑲″拰鎸佷粨鏁伴噺鐨勫叕鍙歌涓鸿处鏈紱褰撳墠榛樿涓嶅鏉冧环鏍兼敹鐩婁笉璁＄幇閲戝垎绾紝鎷嗚偂鍖洪棿闇€瑕侀澶栧鏌ャ€?
杩炵画鏈熻揣鐩存帴鎷掔粷锛涘叿浣撳悎绾﹀繀椤绘彁渚涘彲闈犱唬鐮併€佷箻鏁般€佷繚璇侀噾銆佹椂鍖恒€佹椂娈靛拰鍒版湡鏃ワ紝鎸夊埌鏈熼€€鍑恒€傜己灏戝彲楠岃瘉鎹㈡湀鍘嗚〃鏃朵笉鍚堟垚杩炵画鍚堢害鏀剁泭銆傚皻鏈缓绔嬮€愭棩缁撶畻鍜岀淮鎸佷繚璇侀噾寮哄钩妯″瀷銆?
涓嶅悓甯佺绂佹鐩稿姞锛涙棤鍙潬 FX 鏃朵笉鍚敤缁熶竴璁′环缁勫悎銆傚姞瀵嗚揣甯併€佸姹囧拰娴峰鍟嗗搧鏃犲凡楠岃瘉鐨?efinance 閫傞厤鍣紝鍦ㄧ嚎鏄庣‘ `UNSUPPORTED`锛屽厑璁稿甫鏉ユ簮鐨勭湡瀹炵绾挎暟鎹爺绌躲€?
褰撳墠 watchlist 涓嶆槸鍘嗗彶鏃剁偣鍏ㄥ競鍦烘垚鍒嗭紝鎶ュ憡鏍囪骞稿瓨鑰呭亸宸紝涓嶈兘鎹澹扮О娑堥櫎浜嗛€€甯傛牱鏈亸宸€傛垚鏈?YAML 涓烘槑纭爺绌跺亣璁撅紝涓嶆槸瀹炴椂鍒稿晢璐圭巼锛涚己灏戞暟鎹殑鍊熷埜 / 铻嶈祫 / 璧勯噾璐圭巼璁板綍 null 鍜屾湭寤烘ā椤广€傝偂绁ㄥ仛绌洪』璧勪骇鍙仛绌轰笖鍊熷埜鎴愭湰宸叉槑纭厤缃€?
## 鐮旂┒涓庡鐜?
`outputs/<瀹為獙ID>/` 淇濆瓨 manifest銆佹寚鏍囥€佽緭鍏?Parquet 蹇収銆佷氦鏄?/ 鎴愪氦 / 椋庨櫓浜嬩欢 / 淇″彿鐨?CSV 涓?Parquet銆佽嚜鍖呭惈 HTML 鎶ュ憡銆丳ython 婧愮爜涓庨厤缃?ZIP銆侱uckDB 绱㈠紩瀹為獙鍜屼氦鏄撹褰曘€傝褰曟簮浠ｇ爜鍝堝笇銆佷緷璧栫増鏈€佽祫浜ц鍒欍€佸弬鏁般€佹垚鏈€佹墽琛屽亣璁俱€佹暟鎹潵婧愪笌鍐呭鍝堝笇銆?
澶嶅埗瀹為獙閲嶇畻骞剁敓鎴愭柊 ID銆傛櫘閫氬疄楠岄噸鏂扮敓鎴愪俊鍙凤紱Walk Forward 绛夋樉寮忔彁渚涗俊鍙风殑瀹為獙澶嶆斁宸茶褰曠殑淇″彿鎵ц锛宍supplied_signals` 鏄庣‘鏍囪杩欎竴宸埆銆傞暱鏈熷鐜伴渶浣跨敤淇濆瓨鐨勬簮鐮佸強鐩稿悓渚濊禆鐗堟湰銆?
Walk Forward 鍙寜璁粌鏈?`total_return - 2 * max_drawdown` 閫夋嫨鍙傛暟锛屽苟瑕佹眰鏈€灏戜氦鏄撴暟锛涙祴璇曟涓嶅彲閲嶅彔锛岃缁冧笉瓒充細杩斿洖鏄庣‘鐘舵€併€傛祴璇曚繚鐣欒缁冨巻鍙插仛鎸囨爣棰勭儹锛屼絾浠呮祴璇曟湡淇″彿鍙備笌鎵ц銆傝瘎鍒嗘秷铻嶅彧绉婚櫎璇勫垎鍥犵礌骞堕噸褰掍竴鍖栵紝涓嶅伔鍋锋敼鍔ㄧ瓥鐣ョ殑纭€ц鍒欍€侻onte Carlo 鏀寔鍥哄畾閲戦浜ゆ槗 P&L 椤哄簭閲嶆帓鍜?IID bootstrap锛屼笉淇濈暀搴忓垪渚濊禆銆佸苟鍙戠粍鍚堢害鏉熸垨澶嶅埄锛涚粨鏋滀笉鏄敹鐩婁繚璇併€?
## 浠ｇ爜缁撴瀯

```text
quant_research/
  data/          efinance 杩涚▼闅旂璋冪敤銆佹牎楠屻€佽仛鍚堛€丳arquet 蹇収銆佷环鏍肩┖闂?  indicators/    EMA / SMA / Wilder ATR / ADX / RSI / MACD / ROC / 閲忎环 / 缁撴瀯 / 鍖哄煙
  strategies/    BaseStrategy 涓庝笁濂楃嫭绔嬬瓥鐣?  backtest/      浜嬩欢寮曟搸銆佹垚浜ゆ垚鏈€佺哗鏁堟寚鏍?  research/      DuckDB 瀹為獙绠＄悊銆佹晱鎰熸€с€佹秷铻嶃€乄alk Forward銆丮onte Carlo
  app/           涓枃 Streamlit 鐮旂┒宸ヤ綔鍙?  risk.py        浠撲綅涓庣粍鍚堥闄?  regime.py      澶氳鍒欏競鍦虹姸鎬佸垎绫?  decision.py    纭繃婊や笌鍙В閲婅瘎鍒?  manual_trading.py  浜哄伐璁″垝涓庢棩蹇?  reports.py     浜や簰鍥捐〃涓庣绾?HTML 鎶ュ憡
  service.py     杩愯涓庢寔涔呭寲缁熶竴鍏ュ彛
  cli.py         鍛戒护琛屽叆鍙?config/          璧勪骇 / 鏃舵 / 绛栫暐 / 鎴愭湰 / 椋庨櫓
tests/           浜哄伐娴嬭瘯澶瑰叿鍙婅嚜鍔ㄩ獙璇?docs/            鍘熷闇€姹傘€佹帴鍙ｅ璁°€佽兘鍔涚煩闃靛拰璁捐璇存槑
```

鎸囨爣涓殑 VWAP 浠呭湪杈撳叆鍏锋湁鍙潬 `session_id` 鏃惰绠楋紱缂哄け鏃朵繚鎸佷笉鍙敤锛屼笉鎶婅法澶滅疮璁′环鏍煎啋鍏呮棩鍐?VWAP銆?
