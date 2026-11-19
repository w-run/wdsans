#!/usr/bin/env python3
"""verify_typo_metrics - 验证启用 USE_TYPO_METRICS 是否安全"""
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
os2 = f["OS/2"]
cm = f.getBestCmap(); gs = f.getGlyphSet()

TYPO_ASC = os2.sTypoAscender    # 880
TYPO_DESC = os2.sTypoDescender  # -120
print("typo 范围: %d ~ %d  (共 %d = %.2fem)" % (TYPO_DESC, TYPO_ASC, TYPO_ASC-TYPO_DESC, (TYPO_ASC-TYPO_DESC)/1000.0))

print()
print("=== CJK 字形是否在此范围内 ===")
over_hi = []; over_lo = []
sample = [c for c in cm if 0x4E00 <= c <= 0x9FFF]
for cp in sample:
    gn = cm[cp]
    bp = BoundsPen(gs)
    try:
        gs[gn].draw(bp)
    except Exception:
        continue
    if not bp.bounds: continue
    if bp.bounds[3] > TYPO_ASC:
        over_hi.append((chr(cp), bp.bounds[3]))
    if bp.bounds[1] < TYPO_DESC:
        over_lo.append((chr(cp), bp.bounds[1]))
print("  CJK 共 %d 字" % len(sample))
print("  超出上方(>%d): %d 字" % (TYPO_ASC, len(over_hi)))
if over_hi[:5]: print("    样例: %s" % over_hi[:5])
print("  超出下方(<%d): %d 字" % (TYPO_DESC, len(over_lo)))
if over_lo[:5]: print("    样例: %s" % over_lo[:5])

print()
print("=== 拉丁/符号是否在此范围内（抽样 2000）===")
lat = [c for c in cm if 0x20 <= c <= 0x24F][:2000]
lhi = []; llo = []
for cp in lat:
    gn = cm[cp]
    bp = BoundsPen(gs)
    try:
        gs[gn].draw(bp)
    except Exception:
        continue
    if not bp.bounds: continue
    if bp.bounds[3] > TYPO_ASC: lhi.append((chr(cp), bp.bounds[3]))
    if bp.bounds[1] < TYPO_DESC: llo.append((chr(cp), bp.bounds[1]))
print("  拉丁/符号 %d 字" % len(lat))
print("  超高: %d  样例 %s" % (len(lhi), lhi[:3]))
print("  超低: %d  样例 %s" % (len(llo), llo[:3]))

print()
print("=== 若启用 typo，行高布局 ===")
print("  单行 = 1000 单位 = 1.00em")
print("  CJK 字面高 860 + 下伸 92 = 952 < 1000 -> 能放下")
print("  但字间会非常紧（CJK 常态行距是 1.0em 到 1.2em）")
print()
print("  参考: OPPO 1.32em / HOS 1.18em / 常见 CJK 网页 1.5-1.8em")
f.close()