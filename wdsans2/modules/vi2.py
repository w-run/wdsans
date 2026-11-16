#!/usr/bin/env python3
"""vi2 - 轻量验证 9 档插值（HarfBuzz，不实例化整个字体）"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
data = open(VF, 'rb').read()
CH = '永国字体设计的一是不了在人有我他这中大来上'


def adv_at(wght, text):
    blob = hb.Blob(data); face = hb.Face(blob); font = hb.Font(face)
    font.set_variations({'wght': wght})
    b = hb.Buffer(); b.add_str(text)
    b.direction = 'ltr'; b.script = 'hani'; b.language = 'zh'
    hb.shape(font, b)
    return sum(font.get_glyph_h_advance(i.codepoint) for i in b.glyph_infos)


print('=== 各档 advance 总宽（19 字）===')
prev = None
for w in [250, 300, 350, 400, 500, 600, 700, 800, 900]:
    a = adv_at(w, CH)
    flag = ''
    if prev is not None and a <= prev:
        flag = '  <<< 非递增!'
    print('  wght=%3d  adv总=%5d%s' % (w, a, flag))
    prev = a

print()
print('=== 结构与 cmap 一致性 ===')
f = TTFont(VF, lazy=True)
go = f.getGlyphOrder(); cm = f.getBestCmap()
print('  glyphs=%d cmap=%d cjk=%d' % (len(go), len(cm),
      sum(1 for cp in cm if 0x4E00 <= cp <= 0x9FFF)))
g = f['GSUB'].table
feats = sorted(set(fr.FeatureTag for fr in g.FeatureList.FeatureRecord))
print('  features=%d lookups=%d' % (len(feats), len(g.LookupList.Lookup)))
print('  fvar axes: %s' % [(a.axisTag, a.minValue, a.maxValue, a.defaultValue)
      for a in f['fvar'].axes])
print('  instances=%d' % len(f['fvar'].instances))
for t in ['HVAR', 'STAT', 'GDEF', 'BASE', 'VORG', 'VVAR']:
    print('  %-5s: %s' % (t, '有' if t in f else '缺失!'))
f.close()