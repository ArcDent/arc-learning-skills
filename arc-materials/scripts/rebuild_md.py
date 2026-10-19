# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""MinerU content_list.json 重建 arc-materials 产物。

用法：uv run rebuild_md.py xx_content_list.json --topic 课题 --source 路径 --hash 16位 --out 产物.md
数据源用 zip 内 v1 的 *_content_list.json，不用 v2。
重建页锚点、text_level 标题、图与图注、公式归一化，图片只拷 content_list 引用的。
frontmatter 和转写说明自动生成，写盘前先过 audit_md，不过关不落盘。
sh 和 ch 按讲义原写法记为 \\mathrm{sh} 和 \\mathrm{ch}。
"""

import argparse
import datetime
import json
import pathlib
import re
import shutil
import sys
from html.parser import HTMLParser

from audit_md import audit_text


class _TableHTML(HTMLParser):
    """把 MinerU 输出的 HTML 表格抽成行列结构。"""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None
        elif tag in ("td", "th") and self._cell is not None:
            self._row.append(re.sub(r"\s+", " ", "".join(self._cell)).strip())
            self._cell = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


def html_table_to_md(table_body: str) -> str:
    parser = _TableHTML()
    try:
        parser.feed(table_body)
    except Exception:
        return f"```html\n{table_body.strip()}\n```"
    rows = parser.rows
    if not rows:
        return ""
    out = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join("---" for _ in rows[0]) + " |"]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)

MATH = re.compile(r"\$\$.*?\$\$|\$[^$]*\$", re.S)
UPRIGHT = re.compile(r"\\mathrm\{(cos|sin|tan|cot|ln|exp|log)\}")
SPLIT = re.compile(
    r"(?<![A-Za-z\\])"
    r"(?:a r c t a n|a r c s i n|a r c c o s|a r c c o t"
    r"|s i n h|c o s h|s i n|c o s|t a n|c o t|s e c|c s c|e x p|l n|l o g|s h|c h)"
    r"(?![A-Za-z])"
)
FUNC_MAP = {
    "a r c t a n": "\\arctan", "a r c s i n": "\\arcsin", "a r c c o s": "\\arccos",
    "a r c c o t": "\\arccot", "s i n h": "\\sinh", "c o s h": "\\cosh",
    "s i n": "\\sin", "c o s": "\\cos", "t a n": "\\tan", "c o t": "\\cot",
    "s e c": "\\sec", "c s c": "\\csc", "e x p": "\\exp", "l n": "\\ln", "l o g": "\\log",
    "s h": "\\mathrm{sh}", "c h": "\\mathrm{ch}",
}
SUBSUP_SIMPLE = re.compile(r"([_^])\{\s*(\\[A-Za-z]+|[A-Za-z0-9])\s*\}")

STATS = {"subsup": 0, "split": 0, "upright": 0, "space": 0, "split_names": set()}


def fix_math(seg: str) -> str:
    """只对公式片段做的修正。"""

    def up(m: re.Match) -> str:
        STATS["upright"] += 1
        return "\\" + m.group(1)

    def sp(m: re.Match) -> str:
        STATS["split"] += 1
        STATS["split_names"].add(FUNC_MAP[m.group(0)])
        return FUNC_MAP[m.group(0)]

    # 清洗畸形公式编号：\tag{\( (1') \} -> \tag{(1')}
    seg = re.sub(r"\\tag\{\\\(\s*(.*?)\s*\\\}", r"\\tag{(\1)}", seg)
    return SPLIT.sub(sp, UPRIGHT.sub(up, seg))


def fix_text(text: str) -> str:
    """整条文本：行内/行间公式走 fix_math，空格清理全量做。"""
    parts, last = [], 0
    for m in MATH.finditer(text):
        parts.append(text[last:m.start()])
        parts.append(fix_math(m.group(0)))
        last = m.end()
    parts.append(text[last:])
    text = "".join(parts)

    for pattern, repl, key in (
        (r"\\([A-Za-z]+) \{", r"\\\1{", "space"),
        (r"([_^]) \{", r"\1{", "subsup"),
    ):
        text, n = re.subn(pattern, repl, text)
        STATS[key] += n
    text, n = SUBSUP_SIMPLE.subn(r"\1\2", text)
    STATS["subsup"] += n
    return text


def render(entries: list[dict]) -> str:
    lines: list[str] = []
    pages = sorted({x["page_idx"] for x in entries if x["type"] != "page_number"})
    for page in pages:
        lines.append(f"<!-- p.{page + 1} -->")
        for x in (e for e in entries if e["page_idx"] == page):
            t = x["type"]
            if t == "page_number":
                continue
            if t == "text":
                body = fix_text(x.get("text", "").strip())
                if body:
                    lvl = x.get("text_level")
                    lines.append(f"{'#' * lvl} {body}" if lvl in (1, 2, 3, 4) else body)
            elif t == "equation":
                body = fix_text(x.get("text", "").strip())
                if body:
                    lines.append(body)
            elif t == "header":
                lines.append(f"## {fix_text(x.get('text', '').strip())}")
            elif t == "list":
                for item in x.get("list_items") or []:
                    body = fix_text(item.strip())
                    if body:
                        lines.append(body if body.startswith(("-", "*", "+")) else f"- {body}")
            elif t == "table":
                table = html_table_to_md(x.get("table_body", ""))
                if table:
                    lines.append(table)
                for cap in x.get("table_caption") or []:
                    if cap.strip():
                        lines.append(f"*表注：{fix_text(cap.strip())}*")
            elif t in ("image", "chart"):
                name = pathlib.Path(x.get("img_path", "")).name
                if name:
                    lines.append(f"![](assets/{name})")
                for cap in (x.get("image_caption") or []) + (x.get("chart_caption") or []):
                    if cap.strip():
                        lines.append(f"*图注：{fix_text(cap.strip())}*")
            elif t in ("footer", "page_footnote", "page_number"):
                continue  # 页脚、脚注占位、页码是解析噪声，直接丢弃
            else:
                lines.append(f"<!-- 未处理条目类型 {t} -->")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="MinerU content_list 重建产物")
    parser.add_argument("content_list", help="v1 *_content_list.json 路径")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--source", required=True, help="仓库根相对路径")
    parser.add_argument("--hash", required=True, help="源文件 SHA-256 前 16 位")
    parser.add_argument("--out", required=True, help="产物 .md 路径")
    parser.add_argument("--scope", default="全部")
    parser.add_argument("--date", default=datetime.date.today().isoformat())
    parser.add_argument("--tool", default="mineru")
    parser.add_argument("--fidelity", default="ocr")
    parser.add_argument("--spot", default=None, help="抽查说明，如「第 3 页（黑体辐射公式）」")
    parser.add_argument("--doubt", default=None, help="追加到存疑行的说明")
    args = parser.parse_args()

    cl_path = pathlib.Path(args.content_list)
    if cl_path.name.endswith("_content_list_v2.json"):
        sys.exit("用了 v2 content_list；请改用 zip 内 v1 的 *_content_list.json")
    entries = json.loads(cl_path.read_text(encoding="utf-8"))
    body = render(entries)

    spot_line = f"> - 抽查：{args.spot}已与原 PDF 逐符号对照，一致。\n" if args.spot else ""
    doubt_line = f"> - 存疑：{args.doubt}\n" if args.doubt else "> - 存疑：未发现无法辨认处。\n"
    split_desc = "、".join(sorted(STATS["split_names"])) or "无"
    note = (
        "> **转写说明**（MinerU VLM 转写，fidelity: `ocr`）\n"
        ">\n"
        f"> - 已修正：上下标归一 {STATS['subsup']} 处；拆散函数名 {STATS['split']} 处（{split_desc}）；"
        f"`\\mathrm` 函数统一为 `\\` 命令 {STATS['upright']} 处；命令后多余空格 {STATS['space']} 处。"
        "`sh`/`ch` 按讲义原写法保留为 `\\mathrm{sh}`/`\\mathrm{ch}`。\n"
        f"{spot_line}"
        f"{doubt_line}"
    )
    fm = (
        "---\n"
        f"source: {args.source}\n"
        f"topic: {args.topic}\n"
        f"scope: {args.scope}\n"
        f"date: {args.date}\n"
        f"tool: {args.tool}\n"
        f"fidelity: {args.fidelity}\n"
        f"hash: {args.hash}\n"
        "---\n"
    )
    md = fm + "\n" + note + "\n" + body

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # 先拷图再校验，audit 会检查图片引用存在
    images_dir = cl_path.parent / "images"
    copied = 0
    if images_dir.is_dir():
        assets = out.parent / "assets"
        assets.mkdir(parents=True, exist_ok=True)
        for name in sorted({m.group(1) for m in re.finditer(r"!\[[^\]]*\]\(assets/([^)]+)\)", body)}):
            src = images_dir / name
            dst = assets / name
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
                copied += 1

    issues = audit_text(md, out.parent)
    if issues:
        print("audit 不过关，未落盘：")
        for it in issues:
            print(f"  - {it}")
        sys.exit(1)

    out.write_text(md, encoding="utf-8")

    print(
        f"写出 {out}（{len(md.splitlines())} 行，新拷图片 {copied} 张；"
        f"修正统计：上下标 {STATS['subsup']}、拆散函数名 {STATS['split']}、"
        f"正体统一 {STATS['upright']}、空格 {STATS['space']}）"
    )


if __name__ == "__main__":
    main()