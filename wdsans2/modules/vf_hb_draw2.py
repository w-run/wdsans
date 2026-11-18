#!/usr/bin/env python3
"""vf_hb_draw2 - HarfBuzz draw + fontTools pen 取各字重轮廓"""
import io
import uharfbuzz as hb
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

P = "/workspace/static/wdsans/wd-preview.woff2"
f = TTFont(P); f.flavor = None
b = io.BytesIO(); f.save(b); f.close()
DATA = b.getvalue()

class CollectPen(BasePen):
    def __init__(self):
        super().__init__(None)
        self.pts = []
    def _moveTo(self, p): self.pts.append(p)
    def _lineTo(self, p): self.pts.append(p)
    def _curveToOne(self, p1, p2, p3):
        self.pts.extend([p1, p2, p3])
    def _qCurveToOne(self, p1, p2):
        self.pts.extend([p1, p2])
    def _closePath(self): pass
    def _endPath(self): pass

def outline(ch, w):
    blob = hb.Blob(DATA)
    face = hb.Face(blob); font = hb.Font(face)
    font.set_variations({"wght": w})
    buf = hb.Buffer(); buf.add_str(ch); buf.guess_segment_properties()
    hb.shape(font, buf)
    if not buf.glyph_infos: return None
    gid = buf.glyph_infos[0].codepoint
    if gid == 0: return None
    pen = CollectPen()
    try:
        font.draw_glyph_with_pen(gid, pen)
    except Exception as e:
        return None
    if not pen.pts: return None
    return np.array(pen.pts, float)

WEIGHTS = [250, 300, 350, 400, 500, 600, 700, 800, 900]
CH = ["十", "王", "叫", "昨", "晴", "国", "永"]

print("=== CJK 字形包围盒 vs 字重 ===")
allgood = True
for ch in CH:
    print()
    print("  %s:" % ch)
    prev = None
    seq = []
    for w in WEIGHTS:
        P_ = outline(ch, w)
        if P_ is None:
            print("    w%-4d 无数据" % w); seq.append(None); continue
        wd = P_[:,0].max() - P_[:,0].min()
        ht = P_[:,1].max() - P_[:,1].min()
        d = "" if prev is None else "  %+5.1f" % (wd - prev)
        print("    w%-4d 宽%6.1f%s  高%6.1f" % (w, wd, d, ht))
        seq.append(wd)
        prev = wd
    if any(v is None for v in seq):
        print("    -> 数据不全")
        allgood = False
        continue
    diffs = [seq[i+1]-seq[i] for i in range(len(seq)-1)]
    mono = all(d >= -0.6 for d in diffs)
    if not mono: allgood = False
    print("    -> %s  跳变 min %+.1f max %+.1f" % (
        "单调增 OK" if mono else "!! 非单调", min(diffs), max(diffs)))

print()
print("=" * 50)
print("总体:", "全部单调，插值平滑" if allgood else "存在非单调，需检查")
