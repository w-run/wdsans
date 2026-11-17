#!/usr/bin/env python3
"""digit_src - 查数字 0-9 各自来自哪个源"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
MONA = '/workspace/wdsans/ref/mona/MonaSansVF.ttf'


def metrics(path, ch, inst=None):
    f = TTFont(path, lazy=True)
    if inst is not None and "fvar" in f:
        from fontTools.varLib.instancer import instantiateVariableFont
        f = instantiateVariableFont(f, {"wght": inst}, inplace=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    ap = AreaPen(gs); gs[cm[ord(ch)]].draw(ap)
    bp = BoundsPen(gs); gs[cm[ord(ch)]].draw(bp)
    adv = f["hmtx"][cm[ord(ch)]][0]
    b = bp.bounds
    f.close()
    return abs(ap.value), adv, b[2]-b[0], b[3]-b[1]


print('%-3s %-28s %-28s %-28s %s' % ('字','我们(面积/adv/宽)','SHS','Mona400','来源'))
for ch in "0123456789":
    a = metrics(VF, ch); b = metrics(SHS, ch); m = metrics(MONA, ch, 400)
    if not a: continue
    # 判断来源：adv 与谁一致
    src = "?"
    if b and abs(a[1] - b[1]) <= 1:
        src = "SHS"
    if m and abs(a[1] - m[1]) <= 1:
        src = "Mona" if src == "?" else src + "+Mona(adv同)"
    print("%-3s %-28s %-28s %-28s %s" % (ch,
        "%.0f/%d/%d" % (a[0], a[1], a[2]),
        "%.0f/%d/%d" % (b[0], b[1], b[2]) if b else "-",
        "%.0f/%d/%d" % (m[0], m[1], m[2]) if m else "-",
        src))