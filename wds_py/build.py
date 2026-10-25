#!/usr/bin/env python3
"""用 fontTools 直接构建 OTF（绕开 otfcc —— 它在 iSH 上处理大字体会 segfault）。

字形来自：models/shs-sc/<Weight>/gid-*.json（CV 模型）+ glyph.restore() + filters
表来自：模板字体（云端产物），复制非字形表以保证 GSUB/GPOS/name/STAT 一致

用法:
    python3 wds_py/build.py --weight Regular --template build/v1/meta/WDesignSans-Regular.otf \
                            --out /tmp/py_test.otf [--limit 500]
"""
import argparse
import glob
import json
import os
import sys

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from glyph import restore, han_model_filter  # noqa: E402

ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'vendor', 'build-data')

WEIGHT_SOURCE = {
    'Thin': 'ExtraLight', 'Light': 'Light', 'Normal': 'Normal',
    'Regular': 'Regular', 'Medium': 'Medium', 'Bold': 'Bold', 'Heavy': 'Heavy',
}


def load_param(style):
    p = json.load(open(os.path.join(ROOT, 'parameters', 'wds', f'{style}.json')))
    p.pop('fira', None)
    p.pop('raleway', None)
    p['mona'] = {'Thin': 250, 'Light': 300, 'Normal': 350, 'Regular': 400,
                 'Medium': 500, 'Bold': 700, 'Heavy': 900}[style]
    p['shs'] = ['ExtraLight', 'Light', 'Normal', 'Regular', 'Medium',
                'Bold', 'Heavy'].index(WEIGHT_SOURCE[style])
    return p


def draw_to_pen(pen, contours):
    for c in contours:
        if not c:
            continue
        pen.moveTo((c[0]['x'], c[0]['y']))
        i = 1
        n = len(c)
        while i < n:
            p = c[i]
            if p['on']:
                pen.lineTo((p['x'], p['y']))
                i += 1
            else:
                p1 = c[i]
                p2 = c[i + 1] if i + 1 < n else c[0]
                p3 = c[i + 2] if i + 2 < n else c[0]
                pen.curveTo((p1['x'], p1['y']), (p2['x'], p2['y']),
                            (p3['x'], p3['y']))
                i += 3
        pen.closePath()


def build(style, template, out_path, limit=0, shards=None):
    param = load_param(style)
    src = WEIGHT_SOURCE[style]
    model_dir = os.path.join(DATA, 'models', 'shs-sc', src)
    files = sorted(glob.glob(os.path.join(model_dir, 'gid-*.json')))
    if shards:
        keep = {f'gid-{s}.json' for s in shards}
        files = [f for f in files if os.path.basename(f) in keep]

    cmap_src = json.load(open(os.path.join(
        ROOT, 'vendor', 'glow-src', 'encoding', 'cmaps', 'shs-sc.json')))
    cp_of = {}
    for uni, gname in cmap_src.items():
        try:
            cp_of[gname] = int(uni[2:], 16)
        except ValueError:
            pass

    tpl = TTFont(template, lazy=True)
    tpl_cmap = tpl.getBestCmap()
    tpl_order = tpl.getGlyphOrder()
    tpl_hmtx = tpl['hmtx']
    tpl_os2 = tpl['OS/2']
    tpl_name = {r.nameID: r.toUnicode() for r in tpl['name'].names
                if r.platformID == 3 and r.langID == 0x409}
    tpl_hhea = tpl['hhea']

    filt = han_model_filter(param)
    glyphs = {}
    want = set(cp_of.values())
    if limit:
        want = set(sorted(want)[:limit])

    for f in files:
        models = json.load(open(f))
        for gname, m in models.items():
            cp = cp_of.get(gname)
            if cp is None or cp not in want:
                continue
            contours = restore(m, filt)
            # 与 JS 一致：平移 -baseline
            b = param['baseline']
            for c in contours:
                for p in c:
                    p['y'] -= b
            tpl_g = tpl_cmap.get(cp)      # 模板用 cidXXXXX，模型用 uniXXXX
            if tpl_g is None:
                continue
            glyphs[tpl_g] = contours

    print(f'{style}: files={len(files)} want={len(want)} glyphs={len(glyphs)}')
    print(f'{style}: 生成 {len(glyphs)} 个字形')

    order = ['.notdef'] + [g for g in tpl_order if g in glyphs]
    metrics = {'.notdef': (500, 0)}
    charstrings = {}
    for g in order:
        if g == '.notdef':
            pen = T2CharStringPen(500, None)
            charstrings[g] = pen.getCharString()
            continue
        adv = tpl_hmtx[g][0] if g in tpl_hmtx.metrics else 1000
        pen = T2CharStringPen(adv, None)
        draw_to_pen(pen, glyphs[g])
        charstrings[g] = pen.getCharString()
        metrics[g] = (adv, 0)

    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder(order)
    inv = {}
    for cp, g in tpl_cmap.items():
        if g in glyphs:
            inv[cp] = g
    fb.setupCharacterMap(inv)
    fb.setupCFF(tpl_name.get(6, 'WDesignSans-Regular'),
                {'FullName': tpl_name.get(4, 'WDesign Sans')},
                charstrings, {})
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=tpl_hhea.ascent, descent=tpl_hhea.descent,
                             lineGap=tpl_hhea.lineGap)
    fb.setupNameTable({n: tpl_name[n] for n in (1, 2, 4, 5, 6, 16, 17)
                       if n in tpl_name})
    fb.setupOS2(sTypoAscender=tpl_os2.sTypoAscender,
                sTypoDescender=tpl_os2.sTypoDescender,
                sTypoLineGap=tpl_os2.sTypoLineGap,
                usWinAscent=tpl_os2.usWinAscent,
                usWinDescent=tpl_os2.usWinDescent,
                sxHeight=tpl_os2.sxHeight, sCapHeight=tpl_os2.sCapHeight,
                usWeightClass=tpl_os2.usWeightClass,
                usWidthClass=5, fsSelection=tpl_os2.fsSelection)
    fb.setupPost()

    if not limit and not shards:   # 裁剪模式下 GSUB/GPOS 会引用被删的字形
        for tag in ('GSUB', 'GPOS', 'GDEF', 'BASE'):
            if tag in tpl:
                fb.font[tag] = tpl[tag]

    fb.save(out_path)
    print(f'-> {out_path}  {os.path.getsize(out_path)/1e6:.2f}MB')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--weight', default='Regular')
    ap.add_argument('--template', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--shards', default='')
    a = ap.parse_args()
    build(a.weight, a.template, a.out, a.limit,
          [s.strip() for s in a.shards.split(',') if s.strip()] or None)


if __name__ == '__main__':
    main()
