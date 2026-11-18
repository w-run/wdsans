#!/usr/bin/env python3
# joint - 撇起笔端 (横折处) 的轮廓点, SHS vs R32, 250档
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

def dump(path, lbl, raw=False):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    print("=== %s ===" % lbl)
    if raw:
        for i,(op,args) in enumerate(rp.value):
            if op=="closePath": continue
            if op in ("moveTo","lineTo"):
                p=args[0]
                if p[1] > 600 and p[0] > 500:
                    print("  %2d %-8s (%.0f,%.0f)" % (i,op,p[0],p[1]))
            elif op=="qCurveTo":
                for p in args:
                    if p and p[1] > 600 and p[0] > 500:
                        print("  %2d q         (%.0f,%.0f)" % (i,p[0],p[1]))
        print(); return
    C = contours_from_pen(rp.value)
    for c in C:
        pts=[np.array(c["start"],float)]
        for s in c["segs"]:
            if s[0]=="QM":
                for q in s[1]: pts.append(np.array(q,float))
            elif s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
            else: pts.append(np.array(s[1],float))
        P=np.array(pts)
        if P[:,1].max() < 600 or P[:,0].max() < 600: continue
        sig="".join(s[0] for s in c["segs"])
        print("  c %-18s 起点(%.0f,%.0f)  %d段  x[%.0f,%.0f] y[%.0f,%.0f]" % (
            sig, c["start"][0], c["start"][1], len(c["segs"]),
            P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
    print()

dump("/workspace/wdsans/ref/shs/shs-250.otf", "SHS-250", raw=True)
dump("/workspace/wdsans2/build/masters_R32/master-ExtraLight-250.otf", "R32-250")