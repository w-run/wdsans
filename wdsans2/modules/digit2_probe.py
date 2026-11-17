#!/usr/bin/env python3
"""digit2_probe - 查数字 2 为什么偏粗"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
MONA = '/workspace/wdsans/ref/mona/MonaSansVF.ttf'


def info(path, ch, lbl, inst=None):
    f = TTFont(path, lazy=True)
    if inst is not None and "fvar" in f:
        from fontTools.varLib.instancer import instantiateVariableFont
        f = instantiateVariableFont(f, {"wght": inst}, inplace=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        print("  %-8s 无此字" % lbl); f.close(); return
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    ap = AreaPen(gs); gs[cm[ord(ch)]].draw(ap)
    bp = BoundsPen(gs); gs[cm[ord(ch)]].draw(bp)
    n = sum(1 for op,a in rp.value if op=="moveTo")
    nov = sum(1 for op,a in rp.value if op in ("curveTo","qCurveTo"))
    adv = f["hmtx"][cm[ord(ch)]][0]
    b = bp.bounds
    f.close()
    print("  %-8s 轮廓%2d 曲线%2d 面积%6.0f bbox %dx%d adv=%d" % (
        lbl, n, nov, abs(ap.value), b[2]-b[0], b[3]-b[1], adv))


print('=== 数字 2 ===')
for ch in '2':
    info(VF, ch, '我们VF')
    info(SHS, ch, 'SHS')
    info(MONA, ch, 'Mona400', 400)
print()
print('=== 数字 9（对照）===')
info(VF, '9', '我们VF')
info(SHS, '9', 'SHS')
info(MONA, '9', 'Mona400', 400)
print()
print('=== 数字 0（对照）===')
info(VF, '0', '我们VF')
info(SHS, '0', 'SHS')
info(MONA, '0', 'Mona400', 400)