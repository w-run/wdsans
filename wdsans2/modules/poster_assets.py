#!/usr/bin/env python3
"""poster_assets - 生成海报所需的字体子集与字形 path 数据"""
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools import subset
from fontTools.pens.svgPathPen import SVGPathPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
FA = '/workspace/static/wdsans/WDesignSans-FlatApex-Regular.otf'
OUT = '/workspace/static/wdsans/poster'
os.makedirs(OUT, exist_ok=True)

PARTS = [
    '永国字体设计的一是不了在人有我他这中大来上为个到说们',
    '永和九年岁在癸丑暮春之初会于山阴之兰亭修禊事也群贤毕至少长咸集',
    '天地玄黄宇宙洪荒日月盈昃辰宿列张寒来暑往秋收冬藏',
    '今合会含令全金余介企理想致美',
    '口田王三人八大天夫火木水日目明了子小',
    '横竖撇捺折点提钩笔锋端面曲率重心中宫平顶结构',
    'WDesign Sans 0123456789',
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
    '，。：；！？、「」（）—…·',
    '©®™+-×÷=%¥$€',
]
CHARS = sorted(set("".join(PARTS)))


def make_subset(src, dst, flavor=None):
    f = TTFont(src)
    opts = subset.Options()
    opts.layout_features = ['*']
    opts.notdef_outline = True
    opts.recalc_bounds = True
    opts.drop_tables += ['DSIG']
    if flavor:
        opts.flavor = flavor
    sub = subset.Subsetter(options=opts)
    sub.populate(unicodes=[ord(c) for c in CHARS])
    sub.subset(f)
    if flavor:
        f.flavor = flavor
    f.save(dst)
    f.close()
    print('  %s  %.0f KB' % (os.path.basename(dst), os.path.getsize(dst)/1024))


make_subset(VF, OUT + '/wd-vf.woff2', 'woff2')
make_subset(FA, OUT + '/wd-flat.woff2', 'woff2')


def paths(path, chars, wght=None):
    f = TTFont(path)
    if wght is not None and "fvar" in f:
        from fontTools.varLib.instancer import instantiateVariableFont
        f = instantiateVariableFont(f, {"wght": wght}, inplace=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap(); hm = f["hmtx"]
    out = {}
    for ch in chars:
        if ord(ch) not in cm:
            continue
        gn = cm[ord(ch)]
        sp = SVGPathPen(gs)
        gs[gn].draw(sp)
        d = sp.getCommands()
        if not d:
            continue
        out[ch] = {"d": d, "w": hm[gn][0]}
    f.close()
    return out


glyphs = paths(VF, CHARS)
print('  提取 %d 个字形 path' % len(glyphs))

flat_chars = '今合会含令全金余介企'
vf_p = paths(VF, flat_chars)
fa_p = paths(FA, flat_chars)

data = {"glyphs": glyphs, "flat": {"vf": vf_p, "fa": fa_p}}
json.dump(data, open(OUT + '/glyphdata.json', 'w'), ensure_ascii=False)
print('  glyphdata.json  %.0f KB' % (os.path.getsize(OUT + '/glyphdata.json')/1024))
print('done')