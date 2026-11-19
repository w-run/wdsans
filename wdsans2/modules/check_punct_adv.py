#!/usr/bin/env python3
"""check_punct_adv - 全面检查标点 advance 与参考字体对比"""
from fontTools.ttLib import TTFont

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS":  "/workspace/wdsans/ref/hos/hos-400.ttf",
}
# 常用中文标点 + 间隔号 + 拉丁标点
PUNCT = [
    ("U+00B7 ·", 0x00B7), ("U+2022 •", 0x2022), ("U+30FB ・", 0x30FB),
    ("U+3001 、", 0x3001), ("U+3002 。", 0x3002), ("U+FF0C ，", 0xFF0C),
    ("U+FF1A ：", 0xFF1A), ("U+FF1B ；", 0xFF1B), ("U+FF01 ！", 0xFF01),
    ("U+FF1F ？", 0xFF1F), ("U+2014 —", 0x2014), ("U+2026 …", 0x2026),
    ("U+300C 「", 0x300C), ("U+300D 」", 0x300D),
    ("U+FF08 （", 0xFF08), ("U+FF09 ）", 0xFF09),
    ("U+00B7", 0x00B7),
]
# 去重
seen = set(); P2 = []
for n, c in PUNCT:
    if c in seen: continue
    seen.add(c); P2.append((n, c))

data = {}
for name, path in FONTS.items():
    f = TTFont(path, lazy=True)
    cm = f.getBestCmap(); hmtx = f["hmtx"]
    d = {}
    for label, cp in P2:
        if cp in cm:
            d[cp] = hmtx[cm[cp]][0]
    f.close()
    data[name] = d

print("%-14s %8s %8s %8s %8s   %s" % ("标点", "我们", "SHS", "OPPO", "HOS", "判定"))
print("-" * 68)
issues = []
for label, cp in P2:
    row = "%-14s" % label
    vals = {}
    for n in FONTS:
        v = data[n].get(cp)
        vals[n] = v
        row += " %8s" % (v if v is not None else "-")
    # 判定：我们 vs 三家参考的最小值
    refs = [vals[n] for n in ("SHS","OPPO","HOS") if vals[n] is not None]
    me = vals["我们"]
    if me is None or not refs:
        verdict = "无数据"
    else:
        mn, mx = min(refs), max(refs)
        if me < mn * 0.7:
            verdict = "!! 偏窄"
            issues.append((label, cp, me, mn, mx))
        elif me > mx * 1.4:
            verdict = "!! 偏宽"
            issues.append((label, cp, me, mn, mx))
        else:
            verdict = "OK"
    row += "   " + verdict
    print(row)

print()
if issues:
    print("=== 需要修正的标点（我们 < 参考最小值*0.7）===")
    for label, cp, me, mn, mx in issues:
        print("  %-14s 我们 %d  参考 %d~%d  (差 %+d)" % (label, me, mn, mx, me-mn))
else:
    print("全部在合理区间")
