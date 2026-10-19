# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""arc-materials 产物校验。

用法：uv run audit_md.py 产物.md [更多.md ...]
检查 frontmatter 七字段、页锚点、图片引用、公式配对、拆散函数名残留。
失败项逐条打印，退出码 1，全部通过为 0。rebuild_md.py 写盘前复用本文件。
"""

import argparse
import pathlib
import re
import sys

FM_FIELDS = ("source", "topic", "scope", "date", "tool", "fidelity", "hash")
FIDELITY = ("text", "ocr", "vision")

PAGE_ANCHOR = re.compile(r"<!-- p\.(\d+) -->")
SLIDE_ANCHOR = re.compile(r"^## 第 (\d+) 页", re.M)
IMG_REF = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
BLOCK_MATH = re.compile(r"\$\$(.*?)\$\$", re.S)
INLINE_MATH = re.compile(r"\$([^$\n]+)\$")
BEGIN_END = re.compile(r"\\(begin|end)\{([^}]*)\}")
LEFT = re.compile(r"\\left(?![A-Za-z])")
RIGHT = re.compile(r"\\right(?![A-Za-z])")
# VLM 把函数名拆成空格字母的残留
SPLIT_RESIDUE = re.compile(
    r"(?<![A-Za-z\\])(?:a r c t a n|a r c s i n|a r c c o s|s i n|c o s|t a n|c o t"
    r"|s e c|c s c|e x p|l n|l o g|s h|c h)(?![A-Za-z])"
)


def _latex_issues(math: str, where: str) -> list[str]:
    issues = []
    stripped = math.replace(r"\{", "").replace(r"\}", "")
    if stripped.count("{") != stripped.count("}"):
        issues.append(f"{where}: 花括号不配对（{stripped.count('{')}/{stripped.count('}')}）")
    begins = [n for k, n in BEGIN_END.findall(math) if k == "begin"]
    ends = [n for k, n in BEGIN_END.findall(math) if k == "end"]
    if sorted(begins) != sorted(ends):
        issues.append(f"{where}: 环境不配对 begin={begins} end={ends}")
    if len(LEFT.findall(math)) != len(RIGHT.findall(math)):
        issues.append(f"{where}: \\left/\\right 不配对")
    return issues


def audit_text(text: str, base_dir: pathlib.Path, allow_anchor_gaps: bool = False) -> list[str]:
    issues: list[str] = []

    # 1. frontmatter 七字段
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        issues.append("frontmatter 缺失或格式不对（应 --- 包裹）")
    else:
        fields = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fields[k.strip()] = v.strip()
        missing = [k for k in FM_FIELDS if k not in fields]
        extra = [k for k in fields if k not in FM_FIELDS]
        if missing:
            issues.append(f"frontmatter 缺字段: {missing}")
        if extra:
            issues.append(f"frontmatter 多字段: {extra}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fields.get("date", "")):
            issues.append(f"date 不是 YYYY-MM-DD: {fields.get('date')!r}")
        if not re.fullmatch(r"[0-9a-f]{16}", fields.get("hash", "")):
            issues.append(f"hash 不是 16 位十六进制: {fields.get('hash')!r}")
        if fields.get("fidelity") not in FIDELITY:
            issues.append(f"fidelity 应为 {FIDELITY} 之一: {fields.get('fidelity')!r}")
        for k in ("source", "topic", "scope", "tool"):
            if not fields.get(k):
                issues.append(f"{k} 为空")

    body = text[m.end():] if m else text

    # 2. 页锚点，有锚点才查，DOCX 产物无锚点属正常
    #    默认从 1 起连续，pdf2md 路线合法丢空白页时用 --allow-anchor-gaps 只查单调递增
    for pattern, label in ((PAGE_ANCHOR, "<!-- p.N -->"), (SLIDE_ANCHOR, "## 第 N 页")):
        nums = [int(x) for x in pattern.findall(body)]
        if not nums:
            continue
        if nums != sorted(set(nums)):
            issues.append(f"{label} 重复或乱序: {nums[:8]}…")
        elif not allow_anchor_gaps and nums != list(range(1, len(nums) + 1)):
            issues.append(f"{label} 不连续或未从 1 起: {nums[:8]}…")

    # 3. 图片引用存在
    refs = IMG_REF.findall(body)
    for ref in refs:
        target = base_dir / ref
        if not target.exists():
            issues.append(f"图片引用不存在: {ref}")

    # 4. $ 与 $$ 配对
    for i, line in enumerate(text.splitlines(), 1):
        residue = line.replace("$$", "")
        if residue.count("$") % 2:
            issues.append(f"行 {i}: 行内 $ 不配对")
    if text.count("$$") % 2:
        issues.append("$$ 块定界符不成对")

    # 5. LaTeX 结构，look-ahead 排除 \rightarrow 类误报
    def line_of(idx: int) -> int:
        return body[:idx].count("\n") + 1

    for span_m in BLOCK_MATH.finditer(body):
        issues += _latex_issues(span_m.group(1), f"正文行 {line_of(span_m.start())} 的 $$ 块")
    for span_m in INLINE_MATH.finditer(body):
        issues += _latex_issues(span_m.group(1), f"正文行 {line_of(span_m.start())} 的行内公式")

    # 6. 拆散函数名残留，跳过转写说明引用块和注释行
    for i, line in enumerate(text.splitlines(), 1):
        if line.startswith(">") or line.lstrip().startswith("<!--"):
            continue
        hit = SPLIT_RESIDUE.search(line)
        if hit:
            issues.append(f"行 {i}: 拆散函数名残留 {hit.group(0)!r}")

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="arc-materials 产物校验")
    parser.add_argument("files", nargs="+", help="一个或多个产物 .md")
    parser.add_argument("--allow-anchor-gaps", action="store_true",
                        help="pdf2md 路线合法丢空白页时用：锚点只查单调递增，不查连续")
    args = parser.parse_args()

    failed = False
    for f in args.files:
        path = pathlib.Path(f)
        if not path.exists():
            print(f"{path}: 不存在")
            failed = True
            continue
        content = path.read_text(encoding="utf-8")
        issues = audit_text(content, path.parent, args.allow_anchor_gaps)
        unrecognised = content.count("<!-- 无法辨认 -->")
        note = f"（含 {unrecognised} 处无法辨认标记）" if unrecognised else ""
        if issues:
            failed = True
            print(f"{path}: {len(issues)} 处问题{note}")
            for it in issues:
                print(f"  - {it}")
        else:
            print(f"{path}: 通过{note}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()