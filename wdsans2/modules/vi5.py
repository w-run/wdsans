#!/usr/bin/env python3
"""vi5 - 检查未映射槽位与空字形的情况"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
f = TTFont(VF, lazy=True)
go = f.getGlyphOrder(); cm = f.getBestCmap(); gs = f.getGlyphSet()
mapped = set(cm.values())
print('总字形: %d  已映射: %d  未映射: %d' % (len(go), len(mapped), len(go) - len(mapped)))

# 检查未映射字形里有多少非空（可能是 latinext 注入的）
nonempty = 0; empty = 0; samples = []
for gn in go:
    if gn in mapped:
        continue
    rp = RecordingPen()
    try:
        gs[gn].draw(rp)
    except Exception:
        continue
    if rp.value:
        nonempty += 1
        if len(samples) < 8:
            samples.append(gn)
    else:
        empty += 1
print('  未映射且有轮廓: %d' % nonempty)
print('  未映射且空: %d' % empty)
print('  非空样例: %s' % samples)

# 检查这些非空未映射字形是否被 GSUB 引用（如果没被引用就是浪费）
g = f['GSUB'].table
refs = set()
for lk in g.LookupList.Lookup:
    for st in lk.SubTable:
        t = st.ExtSubTable if hasattr(st, 'ExtSubTable') else st
        m = getattr(t, 'mapping', None)
        if m:
            for k, v in m.items():
                refs.add(k)
                if isinstance(v, str):
                    refs.add(v)
for attr in ('Coverage', 'InputCoverage', 'BacktrackCoverage', 'LookAheadCoverage'):
    pass
orphan = [gn for gn in samples if gn not in refs]
print()
print('=== 非空未映射字形的 GSUB 引用 ===')
print('  样本中未被子程序引用的: %d/%d' % (len(orphan), len(samples)))
print('  样例: %s' % orphan[:5])
f.close()