#!/usr/bin/env python3
"""vi8 - 检查 U+4E00 与 U+2F00 是否指向同一字形或不同字形"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
import numpy as np

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
f = TTFont(VF, lazy=True)
cm = f.getBestCmap(); gs = f.getGlyphSet(); hm = f['hmtx']
go = f.getGlyphOrder()

print('=== U+4E00(一) 与 U+2F00(⼀ 康熙部首) 的映射 ===')
for cp in [0x4E00, 0x2F00]:
    gn = cm.get(cp)
    print('  U+%04X -> %s' % (cp, gn))
    if gn:
        rp = RecordingPen()
        gs[gn].draw(rp)
        print('     gid=%d ops=%d adv=%d' % (go.index(gn), len(rp.value), hm[gn][0]))

print()
print('=== 两者轮廓是否相同 ===')
def sig(gn):
    rp = RecordingPen(); gs[gn].draw(rp)
    return len(rp.value), str(rp.value)[:80]
a = cm.get(0x4E00); b = cm.get(0x2F00)
if a and b:
    print('  U+4E00 -> %s  ops=%d' % (a, sig(a)[0]))
    print('  U+2F00 -> %s  ops=%d' % (b, sig(b)[0]))
    print('  同一字形: %s' % (a == b))

print()
print('=== 抽查 10 个基本字的 U+4E00 与 U+2Fxx 映射对 ===')
PAIRS = [(0x4E00,0x2F00,'一'),(0x4EBA,0x2F08,'人'),(0x513F,0x2F09,'儿'),
         (0x5165,0x2F0A,'入'),(0x516B,0x2F0B,'八'),(0x53E3,0x2F1D,'口'),
         (0x65E5,0x2F47,'日'),(0x6708,0x2F49,'月'),(0x6728,0x2F4A,'木'),
         (0x6C34,0x2F54,'水')]
print('%-4s %-12s %-12s %s' % ('字','U+4Exx','U+2Fxx','同一字形'))
for cp1, cp2, ch in PAIRS:
    g1 = cm.get(cp1); g2 = cm.get(cp2)
    print('%-4s %-12s %-12s %s' % (ch, g1 or '-', g2 or '-', '是' if g1==g2 else '否'))
f.close()