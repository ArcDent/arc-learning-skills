# arc 系列静态骨架

arc-learning-map 的静态数据：只有流程顺序或易混关系变化时才改本文件，新增 `arc-*` skill 无需改。

## 流程顺序

```
arc-materials → arc-distill → ┬ arc-concept-quiz 查概念理解
                              ├ arc-examiner 出题自练 → arc-socratic-drill 对局解题
                              └ → arc-dashboard 进度看板
```

支线说明：materials 把新材料转成 md，distill 把 md 提炼成概念清单 `concepts.md`。之后三条支线可任意组合、反复使用。concept-quiz 检验概念是否真懂，examiner 出一批题练手，拿到题想被引导着做就进 socratic-drill。dashboard 随时可看，不依赖顺序。三条支线靠 `concepts.md` 的概念 id（如 `D-012`）互相对上：examiner 的考点、drill 的漏洞、concept-quiz 的结果与漏洞都记 id。

## 使用场景

按流程位置写死。

| skill | 什么时候用 |
|---|---|
| arc-materials | 拿到新材料想入库时，常见 PDF、讲义、图片、EPUB |
| arc-distill | 材料转完 md 后想提炼成概念清单时 |
| arc-concept-quiz | 想检验概念有没有真懂时 |
| arc-examiner | 想要一批练习题时 |
| arc-socratic-drill | 有一道题做不出来，想被引导着做时 |
| arc-dashboard | 想看整体学习进度时 |

## 易混区别

三个都和「做题」有关，按目的区分。

| skill | 一句话区别 |
|---|---|
| arc-concept-quiz | 让你用自己的话解释 `concepts.md` 里的概念，一批 5 题，按核心点批改，答错就讲，回写状态 |
| arc-examiner | 只出题，出完即停，题目落在 `{课题}/problems/` |
| arc-socratic-drill | 不出题，接你给的题，每轮先问你下一步怎么做，引导你自己想出每一步，对局落在 `{课题}/drills/` |