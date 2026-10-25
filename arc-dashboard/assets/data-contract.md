# 数据契约

数据源、注入 JSON 结构与字段口径只在本文件定义。`scripts/build_dashboard.py` 照本文件实现，改口径时两边一起改；模板只读注入的 JSON。

`{课题}` 指仓库根下不以 `.` 开头的目录。数据源文件不存在时，对应字段给空值。单条解析不了就跳过不计，脚本逐条列出文件和行号。解析不了包括：状态不合四值、标题缺类型、漏洞行不合格式、依赖指向不存在的 id、登记表坏行。

## 数据源映射

| 数据源 | 读出什么 | 填哪些字段 |
|---|---|---|
| `{课题}/concepts.md` | 每条状态、类型、依赖 | `concepts`、`blocked` |
| `{课题}/drills/*.md` | 首行 `<!-- arc-drill: -->` 状态、日期、题目短名 | `drills`、`activity` |
| `{课题}/concept-sessions/*.md` | 场次日期、概念名 | `activity` |
| `{课题}/gaps.md` | 漏洞条目：描述、id、日期、来源 | `vulnerabilities`、`vulnerabilityCounts` |
| `.local/answers/index.jsonl` | date/topic/topics/difficulty/question_type/cognitive_level/problem_file | `questions`、`vulnerabilities[].rePracticed`、`vulnerabilityCounts.open`、`activity` |
| `{课题}/notes/*.md` | 产物文件数 | `guidance.materials` |
| `.local/distill-index.jsonl` | 已凝练登记 | `guidance.distillable` |

## 注入 JSON 结构

模板里有一行占位符 `__ARC_DASHBOARD_DATA__`，生成时用一段合法 JSON 整体替换它。JSON 里不写注释和尾逗号，`<` 一律写成 `\u003c`，免得描述里的 `</script>` 截断注入块。字段缺省时给空值，模板会省略对应模块。

```json
{
  "generated": "YYYY-MM-DD",
  "topics": ["热统"],
  "concepts": {
    "byStatus": {"mastered": 7, "pending": 3, "misconceived": 4, "untested": 28},
    "byType": {"定义": 11, "公式": 14},
    "byTopic": {"热统": {"mastered": 5, "pending": 2, "misconceived": 2, "untested": 18}}
  },
  "drills": {"total": 9, "passed": 6, "surrendered": 1, "open": 2,
             "byTopic": {"热统": {"passed": 4, "surrendered": 1, "open": 1}}},
  "vulnerabilities": [{"desc": "说不出相律中自由度的含义", "id": "D-012", "date": "2026-10-13", "source": "问答", "rePracticed": true},
                      {"desc": "杠杆规则适用条件记错", "id": "D-031", "date": "2026-10-11", "source": "对局", "rePracticed": false},
                      {"desc": "分不清强度量与广延量", "date": "2026-10-09", "source": "手动", "rePracticed": false}],
  "vulnerabilityCounts": {"total": 3, "open": 2},
  "activity": [{"date": "2026-10-13", "kind": "概念问答", "label": "热统 · 相律、杠杆规则 等 5 个概念"}],
  "blocked": [{"concept": "克劳修斯-克拉佩龙方程", "missing": ["相变潜热"]}],
  "questions": {"total": 15, "byDifficulty": {"基础": 5}, "byType": {"简答": 10}, "byCognitive": {"理解": 6}},
  "guidance": {"materials": 6, "distillable": 2}
}
```

## 字段口径

- `concepts`：concepts.md 逐条读状态与类型，按状态、类型、课题三组计数。类型取标题「### D-xxx 名称（类型）」末尾括号，标题不合此式的条目整条跳过。状态取值见 `arc-distill/assets/concept-format.md`，`byStatus` 四键固定：mastered ☑ / pending `待复验 @ 日期` / misconceived ⚠ / untested ☐。
- `drills`：逐文件读首行状态标记计数，surrendered 与 open 分开计。
- `vulnerabilities`：各课题 `gaps.md` 的条目逐条抽出，格式见 `arc-gaps/assets/gap-format.md`；问答文件、对局文件里残留的旧 `- 漏洞：` 行不读，要算进来先用 `/arc-gaps` 迁移。按日期倒序，同日后记的在前，最多 20 条；只读「## 条目」下的行。
  - `source`：照抄条目的来源，取 问答 / 对局 / 对局（认输） / 手动。
  - `rePracticed`：漏洞带 `[D-xxx]` 时，`.local/answers/index.jsonl` 里存在同课题、`topics[]` 含该 id、日期不早于漏洞日期的题即为 true；没有 id 一律 false。
- `vulnerabilityCounts`：`total` 为全部漏洞条数，`open` 为其中 `rePracticed` 为 false 的条数。两个数都按全部漏洞算，不受 `vulnerabilities` 最多 20 条的限制。
- `activity`：每件事一条，按日期倒序取最近 8 条；同日按文件序号（`-2`、`-3`）或登记行号倒序。对局和问答的日期取正文「- 日期：」，没有就取文件名开头的日期；出题取登记的 `date`。
  - 对局：每个对局文件一条，`kind` 为「对局」，`label` 为「课题 · 题目短名」，短名取「# 答题：」标题，没有就取文件名去掉日期。
  - 问答：每个有题的问答文件一条，`kind` 为「概念问答」，`label` 为「课题 · 前两个概念名」，超过两个时后接「等 N 个概念」。`.local/` 下的问答登记表不读，它和问答文件一场各记一条，都读会重复。
  - 出题：index.jsonl 每题一条，`kind` 为「出题」，`label` 为「课题 · 题名」，题名取 `problem_file` 去掉日期前缀。
- `blocked`：只列状态为 ⚠ 或待复验的概念，☐ 概念不列，避免开学时整份清单都算阻塞。`missing` 取该概念 `依赖` 字段中状态非 ☑ 的前置名称，没有这样的前置就不列。
- `questions`：index.jsonl 按 difficulty、question_type、cognitive_level 分别计入 `byDifficulty`、`byType`、`byCognitive`，`total` 为题数；某题缺某个字段只不计入那一组。
- `guidance`：`materials` 数所有带 `notes/` 的目录下 `notes/*.md` 产物数，不要求该课题已有 concepts.md；`distillable` 数其中相对仓库根的路径未作为 `material` 登记进 `.local/distill-index.jsonl` 的产物。没有任何 `notes/` 时给空值。其他模块有数据时也照填，因为模板靠它给出「下一步」提示；「下一步」不算数据模块。
- `topics` 按名称排序，列全部有 concepts.md 或 `drills/*.md` 的课题；`concepts`、`drills`、`vulnerabilities`、`activity` 只读这些课题。`byTopic` 只列有数据的课题。
