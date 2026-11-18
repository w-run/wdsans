#!/usr/bin/env python3
# ratio3w - 撇厚度/横笔厚 的三档比例, 看 250 是否失衡
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

def bez(p0,c1,c2,p3,n=150):
    t = np.linspace(0,1,n)[:,None]
    return ((1-t)**3)*p0 + 3*((1-t)**2)*t*c1 + 3*(1-t)*(t**2)*c2 + (t**3)*p3

def measure(path, lbl):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    bar_h = None
    for c2 in C:
        if "".join(s[0] for s in c2["segs"]) == "LLL":
            yy=[c2["start"][1]]+[s[-1][1] for s in c2["segs"]]
            if max(yy) > 500 and min(yy) < 800:
                bar_h = max(yy)-min(yy)
    res = []
    for c in C:
        sig = "".join(s[0] for s in c["segs"])
        if sig != "LCCC": continue
        pts=[np.array(c["start"],float)]
        for s in c["segs"]:
            if s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
            else: pts.append(np.array(s[1],float))
        P=np.array(pts)
        if P[:,1].max()<600 or P[:,0].max()<600: continue
        segs = c["segs"]
        st = np.array(c["start"], float)
        outer = bez(st, np.array(segs[1][1],float), np.array(segs[1][2],float), np.array(segs[1][3],float))
        inner = bez(np.array(segs[2][3],float), np.array(segs[3][1],float), np.array(segs[3][2],float), np.array(segs[3][3],float))
        for ty in [560, 600, 640]:
            sel = inner[np.abs(inner[:,1]-ty) < 8]
            if not len(sel): continue
            best = min(np.hypot(outer[:,0]-p[0], outer[:,1]-p[1]).min() for p in sel)
            res.append((ty, best, best/bar_h if bar_h else 0))
        break
    print("%-10s bar_h=%-5.0f  " % (lbl, bar_h or 0) + "  ".join("y%d:%.0f(%.2f)" % r for r in res))

R = "/workspace/wdsans2/build/masters_R32/"
T = "/workspace/wdsans2/build/masters_T6/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
print("=== R32 (已修) 三档 ===")
for k in ["250","400","900"]: measure(R+FN[k], "R32-"+k)
print()
print("=== T6 (barple前) 三档 ===")
for k in ["250","400","900"]: measure(T+FN[k], "T6-"+k)
print()
print("=== SHS 三档 ===")
for w in [250,400,900]: measure("/workspace/wdsans/ref/shs/shs-%d.otf"%w, "SHS-%d"%w)