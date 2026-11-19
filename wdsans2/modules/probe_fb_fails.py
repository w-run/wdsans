#!/usr/bin/env python3
"""probe_fb_fails - 核实 fontbakery 报的 2 个可修 FAIL"""
from fontTools.ttLib import TTFont

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
SHS = "/workspace/wdsans/ref/shs/shs-400.otf"

print("=== FAIL 1: 版本号不一致 ===")
for lbl, p in (("我们", VF), ("SHS", SHS)):
    f = TTFont(p, lazy=True)
    rev = f["head"].fontRevision
    n5 = f["name"].getDebugName(5)
    print("  %-4s head.fontRevision=%.5f  nameID5=%s" % (lbl, rev, n5))
    f.close()

print()
print("=== FAIL 2: 零 advance 的基底字符 ===")
f = TTFont(VF, lazy=True)
cm = f.getBestCmap(); h = f['hmtx']
for cp in (0x20DD, 0x20DE, 0x20DF, 0x20E0):
    if cp not in cm:
        print("  U+%04X 字体无" % cp); continue
    gn = cm[cp]
    adv = h[gn][0]
    print("  U+%04X %-12s adv=%d" % (cp, gn, adv))

# 对比 SHS
print()
print("=== SHS 同字符 ===")
g = TTFont(SHS, lazy=True)
gcm = g.getBestCmap(); gh = g['hmtx']
for cp in (0x20DD, 0x20DE):
    if cp not in gcm:
        print("  U+%04X SHS 无" % cp); continue
    print('  U+%04X %-12s adv=%d' % (cp, gcm[cp], gh[gcm[cp]][0]))
g.close()

print()
print("=== 这两个字符是什么 ===")
import unicodedata
for cp in (0x20DD, 0x20DE):
    try:
        print("  U+%04X %s" % (cp, unicodedata.name(chr(cp))))
    except Exception:
        print("  U+%04X ?" % cp)
f.close()