#!/usr/bin/env python3
"""verify_r36_full - R36 完整质量验证"""
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
FA = "/workspace/static/wdsans/WDesignSans-FlatApex-Regular.otf"

print("=== 1. OS/2 全字段检查（v4 升级后）===")
f = TTFont(VF, lazy=True)
o = f["OS/2"]
print("  version = %d" % o.version)
print("  sTypoAscender/Descender/LineGap = %d/%d/%d" % (
    o.sTypoAscender, o.sTypoDescender, o.sTypoLineGap))
print("  usWinAscent/Descent = %d/%d" % (o.usWinAscent, o.usWinDescent))
print("  fsSelection = 0x%04X" % o.fsSelection)
print("  ulUnicodeRange1 = 0x%08X" % o.ulUnicodeRange1)
print("  ulCodePageRange1 = 0x%08X" % o.ulCodePageRange1)
print("  sxHeight = %d  sCapHeight = %d" % (o.sxHeight, o.sCapHeight))
print("  usLowerOpticalPointSize = %s" % getattr(o, "usLowerOpticalPointSize", "缺"))
print("  usUpperOpticalPointSize = %s" % getattr(o, "usUpperOpticalPointSize", "缺"))

print()
print("=== 2. 字形是否被 typo 范围裁切（关键）===")
print("  bit7 用 typo=(-282,1070)。检查全部字形是否在此范围内:")
cm = f.getBestCmap(); gs = f.getGlyphSet()
SKIP = {0x302A, 0x302D, 0x3031, 0x3032, 0x3033, 0x3034, 0x3035}
over = []; under = []
n = 0
for cp, gn in cm.items():
    if cp in SKIP: continue
    bp = BoundsPen(gs)
    try:
        gs[gn].draw(bp)
    except Exception:
        continue
    if not bp.bounds: continue
    n += 1
    if bp.bounds[3] > o.sTypoAscender:
        over.append((cp, bp.bounds[3]))
    if bp.bounds[1] < o.sTypoDescender:
        under.append((cp, bp.bounds[1]))
print("  检查 %d 字符: 超高 %d / 超低 %d" % (n, len(over), len(under)))
if over:
    print("  !! 超高样例: %s" % [(hex(c), round(y)) for c, y in over[:5]])
if under:
    print("  !! 超低样例: %s" % [(hex(c), round(y)) for c, y in under[:5]])
if not over and not under:
    print("  全部字形在 typo 范围内，无裁切 ✓")

print()
print("=== 3. 竖排符号（usWin 保留的意义）===")
for cp in (0x3031, 0x3032, 0x302A, 0x302D):
    if cp not in cm: continue
    bp = BoundsPen(gs)
    try:
        gs[cm[cp]].draw(bp)
    except Exception:
        continue
    b = bp.bounds
    if b:
        note = "OK(usWin内)" if (b[3] <= o.usWinAscent and b[1] >= -o.usWinDescent) else "仍超usWin"
        print("  U+%04X y=%.0f~%.0f  %s" % (cp, b[1], b[3], note))
f.close()

print()
print("=== 4. FlatApex 一致性 ===")
g = TTFont(FA, lazy=True)
p = g["OS/2"]
print("  version=%d typo=(%d,%d,%d) fsSel=0x%04X usWin=(%d,%d)" % (
    p.version, p.sTypoAscender, p.sTypoDescender, p.sTypoLineGap,
    p.fsSelection, p.usWinAscent, p.usWinDescent))
same = (p.sTypoAscender, p.sTypoDescender, p.fsSelection) == (o.sTypoAscender, o.sTypoDescender, o.fsSelection)
print("  与 VF 度量一致: %s" % same)
g.close()