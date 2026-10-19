# MinerU 云解析路线

适用 pdf ppt pptx doc docx html。html 自动切 MinerU-HTML 模型版本。文件名保留真实后缀上传。

## 第 0 步 token

token 在 .local/mineru-token，600 权限，git 忽略。缺失或失效时用选择题提问工具问用户能否提供。能提供就写入 chmod 600 并跑 `uv run scripts/mineru_run.py --ping` 验证。拒绝就按输入格式改走 docs/local.md 或 docs/officecli.md。

## 流程

1. 确认批次：列文件清单、各文件页数和总页数，用户同意才上传。
2. `uv run scripts/mineru_run.py 源文件 [更多文件]`
3. `uv run scripts/rebuild_md.py xx_content_list.json --topic 课题 --source 路径 --hash 16位 --out 课题夹/notes/日期-短名.md`。页锚点、标题、公式归一化、图片拷贝、frontmatter 自动生成，写盘前自动过 audit。`--spot` 写实际抽查过的页码和内容。fidelity 记 ocr。

## 限制

- 单文件 200MB 与 600 页上限，单批 200 文件，每天 2000 页高优额度。
- 长材料先问页范围，页数消耗额度。
- 个别 docx 报 parsing failed 时重试一次，仍失败改走 docs/officecli.md。
- rtf epub 实测被服务端拒收，不要传云。
