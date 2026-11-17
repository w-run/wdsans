#!/usr/bin/env python3
"""ledge_blast - 精确统计 m_ledge 真实改了多少字、哪些改坏了"""
import sys, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

R15 = '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'
R16 = '/workspace/wdsans2/build/masters_R16/master-Regular-400.otf'

f15 = TTFont(R15, lazy=True); g15 = f15.getGlyphSet(); c15 = f15.getBestCmap()
f16 = TTFont(R16, lazy=True); g16 = f16.getGlyphSet(); c16 = f16.getBestCmap()

changed = []
suspicious = []

cjk = [cp for cp in c15 if 0x4E00 <= cp <= 0x9FFF and cp in c16]
print('对比 %d 字...' % len(cjk), flush=True)

for cp in cjk:
    r1 = RecordingPen(); g15[c15[cp]].draw(r1)
    r2 = RecordingPen(); g16[c16[cp]].draw(r2)
    # 直接比较所有坐标
    v1 = []; v2 = []
    for op, args in r1.value:
        for p in args:
            if hasattr(p, "__len__") and len(p) == 2:
                v1.extend([round(p[0],1), round(p[1],1)])
    for op, args in r2.value:
        for p in args:
            if hasattr(p, "__len__") and len(p) == 2:
                v2.extend([round(p[0],1), round(p[1],1)])
    if v1 == v2:
        continue
    changed.append(cp)
    # 判断是否「横笔跨过字心」：找最大 x 位移
    if len(v1) == len(v2):
        dx = max(abs(a-b) for a,b in zip(v1, v2))
        if dx > 150:
            suspicious.append((round(dx), chr(cp)))

f15.close(); f16.close()

print()
print('R15 -> R16 实际改动: %d 字' % len(changed))
print()
print('单点位移 > 150 单位（疑似拉过头）: %d 字' % len(suspicious))
suspicious.sort(reverse=True)
for d, ch in suspicious[:40]:
    print("  %s  位移 %d" % (ch, d))

json.dump({'changed': len(changed), 'suspicious': suspicious},
          open('/workspace/wdsans2/build/ledge_blast.json','w'), ensure_ascii=False)