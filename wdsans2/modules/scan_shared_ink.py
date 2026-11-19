#!/usr/bin/env python3
"""scan_shared_ink - 共用字形的墨迹尺寸对比

U+2022 • 的问题不是 advance（500 已修）而是墨迹太小（118 vs 229）。
本脚本对全部共用字形组做墨迹尺寸对比，找出同类问题。
"""
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
import collections

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
REFS = {
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS":  "/workspace/wdsans/ref/hos/hos-400.ttf",
}

def load(path):
    f = TTFont(path, lazy=True)
    return f, f.getBestCmap(), f.getGlyphSet(), f["hmtx"]

def ink(gs, gn):
    bp = BoundsPen(gs)
    try:
        gs[gn].draw(bp)
    except Exception:
        return None
    b = bp.bounds
    if not b:
        return None
    return (b[2] - b[0], b[3] - b[1])

f, cm, gs, hmtx = load(VF)
rev = collections.defaultdict(list)
for cp, gn in cm.items():
    rev[gn].append(cp)

refs = {}
for name, path in REFS.items():
    rf, rcm, rgs, rh = load(path)
    refs[name] = (rcm, rgs, rh)

# 全部共用组（不限范围）
groups = [(gn, sorted(cps)) for gn, cps in rev.items() if len(cps) >= 2]
groups.sort(key=lambda x: x[1][0])

def lbl(cp):
    try:
        return "U+%04X %s" % (cp, chr(cp))
    except Exception:
        return "U+%04X" % cp

print("=== 共用字形的墨迹尺寸（w x h）vs 参考 ===")
print()
issues = []
for gn, cps in groups:
    mine = ink(gs, gn)
    if not mine:
        continue
    # 对每个码位取参考墨迹，找「我们明显小于参考」的
    worst = None
    for cp in cps:
        for name, (rcm, rgs, rh) in refs.items():
            if cp not in rcm:
                continue
            r = ink(rgs, rcm[cp])
            if not r:
                continue
            # 用面积比（宽*高）
            ma = mine[0] * mine[1]
            ra = r[0] * r[1]
            if ra > 0 and ma / ra < 0.6:
                if worst is None or ma / ra < worst[2]:
                    worst = (cp, name, ma / ra, r)
    if worst:
        cp, name, ratio, r = worst
        print("  %-30s 我们 %3.0fx%3.0f  vs %s %3.0fx%3.0f  (面积比 %.2f)  <-- 偏小" % (
            " / ".join(lbl(c) for c in cps)[:30], mine[0], mine[1], name, r[0], r[1], ratio))
        issues.append((cps, gn, mine, worst))

print()
print("共 %d 组墨迹偏小" % len(issues))
f.close()