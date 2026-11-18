#!/usr/bin/env python3
# scan_step - find all glyphs where barple created a step
#
# Criterion: two contours overlap in y-range and both reach near the
# glyph right edge, but their right-edge x differs by a lot -> visible step.
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/'
T6 = B + 'masters_T6/master-Regular-400.otf'
MOD = B + 'masters_MOD/master-Regular-400.otf'


def boxes(path, ch):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    out = []
    for c in C:
        pts = [np.array(c["start"], float)]
        for s in c["segs"]:
            if s[0] == "QM":
                for q in s[1]: pts.append(np.array(q, float))
            elif s[0] == "C":
                pts.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
            elif s[0] == "Q":
                pts.extend([np.array(s[1],float), np.array(s[2],float)])
            else:
                pts.append(np.array(s[1], float))
        P = np.array(pts)
        out.append((P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
    return out


# 先看 barple 到底改了多少字
f6 = TTFont(T6, lazy=True); gs6 = f6.getGlyphSet(); cm6 = f6.getBestCmap()
fm = TTFont(MOD, lazy=True); gsm = fm.getGlyphSet(); cmm = fm.getBestCmap()
n_changed = 0; samples = []
for cp in [c for c in cm6 if 0x4E00 <= c <= 0x9FFF]:
    if cp not in cmm:
        continue
    def rb(g, cm):
        rp = RecordingPen()
        try:
            g[cm[cp]].draw(rp)
        except Exception:
            return None
        C = contours_from_pen(rp.value)
        xs = []
        for c in C:
            for s in c["segs"]:
                if s[0] == "QM":
                    for q in s[1]: xs.append(q[0])
                elif s[0] in ("C","Q"):
                    for q in s[1:-1]: xs.append(q[0])
                    xs.append(s[-1][0])
                else:
                    xs.append(s[1][0])
        return max(xs) if xs else None
    a = rb(gs6, cm6); b = rb(gsm, cmm)
    if a is not None and b is not None and abs(a-b) > 3:
        n_changed += 1
        if len(samples) < 20:
            samples.append("%s(%.0f->%.0f)" % (chr(cp), a, b))
f6.close(); fm.close()
print("T6 -> MOD 右界变化 >3 单位的字: %d" % n_changed)
print("  " + " ".join(samples))