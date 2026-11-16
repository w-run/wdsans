#!/usr/bin/env python3
"""make_hos - 生成 HOS 对比子集 woff2"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools import subset

SRC = '/workspace/wdsans/ref/hos/hos-400.ttf'
OUT = '/workspace/static/wdsans/hos-compare.woff2'

# 平顶字 + 对照组 + 常用样板
CH = '今合会含令全金余介企口回十中申甲田日国目'
CH += '永国字体设计的书 0123456789'
CH += 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
CH += '，。：；！？（）「」—…、'

f = TTFont(SRC)
opts = subset.Options()
opts.flavor = 'woff2'
opts.layout_features = ['*']
opts.notdef_outline = True
opts.recalc_bounds = True
opts.drop_tables = []
opts.desubroutinize = False

sub = subset.Subsetter(options=opts)
sub.populate(unicodes=[ord(c) for c in set(CH)])
sub.subset(f)
f.flavor = 'woff2'
f.save(OUT)
f.close()

import os
print('生成 %s  %.1f KB' % (OUT, os.path.getsize(OUT)/1024))
g = TTFont(OUT)
print('  glyphs=%d cmap=%d' % (len(g.getGlyphOrder()), len(g.getBestCmap())))
g.close()