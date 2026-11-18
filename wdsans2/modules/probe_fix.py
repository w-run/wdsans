#!/usr/bin/env python3
# probe_fix - test keeping the slant cut while aligning bar
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

T6 = '/workspace/wdsans2/build/masters_T6/master-Regular-400.otf'
OUT = '/workspace/wdsans2/build/test_duo.otf'

f = TTFont(T6); gs = f.getGlyphSet(); cm = f.getBestCmap()
gn = cm[ord("多")]
rp = RecordingPen(); gs[gn].draw(rp)
C = contours_from_pen(rp.value)
print("T6 duo: %d contours" % len(C))
for ci, c in enumerate(C):
    sig = "".join(s[0] for s in c["segs"])
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
    print("  c%d %-8s x[%.0f,%.0f] y[%.0f,%.0f]" % (ci, sig, P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))

NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
s3_end = np.array(C[1]["segs"][3][-1], float)
s4_end = np.array(C[1]["segs"][4][-1], float)
print("")
print("slant cut: seg3 end (%.0f,%.0f) -> seg4 end (%.0f,%.0f)" % (s3_end[0],s3_end[1],s4_end[0],s4_end[1]))
y_t = 685.0
t = (y_t - s3_end[1]) / (s4_end[1] - s3_end[1])
x_cut = s3_end[0] + t*(s4_end[0]-s3_end[0])
print("cut at y=%.0f -> x=%.1f (t=%.2f)" % (y_t, x_cut, t))
bar = NEW[2]
bar["start"] = (x_cut, bar["start"][1])
bar["segs"][2] = ["L", (x_cut, bar["segs"][2][-1][1])]
print("bar right: 733 -> %.1f" % x_cut)

cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
old = csT[gn]
csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
f["post"].formatType = 3.0; f["post"].glyphOrder = None
f.save(OUT); f.close()
print("saved " + OUT)