# /// script
# requires-python = ">=3.9"
# dependencies = ["requests"]
# ///
"""MinerU 云解析一条龙：token 校验、上传、轮询、下载解压。

用法：uv run mineru_run.py 源.pdf [更多.pdf ...]，--ping 只验 token 不产生任务。
token 从 .local/mineru-token 沿目录向上找，600 权限，git 忽略。
缺失时按 skill 第 0 步向用户要 key，明文不进任何输出。
上传请求不能带 Content-Type，OSS 预签名对此敏感，urllib 和 curl -F 会 403。
"""

import argparse
import hashlib
import pathlib
import re
import sys
import time
import zipfile

import requests

API = "https://mineru.net/api/v4"


def find_token(explicit: str | None) -> pathlib.Path:
    if explicit:
        p = pathlib.Path(explicit)
        if not p.exists():
            sys.exit(f"token 文件不存在: {p}")
        return p
    for parent in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents]:
        p = parent / ".local/mineru-token"
        if p.exists():
            return p
    sys.exit("找不到 .local/mineru-token：按 skill 第 0 步向用户要 key，写入 chmod 600 后重试")


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def ping(token: str) -> None:
    r = requests.post(f"{API}/file-urls/batch", headers=headers(token),
                      json={"files": [{"name": "ping.pdf"}]}, timeout=60)
    resp = r.json()
    if resp.get("code") == 0:
        print("token 有效")
        return
    sys.exit(f"token 无效：{resp.get('msg')}（HTTP {r.status_code}）")


def slugify(stem: str, idx: int) -> str:
    ascii_part = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-")
    digest = hashlib.sha256(stem.encode()).hexdigest()[:8]
    return f"{ascii_part}-{digest}" if ascii_part else f"doc{idx + 1}-{digest}"


def upload_and_wait(token: str, files: list[pathlib.Path], args) -> None:
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # html 须用 MinerU-HTML 模型版本，与其余格式分开提交
    html_files = [f for f in files if f.suffix.lower() in (".html", ".htm")]
    other_files = [f for f in files if f not in html_files]
    batches = []
    if other_files:
        batches.append((other_files, args.model_version))
    if html_files:
        batches.append((html_files, "MinerU-HTML"))
    for group, model in batches:
        run_batch(token, group, model, args, out)


def run_batch(token: str, files: list[pathlib.Path], model_version: str, args, out: pathlib.Path) -> None:
    ids = [slugify(f.stem, i) for i, f in enumerate(files)]
    for did, f in zip(ids, files):
        print(f"{did} <- {f}（模型 {model_version}）")
    if len(set(ids)) != len(ids):
        sys.exit("data_id 撞名，检查输入文件")

    # 文件名保留真实后缀，MinerU 按后缀识别格式，伪造 .pdf 会导致解析失败
    body = {
        "model_version": model_version,
        "language": args.language,
        "files": [{"name": f.name, "data_id": did} for did, f in zip(ids, files)],
    }
    r = requests.post(f"{API}/file-urls/batch", headers=headers(token), json=body, timeout=60)
    resp = r.json()
    if resp.get("code") != 0:
        sys.exit(f"申请上传地址失败：{resp.get('msg')}")
    batch_id = resp["data"]["batch_id"]

    for (did, path), url in zip([(d, p) for d, p in zip(ids, files)], resp["data"]["file_urls"]):
        data = path.read_bytes()
        put = requests.put(url, data=data, timeout=300)
        print(f"{did} 上传 {len(data)} 字节 -> HTTP {put.status_code}")
        if put.status_code >= 400:
            sys.exit(f"上传失败 {did}: {put.text[:300]}\n上传头不能带 Content-Type，用本脚本别换 urllib 或 curl -F")

    deadline = time.time() + args.timeout
    while time.time() < deadline:
        r = requests.get(f"{API}/extract-results/batch/{batch_id}", headers=headers(token), timeout=60)
        results = r.json()["data"]["extract_result"]
        states = {x["data_id"]: x["state"] for x in results}
        print(time.strftime("%H:%M:%S"), states, flush=True)
        if all(s in ("done", "failed") for s in states.values()):
            break
        time.sleep(args.interval)
    else:
        sys.exit(f"轮询超时（{args.timeout}s），batch_id={batch_id} 可稍后手动查")

    failed = False
    for x in results:
        did = x["data_id"]
        if x["state"] != "done":
            print(f"{did} 解析失败：{x.get('err_msg')}")
            failed = True
            continue
        zpath = out / f"{did}.zip"
        zpath.write_bytes(requests.get(x["full_zip_url"], timeout=300).content)
        target = out / did
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(target)
        cl = next(p for p in sorted(target.glob("*_content_list.json")) if not p.name.endswith("_v2.json"))
        print(f"{did} 下载 {zpath.stat().st_size} 字节 -> {target}/")
        print(f"  content_list: {cl}")
    if failed:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="MinerU 云解析一条龙（pdf/ppt/pptx/doc/docx/图片/html）")
    parser.add_argument("files", nargs="*", help="一个或多个文件，html 自动走 MinerU-HTML")
    parser.add_argument("--ping", action="store_true", help="只验 token")
    parser.add_argument("--out", default="/tmp/mineru-out")
    parser.add_argument("--model-version", default="vlm")
    parser.add_argument("--language", default="ch")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--token-file", default=None)
    args = parser.parse_args()

    token = find_token(args.token_file).read_text().strip()
    if args.ping:
        ping(token)
        return
    if not args.files:
        sys.exit("没给输入文件；验 token 用 --ping")
    upload_and_wait(token, [pathlib.Path(f) for f in args.files], args)


if __name__ == "__main__":
    main()