#!/usr/bin/env python3
# diag_w - 撇(斜边)的垂直厚度分布: R31 vs R32 vs SHS
#
# 轮廓 c1 = LCCC: seg1=外缘(下行) seg3=内缘(上行) -> 两者最近距离=笔画厚度
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

def bez(p0,c1,c2,p3,n=120):
    t = np.linspace(0,1,n)[:,None]
    return ((1-t)**3)*p0 + 3*((1-t)**2)*t*c1 + 3*(1-t)*(t**2)*c2 + (t**3)*p3

def core(path, lbl):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    # 找 LCCC 且 x_max>600 y_max>600 的（撇）
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
        print("=== %s ===" % lbl)
        print("   seg3 终点 = (%.0f,%.0f)" % (segs[3][3][0], segs[3][3][1]))
        print("   inner 采样点 y 范围 [%.0f, %.0f]" % (inner[:,1].min(), inner[:,1].max()))
        print("   y_em   厚度   (厚度/横笔厚)")
        bar_h = None
        for c2 in C:
            if "".join(s[0] for s in c2["segs"]) == "LLL":
                yy=[c2["start"][1]]+[s[-1][1] for s in c2["segs"]]
                if max(yy) > 600: bar_h = max(yy)-min(yy)
        for ty in [520, 560, 600, 640, 680, 700]:
            sel = inner[np.abs(inner[:,1]-ty) < 8]
            if not len(sel): continue
            best = 1e9
            for p in sel:
                d = np.hypot(outer[:,0]-p[0], outer[:,1]-p[1]).min()
                if d < best: best = d
            r = best/bar_h if bar_h else 0
            print("   %-6d %-6.0f %.3f" % (ty, best, r))
        print("   bar_h = %.0f" % (bar_h or 0))
        print()
        return

core("/workspace/wdsans2/build/masters_R31/master-ExtraLight-250.otf", "R31-250")
core("/workspace/wdsans2/build/masters_R32/master-ExtraLight-250.otf", "R32-250")
core("/workspace/wdsans/ref/shs/shs-250.otf", "SHS-250")