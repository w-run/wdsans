#!/usr/bin/env python3
"""repro_t6 - replay T6 modules on SHS 永 to find which step moves the endpoint"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_taper, m_stepalign

SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
SW = 77.0


def hook_info(C):
    best = None
    for ci, c in enumerate(C):
        if len(c["segs"]) < 6:
            continue
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
        h = P[:,1].max() - P[:,1].min()
        if best is None or h > best[0]:
            best = (h, ci, c)
    if not best:
        return None
    c = best[2]
    st = np.array(c["start"], float)
    last = np.array(c["segs"][-1][-1], float)
    return (len(c["segs"]), st, last, float(np.hypot(*(last-st))))


f = TTFont(SHS, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
rp = RecordingPen(); gs[cm[ord("永")]].draw(rp); f.close()
C0 = contours_from_pen(rp.value)
r = hook_info(C0)
print("SHS raw      %dsegs  start(%.0f,%.0f) end(%.0f,%.0f) gap=%.1f" % (r[0], r[1][0], r[1][1], r[2][0], r[2][1], r[3]))

print()
print("taper ops:", len(m_taper.find(C0, SW)))
C1 = m_taper.apply(C0, m_taper.find(C0, SW))
r = hook_info(C1)
print("after taper  %dsegs  start(%.0f,%.0f) end(%.0f,%.0f) gap=%.1f" % (r[0], r[1][0], r[1][1], r[2][0], r[2][1], r[3]))

print()
print("stepalign ops:", len(m_stepalign.find(C1, SW)))
C2 = m_stepalign.apply(C1, m_stepalign.find(C1, SW))
r = hook_info(C2)
print("after align  %dsegs  start(%.0f,%.0f) end(%.0f,%.0f) gap=%.1f" % (r[0], r[1][0], r[1][1], r[2][0], r[2][1], r[3]))