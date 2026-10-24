---
name: arc-learning-map
description: 学习地图。汇总 arc 系列 skill 的职责与触发词，输出对话速查表，仅限手动调用。触发：学习地图、arc 地图。全程中文。
disable-model-invocation: true
---

# arc-learning-map 学习地图

> 核心信条：**地图只负责指路，不替人上路。**

给用户自己看的 arc 系列速查表：每个 skill 干什么、怎么点名调用、当前环节该用哪个。输出到对话即止，不落盘。

## 铁律

1. **仅手动调用**：arc 系列每个 skill 的 frontmatter 都带 `disable-model-invocation: true`，只能由用户用 `/<skill名>` 点名启动，skill 之间也不互相调用。输出地图后即停；用户问「该用哪个」也只指路，不替用户启动任何 arc skill。
2. **只输出不落盘**：地图只在对话里输出，不写任何文件。
3. **不读学习数据**：不碰 `concepts.md`、`drills/`、各 index 等学习记录。地图是纯静态知识，不给「你现在学到哪」的判断。

## 数据源

- 静态骨架：流程图、使用场景映射、易混区别都见 `assets/skeleton.md`，仅流程或易混关系变化时更新。
- 职责与触发词：按前缀通配扫本 skill 目录（启动时给出的 Base directory）的同级 `../arc-*/SKILL.md`，不写死名单，读 frontmatter 的 `description`。全局、项目级哪种装法都适用，装了几个就列几个。缺某段就如实标「未写明」，不编。

## 输出格式

每次触发都按下面的格式现做。

1. 标题 `# arc 系列学习地图`，先贴 `assets/skeleton.md` 的流程图与支线说明。
2. 各 skill 速查：按流程顺序逐个输出代码块，learning-map 收尾，其使用场景标「未写明」：

```
<skill名字>
- 职责:<description 第一句>
- 调用:/<skill名>（触发词:<触发词>）
- 使用场景:<skeleton 固定映射>
```

3. 易混提醒：三个做题相关 skill 合并进同一个代码块：

```
<skill名>
- 职责:<description 第一句>
- 区别:<skeleton 易混区别>
```

4. 收尾一行：`共 N 个 skill。arc 系列全部仅手动调用，用 /<skill名> 点名才启动。`