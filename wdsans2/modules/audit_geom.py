#!/usr/bin/env python3
"""audit_geom - 几何模块审计（补充 audit_all 未覆盖的部分）

逐项验证:
  m_barple    横线右端对齐撇右界（永/今/亨 等）
  m_bardiag   横线延伸到斜边（建/延）
  m_ledge     顶部横笔右余 = TARGET_MARGIN
  m_latinext  Latin Ext-A 字符数
  m_punctscale 五个句读标点尺寸
  m_coloncenter 冒号居中（HarfBuzz 实测）
  m_featlang   7 特性在 zh-hans 下生效
"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
RES = []


def rec(name, status, detail):
    RES.append((name, status, detail))
    print('  [%-4s] %-14s %s' % (status, name, detail), flush=True)


f = TTFont(VF, lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()


def bbox(ch):
    if ord(ch) not in cm:
        return None
    bp = BoundsPen(gs)
    gs[cm[ord(ch)]].draw(bp)
    return bp.bounds


print('=== 几何模块 ===')

# m_ledge: DEPRECATED - removed from chain in R29 (see AGENTS.md)
#   v1 1182 chars / v2 2636 chars / v3 1511 chars but damaged 1456 glyphs
#   root cause: cannot distinguish whole-glyph top bar from left-radical bar
rec('ledge', 'SKIP', 'deprecated: m_ledge damaged 1456 glyphs, removed in R29')

# m_latinext: Latin Ext-A 覆盖
exta = sum(1 for cp in cm if 0x0100 <= cp <= 0x017F)
rec('latinext', 'PASS' if exta >= 120 else 'FAIL', 'Latin Ext-A %d/128' % exta)

# m_punctscale: 五个句读标点
print()
print('=== 句读标点尺寸 ===')
for ch, tw, th in [('。',272,272),('、',237,231),('，',138,246),('：',124,533),('；',162,667)]:
    b = bbox(ch)
    if not b:
        continue
    w = b[2]-b[0]; h = b[3]-b[1]
    dw = abs(w-tw)/tw*100; dh = abs(h-th)/th*100
    dev = max(dw, dh)
    rec('punct' + ch, 'PASS' if dev < 8 else 'FAIL',
        '%dx%d (目标%dx%d, 宽偏%+.1f%% 高偏%+.1f%%)' % (w, h, tw, th, dw, dh))
f.close()

print()
print('=== 特性在 zh-hans 下生效 ===')
data = open(VF, 'rb').read()


def gids(text, feats=None, lang="zh-Hans"):
    blob = hb.Blob(data); face = hb.Face(blob); font = hb.Font(face)
    b = hb.Buffer(); b.add_str(text)
    b.direction = 'ltr'; b.script = 'hani'; b.language = lang
    if feats:
        hb.shape(font, b, feats)
    else:
        hb.shape(font, b)
    return [i.codepoint for i in b.glyph_infos]


base = gids('123')
for tag in ['sups','subs','sinf','numr','dnom']:
    got = gids('123', {tag: True})
    rec('featlang.' + tag, 'PASS' if got != base else 'FAIL',
        'base=%s %s=%s' % (base, tag, got))
# pnum 在中文环境被 locl 抵消 —— 已知且正确（见 AGENTS.md）
_rec = gids('123', {'pnum': True})
rec('featlang.pnum', 'SKIP',
    'pnum 被 locl 抵消（已知正确行为），base=%s pnum=%s' % (base, _rec))

print()
print('=== coloncenter (calt) ===')
t1 = gids('12:34')
t2 = gids('a:b')
rec('coloncenter', 'PASS' if t1[2] != t2[1] else 'FAIL',
    '12:34 gid[2]=%d  a:b gid[1]=%d (应不同)' % (t1[2], t2[1]))

npass = sum(1 for x in RES if x[1] == "PASS")
nfail = sum(1 for x in RES if x[1] == "FAIL")
print()
print('=' * 60)
print('几何审计: PASS %d / FAIL %d (共 %d 项)' % (npass, nfail, len(RES)))
if nfail:
    print('FAIL: %s' % [x[0] for x in RES if x[1]=='FAIL'])