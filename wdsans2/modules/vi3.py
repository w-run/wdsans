#!/usr/bin/env python3
"""vi3 - 深入检查 HVAR 与字宽变体"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
f = TTFont(VF, lazy=True)

print('=== HVAR 表结构 ===')
h = f['HVAR'].table
print('  AdvanceWidthMapping: %s' % ('有' if getattr(h,'AdvWidthMap',None) else '缺失!'))
am = getattr(h, 'AdvWidthMap', None)
if am is not None:
    print('    type: %s' % type(am).__name__)
    print('    DeltaSetIndexMap: %s' % ('有' if hasattr(am,'mapping') else '无'))
print('  VarStore: %s' % type(h.VarStore).__name__)
vs = h.VarStore
d = getattr(vs, 'data', None)
print('  VarStore.data: %s' % ('None' if d is None else len(d)))
if d:
    print('    VarData 条数: %d' % len(d.VarData))
    for i, vd in enumerate(d.VarData[:3]):
        print('      [%d] ItemCount=%d NumRegions=%d' % (i, len(vd.Item), vd.VarRegionCount if hasattr(vd,'VarRegionCount') else -1))

print()
print('=== 三档 master 的 hmtx 对比 ===')
for tag, fn in [('250','master-ExtraLight-250.otf'),
                 ('400','master-Regular-400.otf'),
                 ('900','master-Heavy-900.otf')]:
    p = '/workspace/wdsans2/build/masters_R25/' + fn
    if not os.path.exists(p):
        print('  %s 缺失' % tag); continue
    m = TTFont(p, lazy=True)
    hm = m['hmtx']; cm = m.getBestCmap()
    advs = [hm[cm[ord(c)]][0] for c in '永国字体设计' if ord(c) in cm]
    print('  %s: adv=%s' % (tag, advs))
    m.close()

print()
print('=== VF 本身 hmtx (默认 400) ===')
cm = f.getBestCmap(); hm = f['hmtx']
advs = [hm[cm[ord(c)]][0] for c in '永国字体设计' if ord(c) in cm]
print('  VF adv=%s' % advs)
f.close()