#!/usr/bin/env python3
"""quad2cubic - 测试二次转三次后三档一致性"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.basePen import BasePen
import numpy as np

MONA = "/workspace/wdsans/ref/mona/MonaSansVF.ttf"

class QuadToCubicPen(BasePen):
    """把 quadTo 转成 curveTo（每段二次拆成一段三次）"""
    def __init__(self):
        super().__init__(None)
        self.ops = []
    def _moveTo(self, p):
        self.ops.append(("M", p))
    def _lineTo(self, p):
        self.ops.append(("L", p))
    def _curveToOne(self, p1, p2, p3):
        self.ops.append(("C", p1, p2, p3))
    def _qCurveToOne(self, p1, p2):
        # 起点 self._getCurrentPoint()
        p0 = self._getCurrentPoint()
        c1 = (p0[0] + 2.0/3.0*(p1[0]-p0[0]), p0[1] + 2.0/3.0*(p1[1]-p0[1]))
        c2 = (p2[0] + 2.0/3.0*(p1[0]-p2[0]), p2[1] + 2.0/3.0*(p1[1]-p2[1]))
        self.ops.append(("C", c1, c2, p2))
    def _closePath(self):
        self.ops.append(("Z",))
    def _endPath(self):
        self.ops.append(("E",))


def get_bullet_cubic(weight):
    f = TTFont(MONA)
    instantiateVariableFont(f, {"wght": weight}, inplace=True)
    cm = f.getBestCmap(); gs = f.getGlyphSet(); h = f["hmtx"]
    if 0x2022 not in cm:
        f.close(); return None
    gn = cm[0x2022]
    pen = QuadToCubicPen()
    gs[gn].draw(pen)
    adv = h[gn][0]
    f.close()
    return pen.ops, adv


print("=== 二次转三次后的签名 ===")
conv = {}
for w in (250, 400, 900):
    r = get_bullet_cubic(w)
    if r is None:
        print("  w%d 无数据" % w); continue
    ops, adv = r
    sig = "".join(o[0] for o in ops)
    conv[w] = (ops, adv, sig)
    print("  w%-4d adv=%-4d ops=%d sig=%s" % (w, adv, len(ops), sig))

sigs = set(v[2] for v in conv.values())
print()
print("签名数: %d  %s" % (len(sigs), "一致 OK" if len(sigs)==1 else "不一致 !!"))

print()
print("=== 墨迹尺寸（转三次后应不变）===")
for w, (ops, adv, sig) in conv.items():
    xs, ys = [], []
    for o in ops:
        if o[0] in ('M','L'):
            xs.append(o[1][0]); ys.append(o[1][1])
        elif o[0] == 'C':
            for p in o[1:]:
                xs.append(p[0]); ys.append(p[1])
    print("  w%-4d %.0f x %.0f" % (w, max(xs)-min(xs), max(ys)-min(ys)))