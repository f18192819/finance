# 交付验证记录

验证日期：2026-11-14（Asia/Shanghai）。

## 程序验证

- Python 3.12.7；项目安装在本地 `.venv`，实际依赖版本固定在 `requirements.txt`。
- 全套 pytest 通过，包含三套策略正向规则链、指标算例、历史前缀一致性、成交与风险边界、价格空间保护、实验复现、Walk Forward、CLI CSV 端到端和 Streamlit 有数据 / 无数据页面交互。
- 浏览器在 `http://127.0.0.1:8501` 检查总览页面：1440px 视口无横向溢出，无 Streamlit 异常元素。
- Streamlit 本地服务日志：`outputs/server.stdout.log`、`outputs/server.stderr.log`；进程号记录在 `outputs/server.pid`。
- 测试数据只在测试与临时目录内使用，均标明 SYNTHETIC；没有把测试收益发布为真实市场业绩。

## 数据验证

- 指定的六个 efinance API 均检查本机签名并实际发起调用，详细参数、字段、样本或失败原因见 `efinance_api_audit.json`。
- ETF 实时报价和基金净值接口成功；基金净值明确不是 OHLCV。
- 八个资产分类 × 五个周期共 40 个能力记录：25 个历史行情请求样本为 ERROR，15 个未实现在线适配的分类周期为 UNSUPPORTED。Crypto / Forex / 海外 Commodity 不默认支持。
- 对中文股票 / ETF / 指数适配补充了显式行情 ID，避免代码检索歧义；按更新后适配器重新检测，历史 K 线仍存在连接、空返回或超时问题。
- 未启用其他在线行情 API；未用实时快照、基金净值或人工模拟数据替代历史 K 线。

## 尚未获得的外部验证

真实历史 K 线的端到端回测、跨市场业绩对比与正期望收益结论尚未建立。需要 efinance 历史接口恢复，或用户提供有来源的实际历史 CSV。公司行为、历史全市场成分、FX 换算、期货换月及交易所特殊日历也需要可靠数据；当前限制和拒绝路径详见 README。
