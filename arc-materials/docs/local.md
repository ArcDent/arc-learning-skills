# 本地转换路线

零上传。适用 rtf epub。

## rtf

1. `textutil -convert txt 源.rtf -output 临时.txt`
2. 直读临时.txt，按 docs/format-spec.md 组装落盘到课题夹 notes/，tool 记 textutil，fidelity 记 text。
3. `uv run scripts/audit_md.py 产物.md` 校验通过后登记。

## epub

1. `uv run scripts/epub2md.py 输入.epub 输出.md [--max-chapters N]`。按 spine 章序输出，h1 到 h6 映射标题层级，图片提取到 notes/assets/ 并改写引用，每章前插 p.N 锚点。
2. 按 docs/format-spec.md 补 frontmatter，tool 记 epub2md，fidelity 记 text。
3. `uv run scripts/audit_md.py 产物.md` 校验通过后登记。
