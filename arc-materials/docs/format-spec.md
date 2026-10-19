# 产物格式规格

arc-materials 产物格式契约，组装前逐项过一遍。arc-distill 与 audit_concepts.py 也按此解析。

## frontmatter 七字段

```yaml
---
source: 热统/PPT/第5讲.pptx
topic: 热统
scope: 全部
date: 2026-10-13
tool: officecli
fidelity: text
hash: a1b2c3d4e5f60718
---
```

- `scope` 写页范围。PDF 与 EPUB 记 pp.12-30，PPT 记 slides 3-8，全量记「全部」。
- `fidelity` 三档：`text` 是文本层直读零损失，`ocr` 是 MinerU 等 OCR 或 VLM 引擎，`vision` 是模型视觉转写。供 arc-distill 判断哪些内容需回查源文件。同一产物内可靠性不一时取最低档，可疑处标 `<!-- 无法辨认 -->` 或批注。

## 锚点约定

| 格式 | 锚点 |
|---|---|
| PDF / EPUB / PPT | 每页或每张幻灯片前 `<!-- p.N -->`，不可见、可 grep。MinerU 路线 ppt 的 N 即幻灯片号，epub 路线 N 即 spine 章序 |
| DOCX | 按标题样式组装 `#`/`##` 层级，不加页锚点 |
| XLSX | 每个 sheet `## Sheet: {名}` |
| 图片 / 扫描件 | 每张图或每页 `<!-- 图 N -->` 或 `<!-- p.N -->` |

## 可读性自查

组装完成前逐项确认：

- 标题层级贴合源文件结构。
- 公式一律 LaTeX。
- 表格规范，合并单元格展平后加表注。
- 清洗解析噪声与工具自带的分块标记。
- 长段落不切断。