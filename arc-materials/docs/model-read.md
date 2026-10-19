# model-read 视觉直读路线

适用 png jpg 等图片，以及无文本层 PDF 的回退。

1. 多页 PDF 先 `uv run scripts/render_pages.py 源.pdf 起页 止页` 渲染页图到 /tmp/qm-pages，单张图片直接 Read。
2. Read 直读逐页视觉转写，公式记 LaTeX，看不清的内容标 `<!-- 无法辨认 -->`。
3. 每页或每图前加 p.N 或 图N 锚点。
4. 按 docs/format-spec.md 组装落盘到课题夹 notes/，tool 记 model-read，fidelity 记 vision。
5. `uv run scripts/audit_md.py 产物.md` 校验通过后登记。

## pdf 文本层回退

`uv run scripts/pdf2md.py 输入.pdf 输出.md [--pages 12-30]` 输出 p.N 锚点。合法丢空白页时 audit 加 --allow-anchor-gaps。`uv run scripts/pdf_probe.py 输入.pdf` 判定文本层质量。tool 记 pdf2md，fidelity 记 text。
