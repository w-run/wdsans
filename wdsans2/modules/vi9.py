#!/usr/bin/env python3
"""vi9 - 验证预览子集与主字体的一致性"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
W = '/workspace/static/wdsans/wd-preview.woff2'

fv = TTFont(VF, lazy=True); fw = TTFont(W, lazy=True)
cmv = fv.getBestCmap(); cmw = fw.getBestCmap()

print('=== 字体与子集对比 ===')
print('  VF:   glyphs=%d cmap=%d' % (len(fv.getGlyphOrder()), len(cmv)))
print('  子集: glyphs=%d cmap=%d' % (len(fw.getGlyphOrder()), len(cmw)))

# 子集应该覆盖常用 3500 + ASCII
common = open('/workspace/wdsans2/data/common3500.txt', encoding='utf-8').read().strip()
miss = [c for c in common if ord(c) not in cmw]
print('  常用 3500 在子集中缺失: %d' % len(miss))
if miss:
    print('    缺: %s' % ''.join(miss[:30]))

# 特性完整性
gv = fv['GSUB'].table; gw = fw['GSUB'].table
fv_feats = sorted(set(fr.FeatureTag for fr in gv.FeatureList.FeatureRecord))
fw_feats = sorted(set(fr.FeatureTag for fr in gw.FeatureList.FeatureRecord))
print()
print('=== GSUB 特性 ===')
print('  VF:   %d 种' % len(fv_feats))
print('  子集: %d 种' % len(fw_feats))
lost = [f for f in fv_feats if f not in fw_feats]
print('  子集丢失: %s' % (lost if lost else '无'))

# 关键特性是否可用
for tag in ['sups', 'subs', 'frac', 'pnum', 'calt', 'vert', 'vrt2', 'locl']:
    inv = any(fr.FeatureTag == tag for fr in gv.FeatureList.FeatureRecord)
    inw = any(fr.FeatureTag == tag for fr in gw.FeatureList.FeatureRecord)
    print('  %-5s VF=%s 子集=%s %s' % (tag, '有' if inv else '无',
          '有' if inw else '无', '' if inv == inw else '<-- 不一致!'))

# fvar 是否保留
print()
print('=== 可变轴 ===')
print('  VF fvar: %s' % ('有' if 'fvar' in fv else '无'))
print('  子集 fvar: %s' % ('有' if 'fvar' in fw else '无'))
if 'fvar' in fw:
    print('    轴: %s' % [(a.axisTag, a.minValue, a.maxValue) for a in fw['fvar'].axes])
fv.close(); fw.close()