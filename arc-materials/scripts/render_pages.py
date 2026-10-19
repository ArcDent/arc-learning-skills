# /// script
# requires-python = ">=3.9"
# dependencies = ["pymupdf"]
# ///
"""渲染 PDF 指定页为 png，供逐符号对照抽查。

用法：uv run render_pages.py 输入.pdf 3 16 17，页码从 1 起
png 路径逐行打印，供 Read 直读对照。
"""

import argparse
import pathlib

import pymupdf


def main() -> None:
    parser = argparse.ArgumentParser(description="渲染 PDF 页为 png")
    parser.add_argument("input", help="输入 PDF")
    parser.add_argument("pages", nargs="+", type=int, help="页码，从 1 起")
    parser.add_argument("--dpi", type=int, default=110)
    parser.add_argument("--out", default="/tmp/qm-pages")
    args = parser.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    src = pathlib.Path(args.input)
    if not src.exists():
        print(f"{src}: 不存在")
        raise SystemExit(2)
    stem = src.stem
    with pymupdf.open(src) as doc:
        for p in args.pages:
            if not 1 <= p <= doc.page_count:
                print(f"页码 {p} 超界（共 {doc.page_count} 页），跳过")
                continue
            f = out / f"{stem}-p{p}.png"
            doc[p - 1].get_pixmap(dpi=args.dpi).save(f)
            print(f)


if __name__ == "__main__":
    main()