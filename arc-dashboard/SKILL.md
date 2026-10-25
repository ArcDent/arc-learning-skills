---
name: arc-dashboard
description: 进度仪表盘。从学习数据源算指标注入模板生成 dashboard.html，缺数据就省略，不编数。触发：更新仪表盘、看看进度。全程中文。
disable-model-invocation: true
---

# arc-dashboard 进度仪表盘

`scripts/build_dashboard.py` 每次从学习数据现算指标，把结果填进 `assets/dashboard-template.html`，生成仓库根的 `dashboard.html`。产物是单个文件，浏览器能直接打开，可以提交。

数据源、注入 JSON 结构与字段口径只在 `assets/data-contract.md` 定义，脚本照它实现；用户问某个数字怎么来的，或要改统计口径时，再读它。

## 铁律

1. **只读不改**：数据源一律只读，唯一的写操作是脚本生成 `dashboard.html`。
2. **只用脚本生成**：每次都重跑脚本，不拿旧的 `dashboard.html` 做增量。数字只认脚本输出，不自己算、不补数、不估算，也不手填 JSON、不手改产物。

## 流程

1. **生成**：在学习仓库根运行 `python3 {本skill路径}/scripts/build_dashboard.py`。退出码 2 是仓库根不对，换到仓库根重跑；退出码 1 是模板出错，照实汇报报错后停止。
2. **汇报并停止**：照脚本输出列出产物路径、渲染与省略的模块及原因。有跳过条目时逐条列出，说明它们没算进数字，要回源文件按格式改。全空时说明引导页已就位，提示先用 `/arc-materials`、`/arc-distill` 造数据。
