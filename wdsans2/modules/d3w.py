#!/usr/bin/env python3
# d3w - 撇厚度绝对值 三档, R31/R32/T6, 以及撇/横笔比
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

def bez(p0,c1,c2,p3,n=200):
    t = np.linspace(0,1,n)[:,None]
    return ((1-t)**3)*p0 + 3*((1-t)**2)*t*c1 + 3*(1-t)*(t**2)*c2 + (t**3)*p3

def diag_thick(path, lbl):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    bar_h = None
    for c2 in C:
        if "".join(s[0] for s in c2["segs"]) != "LLL": continue
        yy = [c2["start"][1]] + [s[-1][1] for s in c2["segs"]]
        h = max(yy)-min(yy)
        if 20 < h < 400 and max(yy) > 550:
            bar_h = h; break
    for c in C:
        sig = "".join(s[0] for s in c["segs"])
        if sig != "LCCC": continue
        pts=[np.array(c["start"],float)]
        for s in c["segs"]:
            if s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
            else: pts.append(np.array(s[1],float))
        P=np.array(pts)
        if P[:,1].max()<600 or P[:,0].max()<600: continue
        segs=c["segs"]; st=np.array(c["start"],float)
        outer = bez(st, np.array(segs[1][1],float), np.array(segs[1][2],float), np.array(segs[1][3],float))
        inner = bez(np.array(segs[2][3],float), np.array(segs[3][1],float), np.array(segs[3][2],float), np.array(segs[3][3],float))
        vals = []
        for ty in [560, 600, 640]:
            sel = inner[np.abs(inner[:,1]-ty) < 10]
            if not len(sel): continue
            best = min(np.hypot(outer[:,0]-p[0], outer[:,1]-p[1]).min() for p in sel)
            vals.append(best)
        if not vals: continue
        avg = sum(vals)/len(vals)
        print("%-10s bar_h=%-5.0f  diag=%s  avg=%.0f  ratio=%.2f" % (
            lbl, bar_h or 0, "/".join("%.0f"%v for v in vals), avg, avg/bar_h if bar_h else 0))
        return
    print("%-10s 未找到" % lbl)

for src, nm in [("/workspace/wdsans2/build/masters_T6/","T6"),
                ("/workspace/wdsans2/build/masters_R31/","R31"),
                ("/workspace/wdsans2/build/masters_R32/","R32")]:
    for w in ["250","400","900"]:
        fn = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}[w]
        diag_thick(src+fn, "%s-%s" % (nm, w))
    print()