#!/usr/bin/env python3
"""scan_shared2 - 对 26 组共用字形做参考对比，找出真问题"""
from fontTools.ttLib import TTFont
import collections

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
REFS = {
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS":  "/workspace/wdsans/ref/hos/hos-400.ttf",
}

f = TTFont(VF, lazy=True)
cm = f.getBestCmap(); hmtx = f["hmtx"]
rev = collections.defaultdict(list)
for cp, gn in cm.items():
    rev[gn].append(cp)

ref = {}
for name, path in REFS.items():
    rf = TTFont(path, lazy=True)
    rcm = rf.getBestCmap(); rh = rf["hmtx"]
    ref[name] = {cp: rh[rcm[cp]][0] for cp in cm if cp in rcm}
    rf.close()

groups = [(gn, sorted(cps)) for gn, cps in rev.items()
          if len(cps) >= 2 and all(0x20 <= c <= 0x2FFF for c in cps)]
groups.sort(key=lambda x: x[1][0])

def label(cp):
    try:
        return "U+%04X %s" % (cp, chr(cp))
    except Exception:
        return "U+%04X" % cp

print("%-26s %-6s %6s %6s %6s %6s  %s" % ("码位组", "glyph", "我们", "SHS", "OPPO", "HOS", "判定"))
print("-" * 92)
issues = []
for gn, cps in groups:
    mine = hmtx[gn][0]
    # 对每个码位取参考值，看是否所有参考都远大于我们
    worst = None
    for cp in cps:
        rs = [ref[n][cp] for n in REFS if cp in ref[n]]
        if not rs:
            continue
        mn, mx = min(rs), max(rs)
        if mine < mn * 0.7:
            if worst is None or mine / mn < worst[1]:
                worst = (cp, mine / mn, mn, mx)
    cps_s = " ".join(label(c)[:7] for c in cps[:3])
    r0 = ref["SHS"].get(cps[0], -1)
    r1 = ref["OPPO"].get(cps[0], -1)
    r2 = ref["HOS"].get(cps[0], -1)
    verdict = "!! 偏窄" if worst else "OK"
    print("%-26s %-6d %6d %6d %6d %6d  %s" % (cps_s[:26], 0, mine, r0, r1, r2, verdict))
    if worst:
        issues.append((cps, gn, mine, worst))

print()
if issues:
    print("=== 需要关注的组 ===")
    for cps, gn, mine, (cp, ratio, mn, mx) in issues:
        print("  %s" % " / ".join(label(c) for c in cps))
        print("    我们 %d  参考 %d~%d  比值 %.2f" % (mine, mn, mx, ratio))
else:
    print("无 advance 偏窄的共用字形组")