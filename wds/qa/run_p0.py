"""P0 全闸门验证：在试验田上跑 G1/G2/G5。"""
from __future__ import annotations
import os
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, "/workspace/wdsans")
from wds.base import SRC, rebase_axis
from wds import delta as D
from wds.qa import gates

OUTDIR = "/data/build-cache/wdsans-p0"


def build_identity(dst):
    f = TTFont(SRC)
    f = rebase_axis(f)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    f.save(dst)
    return dst


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    ident = os.path.join(OUTDIR, "identity.ttf")

    print("== 构建 identity（重设轴，delta 不动）==", flush=True)
    build_identity(ident)
    print(f"   {ident}  {os.path.getsize(ident)/1024/1024:.1f} MB", flush=True)

    results = []

    print("== G1 拓扑守恒（250/400/900）==", flush=True)
    results.append(gates.g1_topology(ident))
    print("   PASS", flush=True)

    print("== G2 增量往返（对源 400）==", flush=True)
    # 源文件与 identity 都取 wght=400 比较
    results.append(gates.g2_roundtrip(SRC, ident))
    print("   PASS", flush=True)

    print("== G3 特性完整 ==", flush=True)
    results.append(gates.g3_features(
        ident,
        expected_features=["aalt","calt","ccmp","dlig","fwid","hist","hwid","liga","ljmo","locl","pwid","ruby","tjmo","vert","vjmo","vrt2"],
        expected_scripts=["DFLT","cyrl","grek","hang","hani","kana","latn"],
    ))
    print("   PASS", flush=True)

    print("== G4 cmap 基线 ==", flush=True)
    results.append(gates.g4_cmap(ident, min_entries=44000))
    print("   PASS", flush=True)

    print("== G5 结构健康 ==", flush=True)
    results.append(gates.g5_structure(ident))
    print("   PASS", flush=True)

    print("\n全部闸门通过：", flush=True)
    for r in results:
        print("  ", r, flush=True)


if __name__ == "__main__":
    main()
