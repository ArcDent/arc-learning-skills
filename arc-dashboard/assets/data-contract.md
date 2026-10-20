# 数据契约

数据源、注入 JSON 结构与字段口径只在本文件定义；模板只消费注入 JSON。

## 数据源映射

| 数据源 | 读出什么 | 填哪些字段 |
|---|---|---|
| `{课题}/concepts.md` | 每条状态、类型、依赖 | `concepts`、`blocked` |
| `{课题}/drills/*.md` | 首行 `<!-- arc-drill: -->` 状态、通关总结的 `- 漏洞：` 条目、日期 | `drills`、`vulnerabilities`、`vulnerabilityCounts`、`activity` |
| `{课题}/concept-sessions/*.md` | 场次日期、概念名、结论，终场与作废补写的 `- 漏洞：` 条目 | `vulnerabilities`、`vulnerabilityCounts`、`activity` |
| `.local/answers/index.jsonl` | date/topic/topics/difficulty/question_type/cognitive_level | `questions`、`vulnerabilities[].rePracticed`、`vulnerabilityCounts.open`、`activity` |
| `.local/quiz-index.jsonl` | date/topic/results | `activity` |
| `{课题}/notes/` | 产物文件数 | `guidance.materials` |
| `.local/distill-index.jsonl` | 已凝练登记 | `guidance.distillable` |

## 注入 JSON 结构

模板内 `__ARC_DASHBOARD_DATA__` 单行占位符，用一段合法 JSON 整体替换，JSON 内禁止注释与尾逗号。字段缺省时给空值，模块自行省略。

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
                      {"desc": "杠杆规则适用条件记错", "id": "D-031", "date": "2026-10-11", "source": "对局", "rePracticed": false}],
  "vulnerabilityCounts": {"total": 2, "open": 1},
  "activity": [{"date": "2026-10-13", "kind": "概念问答", "label": "相律与自由度"}],
  "blocked": [{"concept": "克劳修斯-克拉佩龙方程", "missing": ["相变潜热"]}],
  "questions": {"total": 15, "byDifficulty": {"基础": 5}, "byType": {"简答": 10}, "byCognitive": {"理解": 6}},
  "guidance": {"materials": 6, "distillable": 2}
}
```

## 字段口径

- `concepts`：concepts.md 逐条读状态与类型，按状态、类型、课题三组计数。状态取值见 `arc-distill/assets/concept-format.md`，`byStatus` 四键固定：mastered ☑ / pending `待复验 @ 日期` / misconceived ⚠ / untested ☐。
- `drills`：逐文件读首行状态标记计数，surrendered 与 open 分开计。
- `vulnerabilities`：drill 通关总结、概念问答终场与作废补写里的 `- 漏洞：{描述} [D-xxx] @ 日期` 逐条抽出，「- 漏洞：无」不算；按日期倒序，最多 20 条。
  - `source`：drill 的写「对局」，概念问答的写「问答」。
  - `rePracticed`：漏洞带 `[D-xxx]` 时，`.local/answers/index.jsonl` 里存在同课题、`topics[]` 含该 id、日期不早于漏洞日期的题即为 true；没有 id 一律 false。
- `vulnerabilityCounts`：`total` 为全部漏洞条数，`open` 为其中 `rePracticed` 为 false 的条数。两个数都按全部漏洞算，不受 `vulnerabilities` 最多 20 条的限制。
- `activity`：对局、问答场次、出题与测验记录每条记一件事（日期 + 事件），按日期倒序取最近 8 条。
- `blocked`：只列状态为 ⚠ 或待复验的概念，☐ 概念不列，避免开学时整份清单都算阻塞。`missing` 取该概念 `依赖` 字段中状态非 ☑ 的前置。
- `questions`：index.jsonl 按 difficulty、question_type、cognitive_level 分别计入 `byDifficulty`、`byType`、`byCognitive`，`total` 为题数。
- `guidance`：`materials` 数 `notes/` 下产物数，`distillable` 数其中未登记进 `.local/distill-index.jsonl` 的产物。有数据时也照常填：模板用它给出「下一步」提示，「下一步」不算数据模块。
- `topics` 列全部有 concepts.md 或对局记录的课题，`byTopic` 只列有数据的课题。
