<p align="center">
  <img alt="arc-learning-skills" src="https://capsule-render.vercel.app/api?type=waving&color=0:1F6FEB,100:8250DF&height=200&section=header&text=arc-learning-skills&fontSize=60&fontColor=FFFFFF&fontAlignY=35">
</p>

<p align="center">
  <img alt="把讲义和课件转成 markdown；提炼出能追回原文的考点清单；用问答、练习和引导式解题学会它" src="https://readme-typing-svg.demolab.com?font=Fira+Code&pause=1000&color=1F6FEB&center=true&vCenter=true&width=480&lines=%E6%8A%8A%E8%AE%B2%E4%B9%89%E5%92%8C%E8%AF%BE%E4%BB%B6%E8%BD%AC%E6%88%90+markdown;%E6%8F%90%E7%82%BC%E5%87%BA%E8%83%BD%E8%BF%BD%E5%9B%9E%E5%8E%9F%E6%96%87%E7%9A%84%E8%80%83%E7%82%B9%E6%B8%85%E5%8D%95;%E7%94%A8%E9%97%AE%E7%AD%94%E3%80%81%E7%BB%83%E4%B9%A0%E5%92%8C%E5%BC%95%E5%AF%BC%E5%BC%8F%E8%A7%A3%E9%A2%98%E5%AD%A6%E4%BC%9A%E5%AE%83">
</p>

<p align="center">
  <a href="#功能"><img alt="Skills：7 个" src="https://img.shields.io/badge/Skills-7_%E4%B8%AA-2ea44f?style=for-the-badge"></a>
  <a href="#快速开始"><img alt="快速开始：安装" src="https://img.shields.io/badge/%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B-%E5%AE%89%E8%A3%85-0969da?style=for-the-badge"></a>
  <a href="arc-learning-map/assets/skeleton.md"><img alt="学习地图：查看" src="https://img.shields.io/badge/%E5%AD%A6%E4%B9%A0%E5%9C%B0%E5%9B%BE-%E6%9F%A5%E7%9C%8B-8250df?style=for-the-badge"></a>
</p>

<p align="center">
  <a href="https://skillicons.dev"><img alt="技术栈：Markdown、Python、HTML、CSS、JavaScript" src="https://skillicons.dev/icons?i=md,py,html,css,js"></a>
</p>

## 关于

arc-learning-skills 是一组 Claude Code skill，帮学生把一门课从讲义学到会做题。你把讲义和课件交给它，它先转成 markdown、提炼出考点清单，再陪你做概念问答、练习题和引导式解题，最后在仪表盘里汇总进度。

每个 skill 都只在你用斜杠命令（如 `/arc-distill`）点名时才启动，彼此不会互相调用，全程用中文交流。

## 功能

先用前两个 skill 把材料变成考点清单，之后的问答、出题和解题可以任意组合、反复使用：

```text
arc-materials → arc-distill → ┬ arc-concept-quiz 查概念理解
                              ├ arc-examiner 出题自练 → arc-socratic-drill 对局解题
                              └ → arc-dashboard 进度看板
```

- **材料入库** [`/arc-materials`](arc-materials/SKILL.md)：把 PDF、Office 文档、EPUB、图片和网页转成 markdown，存进课题的 `notes/` 并登记。默认交给 MinerU 云端解析，用不了或不想上传时，改走本地转换或看图转写。
- **提炼考点** [`/arc-distill`](arc-distill/SKILL.md)：从 `notes/` 里的 markdown 提炼定义、公式等考点，合并进课题的 `concepts.md`。每条都附原文摘录和出处，随时能追回原文。
- **概念问答** [`/arc-concept-quiz`](arc-concept-quiz/SKILL.md)：每批 5 题，让你用自己的话解释 `concepts.md` 里的概念，按核心点批改，答错当场讲清。当场答对先记为待复验，隔天复验通过才算掌握。
- **出练习题** [`/arc-examiner`](arc-examiner/SKILL.md)：按指定材料或概念出 3 到 5 道题，题目存进 `problems/`，参考答案单独放在 `.local/answers/`，平时看不到。你说「随便出」时，它优先挑薄弱概念出题。
- **引导解题** [`/arc-socratic-drill`](arc-socratic-drill/SKILL.md)：拿你给的一道题开一场对局，每轮先问你下一步怎么做，卡住时最多给两级提示。你自己写出完整的解题骨架才算通关。
- **进度仪表盘** [`/arc-dashboard`](arc-dashboard/SKILL.md)：每次都从概念清单、问答与对局记录、出题记录重新计算进度，生成浏览器能直接打开的 `dashboard.html`。缺数据的板块直接隐藏，不编数字。
- **学习地图** [`/arc-learning-map`](arc-learning-map/SKILL.md)：在对话里列出每个 arc skill 管什么、怎么调用，并讲清三个做题类 skill 的区别。忘了该用哪个时，先看它。

## 快速开始

```sh
# 1. 克隆本仓库
git clone <本仓库的 git 地址> ~/arc-learning-skills

# 2. 进入你存放课程资料的学习仓库
cd <你的学习仓库>

# 3. 链接 7 个 skill：Claude Code 从 .claude/skills 加载，学习地图从 .agents/skills 读取
mkdir -p .claude/skills .agents/skills
ln -s ~/arc-learning-skills/arc-* .claude/skills/
ln -s ~/arc-learning-skills/arc-* .agents/skills/

# 4. .local/ 里放参考答案、token 和登记表，别提交进 git
echo "/.local/" >> .gitignore
```

装好后在 Claude Code 里输入 `/arc-learning-map` 看速查表，或者直接用 `/arc-materials` 导入第一份讲义。

材料转换还会用到：

- [uv](https://docs.astral.sh/uv/)：运行转换脚本，依赖在第一次运行时自动安装。
- [MinerU](https://mineru.net) 的 API token：PDF 和 Office 文档默认交给 MinerU 云端解析。没有 token 或不想上传时，`/arc-materials` 会改走本地转换或看图转写。
- `officecli`：转换 Excel 表格，或者不用 MinerU 处理 Office 文档时使用。

## 许可证

MIT 许可证，详见 [LICENSE](LICENSE)。

<p align="center">
  <img alt="" src="https://capsule-render.vercel.app/api?type=waving&color=0:1F6FEB,100:8250DF&height=120&section=footer">
</p>
