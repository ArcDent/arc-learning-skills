# /// script
# requires-python = ">=3.9"
# dependencies = ["pymupdf4llm"]
# ///
"""PDF/EPUB 转 markdown，每页前插 <!-- p.N --> 锚点。

用法：
  uv run pdf2md.py 输入.pdf 输出.md
  uv run pdf2md.py 输入.pdf 输出.md --pages 12-30

页范围从 1 起、含两端；产物为 UTF-8 markdown。
"""

import argparse
import sys

import pymupdf
import pymupdf4llm


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF/EPUB 转 markdown（带页锚点）")
    parser.add_argument("input", help="输入文件（.pdf 或 .epub）")
    parser.add_argument("output", help="输出 markdown 路径")
    parser.add_argument("--pages", default=None, help="页范围，如 12-30（从 1 起，含两端）")
    args = parser.parse_args()

    with pymupdf.open(args.input) as doc:
        page_count = doc.page_count

    pages = None
    if args.pages:
        start, end = args.pages.split("-")
        start, end = int(start), int(end)
        if start < 1 or end > page_count or start > end:
            sys.exit(f"页范围 {start}-{end} 超界：该文件共 {page_count} 页")
        pages = list(range(start - 1, end))  # to_markdown 用 0 基页码

    if pages is None:
        pages = list(range(page_count))  # 全量时与 0 基页码一一对应

    chunks = pymupdf4llm.to_markdown(args.input, pages=pages, page_chunks=True)
    parts = [
        f"<!-- p.{src + 1} -->\n{chunk['text'].strip()}"  # 锚点保留源文件页码
        for src, chunk in zip(pages, chunks)
        if chunk["text"].strip()
    ]
    markdown = "\n\n".join(parts) + "\n"

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"已写出 {args.output}（{len(chunks)} 页）")


if __name__ == "__main__":
    main()
