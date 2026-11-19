#!/usr/bin/env python3
"""which_metrics - 各平台实际用哪个行高度量"""
from fontTools.ttLib import TTFont

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
os2 = f["OS/2"]; hh = f["hhea"]

print("=== 我们的三组度量 ===")
print("  hhea:  ascent=%d  descent=%d  lineGap=%d  -> %.0f (%.2fem)" % (
      hh.ascent, hh.descent, hh.lineGap,
      hh.ascent - hh.descent + hh.lineGap,
      (hh.ascent - hh.descent + hh.lineGap)/1000.0))
print("  typo:  asc=%d  desc=%d  gap=%d  -> %.0f (%.2fem)" % (
      os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap,
      os2.sTypoAscender - os2.sTypoDescender + os2.sTypoLineGap,
      (os2.sTypoAscender - os2.sTypoDescender + os2.sTypoLineGap)/1000.0))
print("  win:   asc=%d  desc=%d  -> %.0f (%.2fem)" % (
      os2.usWinAscent, os2.usWinDescent,
      os2.usWinAscent + os2.usWinDescent,
      (os2.usWinAscent + os2.usWinDescent)/1000.0))

print()
print("=== fsSelection ===")
v = os2.fsSelection
print("  0x%04X  USE_TYPO_METRICS(bit7) = %s" % (v, "ON" if v & 0x80 else "OFF"))

print()
print("=== 各平台实际行为 ===")
if v & 0x80:
    print("  bit7 ON  -> 所有平台优先用 typo = %.0f (%.2fem)" % (
        os2.sTypoAscender - os2.sTypoDescender + os2.sTypoLineGap,
        (os2.sTypoAscender - os2.sTypoDescender + os2.sTypoLineGap)/1000.0))
else:
    print("  bit7 OFF -> Windows 用 win = %.0f (%.2fem)" % (
        os2.usWinAscent + os2.usWinDescent,
        (os2.usWinAscent + os2.usWinDescent)/1000.0))
    print("           -> macOS/iOS 用 hhea = %.0f (%.2fem)" % (
        hh.ascent - hh.descent + hh.lineGap,
        (hh.ascent - hh.descent + hh.lineGap)/1000.0))
    print("           -> HarfBuzz/Chrome 通常用 hhea 或 win（取较大）")

print()
print("=== OPPO/HOS 怎么做的 ===")
for name, path in (("OPPO", "/workspace/wdsans/ref/ops/ops-400.ttf"),
                   ("HOS", "/workspace/wdsans/ref/hos/hos-400.ttf")):
    g = TTFont(path, lazy=True)
    o = g["OS/2"]; h = g["hhea"]
    tv = o.sTypoAscender - o.sTypoDescender + o.sTypoLineGap
    wv = o.usWinAscent + o.usWinDescent
    hv = h.ascent - h.descent + h.lineGap
    fs = o.fsSelection
    print("  %-5s fsSel=0x%04X  typo=%-5d win=%-5d hhea=%-5d  bit7=%s" % (
        name, fs, tv, wv, hv, "ON" if fs & 0x80 else "OFF"))
    g.close()

print()
print("=== 关键洞察 ===")
print('OPPO/HOS 都置了 WWS(bit8) 但没置 USE_TYPO_METRICS(bit7)。')
print('它们靠把 usWin 和 hhea 都压到 1.32/1.18em 来收紧行高。')
print('我们/SHS 保持 1160/288 是因为要容纳 CJK 注音空间。')
f.close()