---
name: arc-materials
description: 材料摄入。把 PDF/Office/图片/EPUB/HTML 转成 markdown 落到课题 notes/ 并登记。触发：转换材料、材料转 md、材料入库。全程中文。
disable-model-invocation: true
---

# arc-materials 材料摄入

把任意格式的学习材料转成结构化 markdown，落到课题夹 `notes/` 并登记全局索引，转完即停。

## 铁律

1. **只转换不凝练**：提炼要点、出题、开对局都不属于本 skill。
2. **源文件只读**：绝不修改、移动、重命名、删除用户的源材料。
3. **每次转换必登记**：`.local/ingest-index.jsonl` 只追加，绝不覆盖已有条目。
4. **产物格式见 `docs/format-spec.md`**：组装前照单过一遍，不过关不算组装完成。
5. **不得编造**：看不清或不确定的内容标 `<!-- 无法辨认 -->`，禁止猜测补全。

## 文件约定

- **产物**：`{课题夹}/notes/YYYY-MM-DD-材料短名.md`。无课题归属落仓库根 `inbox/`。短名取材料实质内容，不沿用「汇总」「最终版」字样。
- **登记**：`.local/ingest-index.jsonl` 每行一个 JSON：`date`、`source`、`hash`、`topic`、`output`、`tool`。`hash` 是源文件 SHA-256 前 16 位。

## 格式路由表

| 输入 | 路线 |
|---|---|
| .pdf .ppt .pptx .doc .docx .html | `docs/mineru.md` |
| .rtf .epub | `docs/local.md` |
| .xlsx .ppt 内嵌表格 | `docs/officecli.md` |
| .md .txt | 直读，加 frontmatter 落盘，tool 记 direct |
| 图片 png jpg 等 | `docs/model-read.md` |

MinerU 是默认路线，不可用或拒绝传云时 pdf 改走 `docs/model-read.md`，Office 改走 `docs/officecli.md`。

## 流程

### 1. 收集与归属

点名文件直接列；点名目录就扫描候选格式列清单，排除 `.git/`、`node_modules/` 和 notes/ 内已有产物。用选择题提问工具逐份确认归属课题，可选现有课题夹、`inbox/` 或新建课题。归属只用用户亲口确认的答案。

### 2. 判重

`shasum -a 256 源文件 | cut -c1-16`。同 source 且同 hash 已登记就跳过转换，报告已有产物路径。hash 不同说明材料重转过，重新转换、覆盖同名产物、追加登记，旧条目不动。

### 3. 转换

按路由表读对应路线文档执行。多文件逐个处理，失败如实汇报，不静默跳过。

### 4. 组装与校验

按 `docs/format-spec.md` 组装，校验命令见路线文档。

**完成判据**：校验命令通过，format-spec 的可读性自查逐项过关。

### 5. 落盘登记后停

产物目录不存在则创建。产物写盘后往 `.local/ingest-index.jsonl` 追加登记。汇报产物路径、来源、规模、tool、fidelity 与已知盲区，提示下一步可用 `/arc-distill` 凝练。
