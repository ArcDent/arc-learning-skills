# 漏洞清单格式

arc 系列漏洞的唯一记录处与格式定义。arc-gaps、arc-concept-quiz、arc-socratic-drill 按此写入，arc-examiner、arc-dashboard 按此解析。旧格式的迁移见 `migrate.md`。

漏洞是学习中暴露出来的不会与误解，具体记哪些由写入方各自的规则决定。

## 落点

每课题一份 `{课题夹}/gaps.md`，不存在则按下面的头部模板创建。

## 头部模板

```markdown
# {课题名} 漏洞清单

- 维护：arc-concept-quiz、arc-socratic-drill 自动追加，arc-gaps 手动增改删
- 条目：一条一行，按记录先后追加

## 条目

{逐条排列}
```

## 条目格式

```markdown
- {描述} [D-xxx] @ YYYY-MM-DD · {来源} · {原文件}
```

- **描述**：一句话，说清错在哪或缺了什么。
- **`[D-xxx]`**：课题 `concepts.md` 的概念 id，供 examiner 重练与 dashboard 统计；对不上就省略，连同方括号。
- **日期**：记录当天。
- **来源**四选一：

| 来源 | 写入方 | 原文件 |
|---|---|---|
| `问答` | arc-concept-quiz | 问答文件，如 `concept-sessions/2026-10-13-概念问答.md` |
| `对局` | arc-socratic-drill 通关时 | 对局学生文件，如 `drills/2026-10-17-谐振子基态.md` |
| `对局（认输）` | arc-socratic-drill 认输时 | 同上 |
| `手动` | arc-gaps | 不写，行末到来源为止 |

- **原文件**：相对课题夹的路径，供追回出处。

示例：

```markdown
- 说不出相律中自由度的含义 [D-012] @ 2026-10-13 · 问答 · concept-sessions/2026-10-13-概念问答.md
- 没想到用方差把平方平均换掉，一级提示后补上 [D-055] @ 2026-10-17 · 对局 · drills/2026-10-17-谐振子基态.md
- 杠杆规则适用条件记错 [D-031] @ 2026-10-20 · 手动
```
