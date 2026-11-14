# Meridian · Multi-Market Quant Research System

基于 **efinance** 的本地 Swing Trading 研究平台。三套独立策略、逐根 K 线与组合回测、样本外研究、实验快照和人工交易计划。只辅助人工交易，没有实盘下单接口。

## 启动

本目录已建立 `.venv` 并安装项目。PowerShell：

```powershell
cd C:\data\Automatic\Windows\finance
.\start.ps1
```

打开 **http://127.0.0.1:8501**。也可直接运行：

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

新环境安装（Python 3.11+，本次验证 Python 3.12.7）：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe -m pytest
```

本次本地虚拟环境使用 `--system-site-packages` 复用已有依赖；`requirements.txt` 固定了实际验证版本，新机器可创建完全隔离环境。

## 当前数据验证结果

2026-11-14 对已安装 **efinance 0.5.5.2** 检查实际签名并发起真实调用。网页文档显示 0.5.9，因此适配器以本机源码和签名为准。

| 接口 | 本机实测 | 用途 / 限制 |
|---|---|---|
| `stock.get_quote_history` | ERROR：空返回、连接错误或超时 | 历史 K 线尚未取得成功样本 |
| `stock.get_realtime_quotes(fs='ETF')` | 成功，1660 行 | 仅实时报价快照，不能替代历史回测 |
| `fund.get_quote_history('161725', pz=10)` | 成功，10 行 | 基金净值，不是 OHLCV，禁止伪造开高低收 |
| `futures.get_quote_history` | ERROR | 连续合约另外禁止直接执行回测 |
| `futures.get_realtime_quotes` | ERROR | 当前请求返回无效响应 |
| `futures.get_futures_base_info` | ERROR | 当前请求返回无效响应 |

完整证据在 [接口审计](docs/efinance_api_audit.json) 和 [市场周期矩阵](docs/data_coverage.json)。运行时最新矩阵在 `data/metadata/coverage.json`。`SUPPORTED` 只意味着指定样本验证成功，不代表整个市场、全部日期可用。

**因此目前没有真实历史行情回测业绩，也没有“已验证盈利”的策略。** 自动化测试使用明确标记的人工测试夹具，隔离在 `tests/` / 测试临时目录中；界面不加载虚构行情。数据源恢复后重新检测或导入真实 CSV，即可运行全流程。

## 使用流程

1. **数据中心**：下载不复权行情，或导入带来源说明的 CSV；查看实际区间、完整 K 线、时区和异常记录。
2. **策略实验室**：编辑并校验 JSON 参数。三套规则分别研究，默认运行明确命名的 `single_timeframe` 变体。
3. **历史回测**：选择一套或多套策略，分别计算收益、回撤、成本、交易记录及风险拒单。每次运行自动持久化。
4. **组合分析**：同币种多资产、多策略共享一份资金账本；查看相关性与集中度。混合币种直接拒绝。
5. **稳健性研究**：参数网格、二维热力图、评分因素消融、滚动训练 / 样本外测试、固定随机种子的 Monte Carlo。
6. **交易记录与计划**：生成最新历史信号的人工计划，记录人工决定，比较实验、标记重点研究、复制复现。

最新历史信号不保证是当前信号。人工计划的参考仓位假设没有其他持仓，必须结合实际组合重新确认。

## 命令行

```powershell
# 实测市场与周期覆盖；单次调用有进程级硬超时
.\.venv\Scripts\python.exe -m quant_research.cli probe --start 2025-01-01 --end 2025-12-31

# 首次下载 / 缓存复用；--refresh 请求刷新，不复权模式可增量更新
.\.venv\Scripts\python.exe -m quant_research.cli download --symbol 510300 --start 2021-01-01 --end 2025-12-31

# 独立策略回测
.\.venv\Scripts\python.exe -m quant_research.cli backtest --symbol 510300 --strategy trend_following
.\.venv\Scripts\python.exe -m quant_research.cli backtest --symbol 510300 --strategy breakout
.\.venv\Scripts\python.exe -m quant_research.cli backtest --symbol 510300 --strategy liquidity_reversal

# 真实离线数据（必须提供来源说明；不会标成 efinance）
.\.venv\Scripts\python.exe -m quant_research.cli backtest --symbol 510300 --csv C:\path\real_history.csv --source broker_export --strategy breakout

# 参数敏感性 / Walk Forward / 消融
.\.venv\Scripts\python.exe -m quant_research.cli sensitivity --symbol 510300 --strategy breakout --grid config/example_grid.json
.\.venv\Scripts\python.exe -m quant_research.cli walk-forward --symbol 510300 --strategy breakout --grid config/example_grid.json --folds config/example_folds.json
.\.venv\Scripts\python.exe -m quant_research.cli ablation --symbol 510300 --strategy breakout

.\.venv\Scripts\python.exe -m quant_research.cli experiments
.\.venv\Scripts\python.exe -m quant_research.cli reproduce EXPERIMENT_ID
.\.venv\Scripts\python.exe -m quant_research.cli monte-carlo EXPERIMENT_ID --method bootstrap --seed 42
```

命令失败返回非零退出码，不静默制造成功结果。`scripts/audit_efinance.py` 可重新验证六个指定接口。

## CSV 规范与时间语义

最低字段：`timestamp,open,high,low,close,volume,amount`。`symbol` 由已配置的资产确定。空模板见 `docs/ohlcv_template.csv`。

- 日线 `timestamp` 可为交易日期，系统按资产交易所时区映射到实际日盘收盘时刻；保留明确的 `open_time`。
- 1H 的 `timestamp` 必须是收盘时刻，按交易所时段验证整小时 K 线。不足 60 分钟的尾段明确排除，不拼接。
- 离线 4H/1W/1M 还需要 `open_time`，两个时间均建议使用带时区的 ISO 8601。
- 内部统一为 UTC。展示 / 日历按 `Instrument.timezone` 转换。未完成 K 线排除并记数。
- 4H 只在**同一连续交易时段**内由四根连续整小时 K 线聚合。A 股上午、下午各两小时，默认不跨午休拼接，所以该规则下 A 股 4H 不可用。
- 周 / 月由日线聚合，在该日历周期结束后才向策略发布，保守避免未完成周期泄漏。不会把日线插值成小时线。
- 假期日历、半日市与夜盘交易日映射尚无可靠交易所历表；配置不匹配时必须补充时段或禁止该资产研究。分钟深度依据真实返回范围，不假设多年可用。

## 策略定义与 LuxAlgo 参考

参考 LuxAlgo 的公开概念，**独立编写可检查的规则实现**，不声称复刻私有指标、参数或历史业绩。原始资料：

- [市场结构 / BOS / CHoCH / CHoCH+](https://docs.luxalgo.com/platform/algos/price-action-concepts/market-structures)
- [Order Blocks](https://docs.luxalgo.com/platform/algos/price-action-concepts/order-blocks)
- [Liquidity Concepts](https://docs.luxalgo.com/platform/algos/price-action-concepts/liquidity)
- [Imbalance / FVG](https://docs.luxalgo.com/platform/algos/price-action-concepts/imbalances)
- [efinance 官方 API](https://efinance.readthedocs.io/en/latest/api.html) / [官方源码](https://github.com/Micro-sheep/efinance)

本项目定义：右侧 `pivot_right` 根收盘才确认摆动点；在下一根开始使用。方向首次建立记为 CHoCH，已有方向上的结构突破记为 BOS。CHoCH+ 还要求先出现 HL / LH 的衰竭迹象。内部结构使用更短窗口。所有标签保存 `pivot_time` 和 `confirmation_time`；不在原始极值时刻提前交易。

OB 为确认结构突破前最近一根反向蜡烛的高低区间，突破收盘后才成立；记录确认、回踩和收盘穿越失效时间。FVG 采用三根 K 线间隙，完整回补后失效。最终区域生命周期表只用于审计；策略使用逐时点快照，不读未来的失效日期。

| 策略 | 必须依次发生的条件 |
|---|---|
| 趋势延续 | EMA 趋势一致 → BOS → 后续 OB/FVG 回踩 → 收盘突破前一根高 / 低点 |
| 收缩突破 | 前一根已处于 BB 宽度收缩 → 放量收盘突破历史区间 → 后续回踩区间边界并收盘确认 |
| 流动性反转 | 刺破已确认摆动点达到 ATR 最小幅度且收回 → 后续 CHoCH → 再后续 OB 回踩并收盘确认 |

默认止盈 TP1=1.5R、TP2=3R，50% 分批；引擎按实际交易单位取整，并重新检查**成本后的加权目标收益 / 风险**。日线研究不被称作 1D/4H/1H 完整策略。

严格多周期：参数设 `mode: multi_timeframe`，通过 CLI 以 `--timeframe 1H` 运行或 Python API 显式传入真实 `1D`、`4H` 数据和 `base_timeframe: 1H`。高周期只按收盘可用时间 backward-asof 对齐，缺失或非真实时长即拒绝。上下文数据一并保存，支持复现。多周期突破使用已完成 4H 规则链后续 1H 方向确认；反转还要求已完成 4H 结构方向一致。

## 成交、风险与业绩口径

- 开盘 / 收盘事件按时间排序。同一时刻先处理上一根收盘，再处理下一根开盘。无信号当根收盘成交。
- 市价单含不利滑点、半价差、最小价格单位取整；限价单不会越过限价。限价仅盘中触及时，数量按开盘信息预留，记账时间为保守开盘预留代理，真实触发时刻未知；禁止同根目标止盈，允许最不利的同根止损。
- 止损遇跳空按更差开盘成交；同根止损与止盈都触达时先止损；零量或单价格锁定 K 线不允许成交。不能模拟真实涨跌停排队。
- T+1 持仓当日不能卖出；若止损因此无法执行，记录风险事件，次日可能承受跳空损失。末日仅在可交易且满足交收条件时平仓，否则保留未实现损益。
- 资金账本独立记录已实现现金、保证金占用、未实现损益、费用与分批剩余数量。仓位考虑合约乘数、手数、保证金和成本。
- 单笔风险、相关组风险、总风险、总敞口、最大仓位数、周度盯市亏损及连续亏损审查均可配置。连续亏损审查在本次运行中锁定新增交易，不假装系统自动完成人工复核。
- 相关组使用显式 group；不同组之间再检查历史滚动收益相关性。资产 / 类别 / 行业相关性及名义仓位 HHI 集中度可查看。
- 收益率 / 回撤为小数比例，P&L / Expectancy 为账户币种金额，R 为净 P&L / 初始含成本风险。持仓时长为标的 K 线数，Exposure 为日历时间加权的总名义敞口 / 权益。
- Sharpe / Sortino 使用日历日收益、零无风险收益基线、365.25 年化；周末前向持平。CAGR 使用实际历时。无交易或分母为零的比率返回 null，不制造数值。短样本 CAGR 不稳定。

## 复权、合约和数据偏差边界

下载层支持不复权 / 前复权 / 后复权。**执行引擎拒绝把复权 OHLC 当实际成交价。** `data/prices.py` 提供同时间 OHLC 的仿射价格映射（考虑加性分红偏移，而非错误地只用收盘比值）；调用方必须明确验证指标历史的 point-in-time 可用性。价格映射不等于分红、拆股和持仓数量的公司行为账本；当前默认不复权价格收益不计现金分红，拆股区间需要额外审查。

连续期货直接拒绝；具体合约必须提供可靠代码、乘数、保证金、时区、时段和到期日，按到期退出。缺少可验证换月历表时不合成连续合约收益。尚未建立逐日结算和维持保证金强平模型。

不同币种禁止相加；无可靠 FX 时不启用统一计价组合。加密货币、外汇和海外商品无已验证的 efinance 适配器，在线明确 `UNSUPPORTED`，允许带来源的真实离线数据研究。

当前 watchlist 不是历史时点全市场成分，报告标记幸存者偏差，不能据此声称消除了退市样本偏差。成本 YAML 为明确研究假设，不是实时券商费率；缺少数据的借券 / 融资 / 资金费率记录 null 和未建模项。股票做空须资产可做空且借券成本已明确配置。

## 研究与复现

`outputs/<实验ID>/` 保存 manifest、指标、输入 Parquet 快照、交易 / 成交 / 风险事件 / 信号的 CSV 与 Parquet、自包含 HTML 报告、Python 源码与配置 ZIP。DuckDB 索引实验和交易记录。记录源代码哈希、依赖版本、资产规则、参数、成本、执行假设、数据来源与内容哈希。

复制实验重算并生成新 ID。普通实验重新生成信号；Walk Forward 等显式提供信号的实验复放已记录的信号执行，`supplied_signals` 明确标记这一差别。长期复现需使用保存的源码及相同依赖版本。

Walk Forward 只按训练期 `total_return - 2 * max_drawdown` 选择参数，并要求最少交易数；测试段不可重叠，训练不足会返回明确状态。测试保留训练历史做指标预热，但仅测试期信号参与执行。评分消融只移除评分因素并重归一化，不偷偷改动策略的硬性规则。Monte Carlo 支持固定金额交易 P&L 顺序重排和 IID bootstrap，不保留序列依赖、并发组合约束或复利；结果不是收益保证。

## 代码结构

```text
quant_research/
  data/          efinance 进程隔离调用、校验、聚合、Parquet 快照、价格空间
  indicators/    EMA / SMA / Wilder ATR / ADX / RSI / MACD / ROC / 量价 / 结构 / 区域
  strategies/    BaseStrategy 与三套独立策略
  backtest/      事件引擎、成交成本、绩效指标
  research/      DuckDB 实验管理、敏感性、消融、Walk Forward、Monte Carlo
  app/           中文 Streamlit 研究工作台
  risk.py        仓位与组合风险
  regime.py      多规则市场状态分类
  decision.py    硬过滤与可解释评分
  manual_trading.py  人工计划与日志
  reports.py     交互图表与离线 HTML 报告
  service.py     运行与持久化统一入口
  cli.py         命令行入口
config/          资产 / 时段 / 策略 / 成本 / 风险
tests/           人工测试夹具及自动验证
docs/            原始需求、接口审计、能力矩阵和设计说明
```

指标中的 VWAP 仅在输入具有可靠 `session_id` 时计算；缺失时保持不可用，不把跨夜累计价格冒充日内 VWAP。
