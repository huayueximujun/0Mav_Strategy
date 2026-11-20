# -*- coding: utf-8 -*-
"""通过 GitHub API 直接推送整个仓库（git trees API，单次提交全部文件）"""
import os
import sys
import json
import base64
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
OWNER, REPO = "huayueximujun", "0Mav_Strategy"
BRANCH = "main"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"

TOKEN = os.environ.get("GH_TOKEN", "").strip()
if not TOKEN:
    sys.exit("缺少 GH_TOKEN 环境变量")

H = {"Authorization": f"Bearer {TOKEN}",
     "Accept": "application/vnd.github+json",
     "Content-Type": "application/json"}

TEXT_EXT = {".py", ".md", ".csv", ".html", ".txt", ".json", ".gitignore", ""}

def collect_files():
    """收集全部受版本管理的文件（排除 .git）"""
    out = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(".git/") or rel == ".gitignore" and False:
            continue
        if rel == ".gitignore":
            out.append((rel, p)); continue
        out.append((rel, p))
    return out

def build_tree_entry(rel: str, p: Path):
    raw = p.read_bytes()
    if p.suffix.lower() in TEXT_EXT or p.name == ".gitignore":
        try:
            return {"path": rel, "mode": "100644", "type": "blob",
                    "content": raw.decode("utf-8"), "encoding": "utf-8"}
        except UnicodeDecodeError:
            pass
    return {"path": rel, "mode": "100644", "type": "blob",
            "content": base64.b64encode(raw).decode(), "encoding": "base64"}

def main():
    files = collect_files()
    print(f"收集到 {len(files)} 个文件")

    tree = [build_tree_entry(rel, p) for rel, p in files]
    payload_size = len(json.dumps({"tree": tree}))
    print(f"tree 请求体大小: {payload_size/1e6:.2f} MB")

    # 1. 创建 tree（空仓库无父提交，直接建根 tree）
    r = requests.post(f"{API}/git/trees", headers=H, json={"tree": tree}, timeout=180)
    if r.status_code >= 300:
        sys.exit(f"创建 tree 失败 {r.status_code}: {r.text[:400]}")
    tree_sha = r.json()["sha"]
    print(f"tree 创建成功: {tree_sha[:12]}")

    # 2. 创建 commit
    r = requests.post(f"{API}/git/commits", headers=H, timeout=180,
                      json={"message": "AMV 择时策略：信号验证、位置分层、跨市场检验与回测框架\n\n"
                                       "- 主策略：AMV 单日 >=+4% 入场 / 持 20 交易日 / 止损 -3% / T+1 开盘买\n"
                                       "- 创业板 2016-2026：年化 12.88%，Sharpe 0.82，回撤 -26.4%，仓位 28%\n"
                                       "- 含版本演进史（VERSIONS.md）、业绩总览（PERFORMANCE.md）、代理指标\n"
                                       "- 注意：legacy/ 内原始脚本含已知回测 bug，数字不可引用",
                             "tree": tree_sha,
                             "parents": []})
    if r.status_code >= 300:
        sys.exit(f"创建 commit 失败 {r.status_code}: {r.text[:400]}")
    commit_sha = r.json()["sha"]
    print(f"commit 创建成功: {commit_sha[:12]}")

    # 3. 创建分支引用 main
    r = requests.post(f"{API}/git/refs", headers=H, timeout=180,
                      json={"ref": f"refs/heads/{BRANCH}", "sha": commit_sha})
    if r.status_code >= 300:
        # 若分支已存在则强制更新
        r = requests.patch(f"{API}/git/refs/heads/{BRANCH}", headers=H, timeout=180,
                           json={"sha": commit_sha, "force": True})
        if r.status_code >= 300:
            sys.exit(f"更新分支失败 {r.status_code}: {r.text[:400]}")
    print(f"分支 {BRANCH} 已指向 {commit_sha[:12]}")
    print("\n完成！仓库地址：https://github.com/huayueximujun/0Mav_Strategy")

if __name__ == "__main__":
    main()
