#!/usr/bin/env python3
"""verify_r36 - R36 行高效果验证"""
import numpy as np
from fontTools.ttLib import TTFont

NEW = "/workspace/wdsans2/build/VF_R36.otf"
OLD = "/workspace/static/wdsans/WDesignSans-VF.otf"

def metrics(p):
    f = TTFont(p, lazy=True)
    o = f["OS/2"]; hh = f["hhea"]
    typo = o.sTypoAscender - o.sTypoDescender + o.sTypoLineGap
    win = o.usWinAscent + o.usWinDescent
    hhea = hh.ascent - hh.descent + hh.lineGap
    b7 = bool(o.fsSelection & 0x80)
    f.close()
    return dict(ver=o.version, typo=typo, win=win, hhea=hhea, b7=b7)

print("=== 行高对比 ===")
print("%-8s %6s %10s %10s %10s %8s" % ("版本","OS/2","typo","usWin","hhea","bit7"))
print("-" * 58)
for lbl, p in (("R35", OLD), ("R36", NEW)):
    m = metrics(p)
    print("%-8s v%-5d %8.2fem %8.2fem %8.2fem %8s" % (
        lbl, m["ver"], m["typo"]/1000.0, m["win"]/1000.0, m["hhea"]/1000.0,
        "ON" if m["b7"] else "off"))

print()
print("=== 实际生效行高（bit7 ON -> 用 typo）===")
for lbl, p in (("R35", OLD), ("R36", NEW)):
    m = metrics(p)
    used = m["typo"] if m["b7"] else m["win"]
    print("  %-4s -> %.2fem  (%d 单位)" % (lbl, used/1000.0, used))

print()
print("=== 7 行 UI 文本总高（14px）===")
PX = 14
for lbl, p in (("R35", OLD), ("R36", NEW)):
    m = metrics(p)
    used = m["typo"] if m["b7"] else m["win"]
    per_line = used / 1000.0 * PX
    total = per_line * 7
    print("  %-4s 单行 %.1fpx  7行 %.0fpx" % (lbl, per_line, total))

print()
print("参考: OPPO 7行=%.0fpx  HOS 7行=%.0fpx" % (1.32*PX*7, 1.18*PX*7))