# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""EPUB 本地转 markdown，零依赖零上传。

用法：uv run epub2md.py 输入.epub 输出.md [--max-chapters N]

epub 被 MinerU 拒收（2026-10-14 实测 unsupported file type），pymupdf 也打不开，
故本脚本用标准库解包：按 OPF spine 顺序抽取各章 xhtml 文本，
h1-h6 映射 # 层级，p/li 转段落与列表，图片提取到输出目录 assets/ 并改写引用。
每个 spine 条目前插 <!-- p.N --> 锚点（N 从 1 起，与 audit 连续性检查兼容）。
tool 记 epub2md，fidelity 记 text。
"""

import argparse
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from pathlib import Path

NS = {
    "c": "urn:oasis:names:tc:opendocument:xmlns:container",
    "o": "http://www.idpf.org/2007/opf",
}


class _XHTMLText(HTMLParser):
    """抽 xhtml 正文：标题层级、段落、列表项、图片引用。"""

    HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._buf: list[str] = []
        self._mode: str | None = None   # 当前块类型: heading/p/li
        self._level: int = 0
        self._skip = 0                  # style/script 深度
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in ("style", "script"):
            self._skip += 1
            return
        if self._skip:
            return
        if tag in self.HEADINGS:
            self._flush()
            self._mode, self._level = "heading", self.HEADINGS[tag]
        elif tag == "p":
            self._flush()
            self._mode = "p"
        elif tag == "li":
            self._flush()
            self._mode = "li"
        elif tag == "img":
            src = dict(attrs).get("src", "")
            if src:
                self.images.append(src)
                self._buf.append(f"![]({src})")
        elif tag == "br" and self._mode:
            self._buf.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("style", "script"):
            self._skip = max(0, self._skip - 1)
        elif tag in self.HEADINGS and self._mode == "heading":
            self._emit("#" * self._level + " ")
        elif tag == "p" and self._mode == "p":
            self._emit()
        elif tag == "li" and self._mode == "li":
            self._emit(prefix="- ")

    def handle_data(self, data: str) -> None:
        if not self._skip and self._mode:
            self._buf.append(data)

    def _flush(self) -> None:
        if self._mode == "heading":
            self._emit("#" * self._level)
        elif self._mode == "li":
            self._emit(prefix="- ")
        elif self._mode == "p":
            self._emit()
        self._mode = None

    def _emit(self, prefix: str = "") -> None:
        text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
        self._buf = []
        if text:
            self.blocks.append(f"{prefix}{text}" if prefix else text)


def _read(zipf: zipfile.ZipFile, name: str) -> bytes:
    return zipf.read(name)


def _spine_docs(zipf: zipfile.ZipFile) -> list[str]:
    """按 container.xml -> OPF -> spine 顺序返回 xhtml 条目路径。"""
    container = ET.fromstring(_read(zipf, "META-INF/container.xml"))
    rootfile = container.find(".//c:rootfile", NS)
    if rootfile is None:
        sys.exit("container.xml 里找不到 rootfile，epub 结构异常")
    opf_path = rootfile.get("full-path")
    opf_dir = posixpath.dirname(opf_path)
    opf = ET.fromstring(_read(zipf, opf_path))
    manifest = {i.get("id"): i.get("href") for i in opf.findall(".//o:item", NS)}
    docs = []
    for ref in opf.findall(".//o:itemref", NS):
        href = manifest.get(ref.get("idref"))
        if href and posixpath.splitext(href)[1].lower() in (".xhtml", ".html", ".htm"):
            docs.append(posixpath.normpath(posixpath.join(opf_dir, href)) if opf_dir else href)
    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description="EPUB 本地转 markdown（零依赖）")
    parser.add_argument("input", help="输入 .epub")
    parser.add_argument("output", help="输出 markdown 路径")
    parser.add_argument("--max-chapters", type=int, default=None,
                        help="只转前 N 章，预览用")
    args = parser.parse_args()

    out = Path(args.output)
    with zipfile.ZipFile(args.input) as zipf:
        docs = _spine_docs(zipf)
        if not docs:
            sys.exit("spine 里没有 xhtml 条目")
        if args.max_chapters:
            docs = docs[: args.max_chapters]

        parts: list[str] = []
        all_images: list[tuple[str, str]] = []  # (epub 内路径, assets 文件名)
        for n, doc in enumerate(docs, 1):
            raw = _read(zipf, doc).decode("utf-8", errors="replace")
            hp = _XHTMLText()
            hp.feed(raw)
            if not hp.blocks and not hp.images:
                continue
            body = []
            for block in hp.blocks:
                for m in re.finditer(r"!\[\]\(([^)]+)\)", block):
                    src = m.group(1)
                    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(doc), src))
                    all_images.append((resolved, Path(src).name))
                body.append(block)
            parts.append(f"<!-- p.{n} -->\n" + "\n\n".join(body))

        if not parts:
            sys.exit("没有抽到任何正文，epub 可能是纯图片版")

        images_dir = out.parent / "assets"
        images_dir.mkdir(parents=True, exist_ok=True)
        for resolved, name in all_images:
            try:
                data = _read(zipf, resolved)
            except KeyError:
                continue
            dst = images_dir / name
            if not dst.exists():
                dst.write_bytes(data)

    # 引用改写到 assets/
    markdown = "\n\n".join(parts) + "\n"
    markdown = re.sub(r"!\[\]\((?!assets/)([^)/][^)]*)\)", r"![](assets/\1)", markdown)
    # 去掉 epub 内部链接与路径前缀
    markdown = re.sub(r"!\[\]\(assets/(\.\./)*", "![](assets/", markdown)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    print(f"已写出 {out}（{len(parts)} 章，图片 {len(all_images)} 张）")


if __name__ == "__main__":
    main()
