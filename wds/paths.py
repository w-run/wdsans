"""路径配置中心（P72）。

## 为什么需要

此前路径硬编码散落在 16 个文件、共 21 处：
  /workspace/wdsans/ref/...       （参考字体）
  /data/build-cache/wdsans-dist   （交付产物）
  /data/build-cache/wdsans-subset（子集）
  /data/build-cache/wdsans-p1     （中间产物）

问题：
  1. 硬盘挂载点变化 / 迁移机器 → 21 处全要改
  2. 路径写死导致无法用环境变量覆盖
  3. 新增脚本容易抄错路径

## 设计

所有路径集中在本模块，按优先级取值：
  1. 环境变量（WDSANS_ROOT / WDSANS_CACHE 等）
  2. 默认值（当前部署的实际情况）

用法：
  from wds.paths import REF_DIR, DIST_DIR, SUBSET_DIR, P1_DIR
"""
from __future__ import annotations
import os

# ---- 根目录（可用环境变量覆盖）----

# 代码与参考字体所在（SSD，默认 /workspace/wdsans）
ROOT = os.environ.get("WDSANS_ROOT", "/workspace/wdsans")

# 构建产物缓存（HDD，体积大，默认 /data/build-cache）
CACHE = os.environ.get("WDSANS_CACHE", "/data/build-cache")


# ---- 参考字体 ----

REF_DIR = os.path.join(ROOT, "ref")

#: 中文基座（Noto Sans CJK SC 可变字体）
NOTO_VF = os.path.join(REF_DIR, "NotoSansCJKsc-VF.ttf")

#: 拉丁来源（Mona Sans 可变字体）
MONA_VF = os.path.join(REF_DIR, "mona", "MonaSansVF.ttf")

#: 对照字体 OPPO Sans（400/500/700）
OPPO_DIR = os.path.join(REF_DIR, "ops")

#: 对照字体 HarmonyOS Sans（400/500/700）
HOS_DIR = os.path.join(REF_DIR, "hos")


# ---- 构建产物 ----

#: 中间产物目录（P0/P1/P2 各阶段）
P0_DIR = os.path.join(CACHE, "wdsans-p0")
P1_DIR = os.path.join(CACHE, "wdsans-p1")
P2_DIR = os.path.join(CACHE, "wdsans-p2")

#: 最终交付目录（7 档静态 + VF + README + OFL）
DIST_DIR = os.path.join(CACHE, "wdsans-dist")

#: Web 子集目录
SUBSET_DIR = os.path.join(CACHE, "wdsans-subset")

#: 母版 VF（所有静态实例与 VF 交付物的来源）
MASTER_VF = os.path.join(P1_DIR, "wdsans-FINAL.ttf")


def ensure_dirs():
    """确保所有产物目录存在（构建前调用）。"""
    for d in (P0_DIR, P1_DIR, P2_DIR, DIST_DIR, SUBSET_DIR):
        os.makedirs(d, exist_ok=True)


def summary():
    """返回路径配置摘要（供文档/日志用）。"""
    return {
        "ROOT": ROOT,
        "CACHE": CACHE,
        "NOTO_VF": NOTO_VF,
        "MONA_VF": MONA_VF,
        "MASTER_VF": MASTER_VF,
        "DIST_DIR": DIST_DIR,
        "SUBSET_DIR": SUBSET_DIR,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(summary(), indent=2, ensure_ascii=False))
    print()
    for k, v in summary().items():
        mark = "OK " if os.path.exists(v) else "缺失"
        print("  [%s] %-12s %s" % (mark, k, v))