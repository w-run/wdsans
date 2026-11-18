#!/usr/bin/env python3
# dbg_D - why did variant D not change 多 at 250?
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_barple

P = '/workspace/wdsans2/build/masters_T6/master-ExtraLight-250.otf'
SW = 30.0

f = TTFont(P, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
C = contours_from_pen(rp.value)
print("T6 250: %d contours" % len(C))
for ci, c in enumerate(C):
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
    P2 = np.array(pts)
    sig = "".join(s[0] for s in c["segs"])
    print("  c%d %-10s x[%.0f,%.0f] y[%.0f,%.0f]" % (ci, sig, P2[:,0].min(), P2[:,0].max(), P2[:,1].min(), P2[:,1].max()))

hits = m_barple.find(C, SW)
print()
hits: %d" % len(hits) if False else print("hits: %d" % len(hits))
for bi, ci, ei, xL, xR, by0 in hits:
    body = C[ci]
    print("  bar c%d, body c%d, ei=%d (body has %d segs), xL=%.1f xR=%.1f by0=%.1f" % (
        bi, ci, ei, len(body["segs"]), xL, xR, by0))
    nxt = ei + 1
    if nxt < len(body["segs"]):
        s = body["segs"][nxt]
        print("    seg[%d] = %s -> (%.1f,%.1f)" % (nxt, s[0], s[-1][0], s[-1][1]))
    else:
        print("    seg[%d] 不存在（ei 已是最后一段）" % nxt)