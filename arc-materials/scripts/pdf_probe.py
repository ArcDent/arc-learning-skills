# /// script
# requires-python = ">=3.9"
# dependencies = ["pymupdf"]
# ///
"""PDF 文本层探针，给 arc-materials 回退路由建议。

用法：uv run pdf_probe.py 输入.pdf [更多.pdf ...]
输出页数、每页均字、图片数、可疑字符占比和回退路由建议。
pdf 按路由表默认走 MinerU；本脚本只在 MinerU 不可用或用户拒绝传云时跑，
给出两档回退建议：pdf2md 文本层可用，model-read 无文本层。
文件打不开时退出码 2，正常为 0。
"""

import argparse
import pathlib
import sys

import pymupdf

# 数学斜体常被 PDF 编码进阿拉伯等区块，白名单外的非 ASCII 记为可疑
RANGES = (
    (0x20, 0x7E),      # ASCII 可打印
    (0x00A0, 0x024F),  # 拉丁补充与扩展
    (0x0370, 0x04FF),  # 希腊、西里尔
    (0x2000, 0x27BF),  # 通用标点、上标、箭头、数学、几何、杂项符号
    (0x2E80, 0x9FFF),  # CJK 部首、标点、汉字
    (0xF900, 0xFAFF),  # CJK 兼容
    (0xFE30, 0xFE4F),  # CJK 兼容形式
    (0xFF00, 0xFFEF),  # 全角形式
)


def suspicious_stats(text: str) -> tuple[int, int]:
    """返回可疑字符数和非空白字符总数。"""
    chars = [c for c in text if not c.isspace()]
    sus = sum(1 for c in chars if not any(lo <= ord(c) <= hi for lo, hi in RANGES))
    return sus, len(chars)


def probe(path: pathlib.Path) -> tuple[str, str]:
    with pymupdf.open(path) as doc:
        pages = doc.page_count
        char_total = 0
        images = 0
        sus = 0
        nonspace = 0
        for page in doc:
            t = page.get_text()
            char_total += len(t.strip())
            images += len(page.get_images())
            s, n = suspicious_stats(t)
            sus += s
            nonspace += n
    avg = char_total / pages if pages else 0
    ratio = sus / nonspace if nonspace else 0.0
    if avg < 40:
        route = "model-read"
        why = f"每页均字 {avg:.0f}，无文本层（扫描件/图片型）"
    elif sus >= 10 and ratio >= 0.005:
        route = "pdf2md"
        why = f"可疑字符 {sus} 个（{ratio:.1%}），文本层有失真，建议 pdf2md 并对照抽查公式"
    else:
        route = "pdf2md"
        why = f"可疑字符 {sus} 个（{ratio:.1%}），文本层可用"
    return (
        f"{path.name}\n"
        f"  页数 {pages} | 每页均字 {avg:.0f} | 图片 {images} | 可疑字符 {sus}（{ratio:.1%}）\n"
        f"  路由建议: {route} —— {why}"
    ), route


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF 文本层探针与路由建议")
    parser.add_argument("files", nargs="+", help="一个或多个 PDF")
    args = parser.parse_args()

    bad = 0
    for f in args.files:
        path = pathlib.Path(f)
        if not path.exists():
            print(f"{path}: 不存在")
            bad += 1
            continue
        try:
            text, _ = probe(path)
        except Exception as e:  # noqa: BLE001
            print(f"{path.name}: 打不开（{e}）")
            bad += 1
            continue
        print(text)
    sys.exit(2 if bad else 0)


if __name__ == "__main__":
    main()