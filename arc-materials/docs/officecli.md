# officecli 直读路线

适用 xlsx 和 ppt 内嵌表格。

1. `officecli view 文件 text`。输出带 /body/p[N]、/slide[N]、/sheet[N] 路径标注，保留标注用于结构组装。
2. docx 先 `officecli get 文件 "/body/p[N]"` 读标题样式，按 Heading N 组装层级。
3. 提取结果只有文本不含图片，关键信息在图里时改走 model-read。
4. 按 docs/format-spec.md 组装落盘到课题夹 notes/，tool 记 officecli，fidelity 记 text。
5. `uv run scripts/audit_md.py 产物.md` 校验通过后登记。
