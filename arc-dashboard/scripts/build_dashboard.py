#!/usr/bin/env python3
"""arc-dashboard 生成：按 assets/data-contract.md 现算注入 JSON，填进模板，写出 dashboard.html。

用法：python3 build_dashboard.py [仓库根] [--out 产物路径]
仓库根默认当前目录，产物默认写到仓库根 dashboard.html；数据源只读。
打印渲染与省略的模块、缺的数据源、跳过的条目，汇报照抄即可。
退出码：0 已生成（可含跳过条目）；1 模板不对；2 仓库根不存在。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "dashboard-template.html"
SLOT = "__ARC_DASHBOARD_DATA__"
DATA_TAG = re.compile(r'<script id="arc-dashboard-data" type="application/json">(.*?)</script>', re.S)

STATUS_KEYS = ("mastered", "pending", "misconceived", "untested")
STATE_KEY = {"☑": "mastered", "⚠": "misconceived", "☐": "untested"}
PENDING_RE = re.compile(r"^待复验 @ (\d{4}-\d{2}-\d{2})$")
TITLE_RE = re.compile(r"^###\s+(D-\d{3,})\s+(.*)（([^（）]+)）\s*$")
HEAD_ID_RE = re.compile(r"^###\s+(D-\d{3,})")
FIELD_RE = re.compile(r"^- (状态|依赖)：(.*)$", re.M)
DEP_RE = re.compile(r"D-\d{3,}")
DRILL_RE = re.compile(r"^<!-- arc-drill: (open|passed|surrendered) -->\s*$")
DRILL_TITLE_RE = re.compile(r"^# 答题：(.+)$", re.M)
QUESTION_RE = re.compile(r"^### \d+\. (D-\d{3,}) (.*)（[^（）]+）\s*$")
GAP_RE = re.compile(
    r"^- (?P<desc>.+?)(?: \[(?P<id>D-\d{3,})\])? @ (?P<date>\d{4}-\d{2}-\d{2})"
    r" · (?P<source>问答|对局（认输）|对局|手动)(?: · .+)?$"
)
DATE_LINE_RE = re.compile(r"^- 日期：(\d{4}-\d{2}-\d{2})\s*$", re.M)
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
QUESTION_FIELDS = (("byDifficulty", "difficulty", "难度"), ("byType", "question_type", "题型"),
                   ("byCognitive", "cognitive_level", "认知层级"))
VULN_LIMIT = 20
ACTIVITY_LIMIT = 8


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def file_date(path: Path, text: str) -> str | None:
    """正文「- 日期：」优先，没有就取文件名开头的日期。"""
    m = DATE_LINE_RE.search(text)
    value = m.group(1) if m else path.name[:10]
    return value if valid_date(value) else None


def file_seq(path: Path) -> int:
    """同日同名文件的序号：无后缀为 1，`-2` 为 2，用来给同一天的记录排先后。"""
    m = re.search(r"-(\d+)$", path.stem)
    return int(m.group(1)) if m else 1


def load_jsonl(path: Path, rel: str, skipped: list[str]) -> list[tuple[int, dict]] | None:
    """读登记表，文件不存在返回 None；坏行进 skipped。"""
    if not path.is_file():
        return None
    rows = []
    for n, line in enumerate(read(path).splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            skipped.append(f"{rel} 第 {n} 行：不是合法 JSON")
            continue
        if not isinstance(rec, dict):
            skipped.append(f"{rel} 第 {n} 行：不是 JSON 对象")
            continue
        rows.append((n, rec))
    return rows


class Concept:
    def __init__(self, cid: str, name: str, ctype: str, state: str, deps: list[str], line: int):
        self.cid, self.name, self.ctype, self.state, self.deps, self.line = cid, name, ctype, state, deps, line


def parse_concepts(text: str, rel: str, skipped: list[str]) -> tuple[list[Concept], set[str]]:
    """切 concepts.md 条目，返回解析成功的条目和标题里出现过的全部 id。"""
    concepts: list[Concept] = []
    seen: set[str] = set()
    # 一个条目从「### 」标题行到下一个 ## 或 ### 标题为止
    for block in re.finditer(r"^### .*?(?=^##|\Z)", text, re.M | re.S):
        line = text.count("\n", 0, block.start()) + 1
        head = block.group(0).split("\n", 1)[0].rstrip()
        seen.update(HEAD_ID_RE.findall(head))
        m = TITLE_RE.match(head)
        if not m:
            skipped.append(f"{rel} 第 {line} 行：标题不是「### D-xxx 名称（类型）」")
            continue
        fields: dict[str, str] = {}
        for key, value in FIELD_RE.findall(block.group(0)):
            fields.setdefault(key, value.strip())
        raw = fields.get("状态")
        pending = PENDING_RE.match(raw or "")
        state = "pending" if pending and valid_date(pending.group(1)) else STATE_KEY.get(raw)
        if state is None:
            problem = "缺「- 状态：」" if raw is None else f"状态「{raw}」不是 ☐ / ☑ / ⚠ / 待复验 @ YYYY-MM-DD"
            skipped.append(f"{rel} 第 {line} 行 {m.group(1)}：{problem}")
            continue
        deps = DEP_RE.findall(fields.get("依赖", ""))
        concepts.append(Concept(m.group(1), m.group(2).strip(), m.group(3), state, deps, line))
    return concepts, seen


def build(root: Path) -> tuple[dict, list[str]]:
    """算注入 JSON；返回数据和跳过的条目。"""
    skipped: list[str] = []
    dirs = sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))
    topics = [p.name for p in dirs if (p / "concepts.md").is_file() or any((p / "drills").glob("*.md"))]
    activity: list[tuple[str, int, dict]] = []

    answers_rel = ".local/answers/index.jsonl"
    answers = load_jsonl(root / answers_rel, answers_rel, skipped)

    # 概念与依赖阻塞
    by_status = dict.fromkeys(STATUS_KEYS, 0)
    by_type: dict[str, int] = {}
    by_topic: dict[str, dict[str, int]] = {}
    blocked = []
    for topic in topics:
        path = root / topic / "concepts.md"
        if not path.is_file():
            continue
        rel = f"{topic}/concepts.md"
        entries, seen = parse_concepts(read(path), rel, skipped)
        state = {c.cid: c.state for c in entries}
        name = {c.cid: c.name for c in entries}
        for c in entries:
            by_status[c.state] += 1
            by_type[c.ctype] = by_type.get(c.ctype, 0) + 1
            by_topic.setdefault(topic, dict.fromkeys(STATUS_KEYS, 0))[c.state] += 1
        for c in entries:
            if c.state not in ("pending", "misconceived"):
                continue
            missing = []
            for dep in c.deps:
                if dep in state:
                    if state[dep] != "mastered":
                        missing.append(name[dep])
                elif dep not in seen:
                    skipped.append(f"{rel} 第 {c.line} 行 {c.cid}：依赖 {dep} 不在清单里，阻塞判断不算它")
            if missing:
                blocked.append({"concept": c.name, "missing": missing})
    concepts = {"byStatus": by_status, "byType": by_type, "byTopic": by_topic} if by_topic else None

    # 对局
    drills = {"total": 0, "passed": 0, "surrendered": 0, "open": 0, "byTopic": {}}
    for topic in topics:
        for f in sorted((root / topic / "drills").glob("*.md")):
            rel = f"{topic}/drills/{f.name}"
            text = read(f)
            m = DRILL_RE.match(text.split("\n", 1)[0])
            if not m:
                skipped.append(f"{rel}：首行不是 <!-- arc-drill: open|passed|surrendered -->")
                continue
            drills["total"] += 1
            drills[m.group(1)] += 1
            drills["byTopic"].setdefault(topic, {"passed": 0, "surrendered": 0, "open": 0})[m.group(1)] += 1
            title = DRILL_TITLE_RE.search(text)
            label = title.group(1).strip() if title else DATE_PREFIX_RE.sub("", f.stem)
            day = file_date(f, text)
            if day:
                activity.append((day, file_seq(f), {"date": day, "kind": "对局", "label": f"{topic} · {label}"}))
            else:
                skipped.append(f"{rel}：读不出日期，不进最近活动")
    if not drills["total"]:
        drills = None

    # 问答场次，只进最近活动
    for topic in topics:
        for f in sorted((root / topic / "concept-sessions").glob("*.md")):
            text = read(f)
            names: dict[str, str] = {}
            for line in text.splitlines():
                m = QUESTION_RE.match(line.rstrip())
                if m:
                    names.setdefault(m.group(1), m.group(2).strip())
            if not names:
                continue
            day = file_date(f, text)
            if not day:
                skipped.append(f"{topic}/concept-sessions/{f.name}：读不出日期，不进最近活动")
                continue
            shown = list(names.values())
            label = f"{topic} · " + "、".join(shown[:2]) + (f" 等 {len(shown)} 个概念" if len(shown) > 2 else "")
            activity.append((day, file_seq(f), {"date": day, "kind": "概念问答", "label": label}))

    # 出题统计与出题活动
    questions = None
    if answers:
        questions = {"total": len(answers), "byDifficulty": {}, "byType": {}, "byCognitive": {}}
        for n, rec in answers:
            for key, field, label in QUESTION_FIELDS:
                value = rec.get(field)
                if isinstance(value, str) and value.strip():
                    questions[key][value] = questions[key].get(value, 0) + 1
                else:
                    skipped.append(f"{answers_rel} 第 {n} 行：缺 {field}，不计入{label}分布")
            day = str(rec.get("date", ""))
            if not valid_date(day):
                skipped.append(f"{answers_rel} 第 {n} 行：日期不合法，不进最近活动")
                continue
            problem = DATE_PREFIX_RE.sub("", Path(str(rec.get("problem_file") or "")).stem)
            label = " · ".join(x for x in (str(rec.get("topic") or ""), problem) if x) or "出题"
            activity.append((day, n, {"date": day, "kind": "出题", "label": label}))

    # 漏洞
    vulns: list[tuple[str, int, dict]] = []
    has_gaps_file = False
    for topic in topics:
        path = root / topic / "gaps.md"
        if not path.is_file():
            continue
        has_gaps_file = True
        rel = f"{topic}/gaps.md"
        lines = read(path).splitlines()
        start = next((i for i, line in enumerate(lines) if line.strip() == "## 条目"), None)
        if start is None:
            skipped.append(f"{rel}：缺「## 条目」标题，整份没读")
            continue
        for i in range(start + 1, len(lines)):
            line = lines[i].rstrip()
            if line.startswith("## "):
                break
            if not line.strip():
                continue
            m = GAP_RE.match(line)
            if not m or not valid_date(m["date"]):
                skipped.append(f"{rel} 第 {i + 1} 行：不是「- 描述 [D-xxx] @ 日期 · 来源 · 原文件」格式")
                continue
            gid, day = m["id"], m["date"]
            redone = bool(gid and answers and any(
                rec.get("topic") == topic and isinstance(rec.get("topics"), list)
                and gid in rec["topics"] and str(rec.get("date", "")) >= day
                for _, rec in answers))
            item = {"desc": m["desc"]}
            if gid:
                item["id"] = gid
            item.update({"date": day, "source": m["source"], "rePracticed": redone})
            vulns.append((day, i, item))
    vulns.sort(key=lambda v: (v[0], v[1]), reverse=True)
    vuln_counts = None
    if has_gaps_file:
        vuln_counts = {"total": len(vulns), "open": sum(1 for v in vulns if not v[2]["rePracticed"])}
    activity.sort(key=lambda a: (a[0], a[1]), reverse=True)

    # 下一步提示用的材料数
    guidance = None
    note_dirs = [d / "notes" for d in dirs if (d / "notes").is_dir()]
    if note_dirs:
        distill_rel = ".local/distill-index.jsonl"
        registered = {rec.get("material") for _, rec in load_jsonl(root / distill_rel, distill_rel, skipped) or []}
        products = [p.relative_to(root).as_posix() for d in note_dirs for p in sorted(d.glob("*.md"))]
        guidance = {"materials": len(products), "distillable": sum(1 for p in products if p not in registered)}

    data = {
        "generated": date.today().isoformat(),
        "topics": topics,
        "concepts": concepts,
        "drills": drills,
        "vulnerabilities": [v[2] for v in vulns[:VULN_LIMIT]],
        "vulnerabilityCounts": vuln_counts,
        "activity": [a[2] for a in activity[:ACTIVITY_LIMIT]],
        "blocked": blocked,
        "questions": questions,
        "guidance": guidance,
    }
    return data, skipped


def modules(data: dict) -> tuple[list[str], list[str]]:
    """渲染与省略的模块，显示条件与模板一致。"""
    c, d, q, vc = data["concepts"], data["drills"], data["questions"], data["vulnerabilityCounts"]
    rows = (
        ("概念掌握", c and f"{sum(c['byStatus'].values())} 个考点", "没有可用的 concepts.md 条目"),
        ("考点类型", c and f"{len(c['byType'])} 类", "没有可用的 concepts.md 条目"),
        ("解题对局", d and f"{d['total']} 场", "没有可用的对局文件"),
        ("漏洞清单", data["vulnerabilities"] and f"{vc['total']} 条，待重练 {vc['open']} 条", "没有可用的 gaps.md 条目"),
        ("最近活动", data["activity"] and f"{len(data['activity'])} 条", "没有对局、问答或出题记录"),
        ("依赖阻塞", data["blocked"] and f"{len(data['blocked'])} 个概念", "没有被前置卡住的待复验或有误解概念"),
        ("出题统计", q and f"{q['total']} 题", "没有可读的 .local/answers/index.jsonl 记录"),
    )
    shown = [f"{name}（{summary}）" for name, summary, _ in rows if summary]
    omitted = [f"{name}（{why}）" for name, summary, why in rows if not summary]
    return shown, omitted


def main() -> None:
    parser = argparse.ArgumentParser(description="按数据契约生成 arc-dashboard 的 dashboard.html")
    parser.add_argument("root", nargs="?", default=".", help="学习仓库根，默认当前目录")
    parser.add_argument("--out", help="产物路径，默认 仓库根/dashboard.html")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"❌ 仓库根不存在：{root}")
        sys.exit(2)
    template = read(TEMPLATE) if TEMPLATE.is_file() else ""
    tag = DATA_TAG.search(template)
    if template.count(SLOT) != 1 or not tag or tag.group(1).strip() != SLOT:
        print(f"❌ 模板 {TEMPLATE} 不存在，或注入槽不是数据块里唯一的一行")
        sys.exit(1)

    data, skipped = build(root)
    # 转义 <，JSON 里的 </script> 就截不断注入块
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    out = Path(args.out).expanduser().resolve() if args.out else root / "dashboard.html"
    out.write_text(template.replace(SLOT, payload), encoding="utf-8")

    shown, omitted = modules(data)
    print(f"产物：{out}")
    print(f"课题：{'、'.join(data['topics']) or '无'}")
    print(f"渲染：{'、'.join(shown) or '无'}")
    print(f"省略：{'、'.join(omitted) or '无'}")
    if not shown:
        print("所有数据模块都为空，页面显示「从第一份材料开始」引导页；先用 /arc-materials、/arc-distill 造数据。")
    if skipped:
        print(f"跳过 {len(skipped)} 条，未计入：")
        for line in skipped:
            print(f"  - {line}")


if __name__ == "__main__":
    main()
