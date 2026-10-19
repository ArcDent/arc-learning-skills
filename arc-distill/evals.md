# arc-distill 路由评测

> 防职责边界漂移:每次改 SKILL.md 后过一遍。arc 系列在 Claude Code 里已设 disable-model-invocation,只能 /点名启动;本表用于检查 arc-learning-map 的指路是否正确,以及不支持该字段的客户端里的自动触发。
> arc 体系五件套边界:materials 只转换,distill 只凝练,examiner 只出题,socratic-drill 只带做用户给的题,concept-quiz 只考清单内概念。

## 用例

| # | 用户输入 | 应触发 | 不应触发 | 判据 |
|---|---|---|---|---|
| 1 | 「把这份 PDF 转成 markdown」 | arc-materials | arc-distill | 输入是原始格式,转完即停,不产出 concepts.md |
| 2 | 「从刚才转好的第 5 讲里提炼考点」 | arc-distill | arc-materials / arc-examiner | 输入是 notes/ 产物,产出 concepts.md 条目,不出题 |
| 3 | 「考我几个概念」 | arc-concept-quiz | arc-examiner / arc-distill | 从 concepts.md 抽概念让学生解释,回写状态,不出题 |
| 4 | 「帮我把这道题引导着做出来」 | arc-socratic-drill | arc-examiner / arc-distill | 题是用户给的,开对局不出题 |
| 5 | 「这篇综述讲了什么,给我提炼一下」(材料是课题夹里的原始 PDF) | arc-materials 先行 | arc-distill 直接凝练 | 铁律 1:distill 只吃转换产物,原始 PDF 先转换,凝练步骤待产物就绪后单独触发 |
| 6 | 「按第 3 讲给我出几道题」 | arc-examiner | arc-concept-quiz / arc-socratic-drill | 出题落 {课题}/problems/,出完即停,不开对局 |

## 期望行为要点

- 用例 2 触发 distill 时:先问课题与用途(流程 1),凝练完必须停,不主动出题。
- 用例 5 若用户坚持直接凝练原始 PDF:拒绝并说明铁律 1,引导先走 arc-materials。