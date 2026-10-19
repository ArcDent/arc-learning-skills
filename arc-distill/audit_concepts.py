#!/usr/bin/env python3
"""arc-distill 质量审计:校验课题总清单 concepts.md 的结构与原文回验。

用法:python3 audit_concepts.py <课题夹>/concepts.md <课题夹>/notes/
退出码:0 全部通过(可含警告);1 存在错误;2 输入文件不存在。
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

FIELD_KEYS = ("定义", "要点", "原文", "出处", "依赖", "状态")
TYPES = ("定义", "事实", "公式", "流程", "关系")
STATES = ("☐", "☑", "⚠")
PENDING_RE = re.compile(r"^待复验 @ (\d{4}-\d{2}-\d{2})$")
ID_RE = re.compile(r"^D-\d{3,}$")
TITLE_RE = re.compile(r"^###\s+(D-\d{3,})\s+(.*)（([^（）]+)）\s*$")
CITE_RE = re.compile(r"^(.*?)\s*<!--\s*p\.(\d+)\s*-->\s*$")
ANCHOR_RE = re.compile(r"<!--\s*p\.(\d+)\s*-->")


def normalize(text: str) -> str:
    """去全部空白后比较,容忍换行与空格差异。"""
    return re.sub(r"\s+", "", text)


def valid_state(value: str) -> bool:
    """状态四值;待复验必须带合法日期,供概念问答判断隔天复验。"""
    if value in STATES:
        return True
    m = PENDING_RE.match(value)
    if not m:
        return False
    try:
        date.fromisoformat(m.group(1))
    except ValueError:
        return False
    return True


class Entry:
    def __init__(self, eid: str, name: str, etype: str, line_no: int):
        self.eid, self.name, self.etype, self.line_no = eid, name, etype, line_no
        self.fields: dict[str, list[str]] = {k: [] for k in FIELD_KEYS}
        self.points: list[str] = []

    @property
    def cites(self) -> list[str]:
        return self.fields["出处"]


def parse_entries(text: str) -> tuple[list[Entry], list[str]]:
    """把 concepts.md 切成条目;标题不合法的行进 malformed。"""
    entries: list[Entry] = []
    malformed: list[str] = []
    cur: Entry | None = None
    cur_point: str | None = None
    for idx, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        if line.startswith("### "):
            m = TITLE_RE.match(line)
            if not m:
                if "（" in line:
                    malformed.append(f"标题行格式非法(第 {idx} 行):{line}")
                else:
                    malformed.append(f"标题行缺 id 或格式非法(第 {idx} 行):{line}")
                cur = None
                continue
            cur = Entry(m.group(1), m.group(2), m.group(3), idx)
            entries.append(cur)
            cur_point = None
            continue
        if cur is None or line.startswith("## "):
            cur_point = None
            continue
        m = re.match(r"^- (定义|要点|原文|出处|依赖|状态)：(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            cur.fields[key].append(val)
            cur_point = key if key == "要点" else None
            continue
        if re.match(r"^\s{2,}- ", line) and cur_point == "要点":
            cur.points.append(re.sub(r"^\s+- ", "", line).strip())
            continue
        if line.strip() and re.match(r"^\s+", raw) and cur is not None:
            # 字段续行:归并到最近的多行字段(原文/出处)
            for key in ("原文", "出处"):
                if cur.fields.get(key):
                    cur.fields[key][-1] += line.strip()
                    break
    return entries, malformed


def load_product_map(notes_dir: Path) -> dict[str, Path]:
    """材料短名 -> 产物文件。产物名形如 YYYY-MM-DD-短名.md。"""
    mapping: dict[str, Path] = {}
    if not notes_dir.is_dir():
        return mapping
    for f in sorted(notes_dir.glob("*.md")):
        stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", f.stem)
        mapping[stem] = f
    return mapping


def product_block(product: Path, page: int | None) -> str:
    """取产物中 p.N 附近(±1 页)的文本;PPTX 产物按『第 N 页』切块。"""
    text = product.read_text(encoding="utf-8", errors="replace")
    if page is None:
        return text
    parts = ANCHOR_RE.split(text)
    # parts: [前言, N1, 块1, N2, 块2, ...]
    if len(parts) > 1:
        pages = {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}
    else:
        pages = {}
        for m in re.finditer(r"##\s*第\s*(\d+)\s*页[：:]", text):
            pages[int(m.group(1))] = ""
        if pages:  # PPTX:退化为全文匹配(页标题切块意义不大)
            return text
    if not pages:
        return text
    merged = []
    for p in (page - 1, page, page + 1):
        if p in pages:
            merged.append(pages[p])
    return "\n".join(merged)


def audit(concepts_path: Path, notes_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    if not concepts_path.is_file():
        print(f"❌ [E00] 找不到清单文件:{concepts_path}")
        sys.exit(2)

    text = concepts_path.read_text(encoding="utf-8", errors="replace")
    entries, malformed = parse_entries(text)
    errors += malformed
    if not entries and not malformed:
        errors.append("[E00] 未解析出任何条目,检查标题行是否为『### D-xxx 名称(类型)』")

    seen: dict[str, Entry] = {}
    for e in entries:
        if e.eid in seen:
            errors.append(f"[E02] 第 {e.line_no} 行 id 重复:{e.eid}({e.name}),已存在于 {seen[e.eid].line_no} 行")
        else:
            seen[e.eid] = e
        for key in FIELD_KEYS:
            if key in ("依赖", "要点"):
                continue  # 依赖允许留空;要点单独查子项
            vals = e.fields[key]
            if not vals or not any(v.strip() for v in vals):
                errors.append(f"[E03] {e.eid} {e.name}:缺少字段「{key}」")
        if not e.points:
            errors.append(f"[E04] {e.eid} {e.name}:要点下没有可检验要点子项")
        if e.etype not in TYPES:
            errors.append(f"[E01] {e.eid} {e.name}:类型「{e.etype}」不在五类口径内")
        if e.fields["状态"] and not valid_state(e.fields["状态"][0]):
            errors.append(
                f"[E07] {e.eid} {e.name}:状态「{e.fields['状态'][0]}」不合法,"
                "应为 ☐ / ☑ / ⚠ / 待复验 @ YYYY-MM-DD"
            )

    # 出处与原文回验
    products = load_product_map(notes_dir)
    if not products:
        warns.append("[W02] notes/ 下未找到产物文件,跳过原文回验")
    for e in entries:
        for dep_raw in e.fields["依赖"]:
            for dep in re.split(r"[,，\s]+", dep_raw.strip()):
                dep = dep.strip()
                if not dep:
                    continue
                if dep == e.eid:
                    errors.append(f"[E06] {e.eid}:依赖引用自身")
                elif dep not in seen:
                    errors.append(f"[E06] {e.eid} {e.name}:依赖 {dep} 不存在于本清单(悬空依赖)")
        if not products:
            continue
        quote = normalize(e.fields["原文"][0]) if e.fields["原文"] else ""
        if not quote:
            continue
        if quote == normalize("（缺失）") or quote == "(缺失)":
            warns.append(f"[W03] {e.eid} {e.name}:原文为缺失占位,未回验")
            continue
        for cite in e.cites:
            m = CITE_RE.match(cite)
            short = m.group(1).strip() if m else cite.strip()
            page = int(m.group(2)) if m else None
            product = products.get(short)
            if product is None:
                hit = next((v for k, v in products.items() if short in k or k in short), None)
                if hit is None:
                    warns.append(f"[W02] {e.eid}:找不到材料「{short}」对应的产物文件")
                    continue
                product = hit
            block = product_block(product, page)
            if page is None:
                warns.append(f"[W01] {e.eid}:出处缺页锚点 <!-- p.N -->(对全文回验)")
            if normalize(quote) not in normalize(block):
                errors.append(
                    f"[E05] {e.eid} {e.name}:原文回验未命中(材料「{short}」"
                    f"{'p.' + str(page) if page else '全文'} 附近)"
                )
    return errors, warns


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    errors, warns = audit(Path(sys.argv[1]), Path(sys.argv[2]))
    for line in errors:
        print(f"❌ {line}")
    for line in warns:
        print(f"⚠️  {line}")
    total = len(errors)
    print(f"\n审计完成:错误 {total} 项,警告 {len(warns)} 项")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()