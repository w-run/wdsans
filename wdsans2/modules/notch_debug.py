#!/usr/bin/env python3
# notch_debug - 多 250 R32: 横笔右端 vs body 在横笔上缘处的 x
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

for path, lbl in [("/workspace/wdsans2/build/masters_R32/master-ExtraLight-250.otf","R32-250"),
                   ("/workspace/wdsans/ref/ops/ops-400.ttf","OPPO")]:
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    qt = lbl == "OPPO"
    print("=== %s ===" % lbl)
    if qt:
        for i,(op,args) in enumerate(rp.value):
            if op == "closePath": print("  %2d close" % i); continue
            if op == "moveTo": print("  %2d move (%.0f,%.0f)" % (i,args[0][0],args[0][1])); continue
            if op == "lineTo": print("  %2d line (%.0f,%.0f)" % (i,args[0][0],args[0][1])); continue
            if op == "qCurveTo":
                print("  %2d qCurve " % i + " ".join("(%.0f,%.0f)"%(p[0],p[1]) if p else "None" for p in args)); continue
        print()
        continue
    C = contours_from_pen(rp.value)
    for ci, c in enumerate(C):
        pts=[np.array(c["start"],float)]
        for s in c["segs"]:
            if s[0]=="QM":
                for q in s[1]: pts.append(np.array(q,float))
            elif s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
            elif s[0]=="Q": pts.extend([np.array(s[1],float),np.array(s[2],float)])
            else: pts.append(np.array(s[1],float))
        P=np.array(pts)
        if P[:,1].max() < 600 or P[:,0].max() < 600: continue
        sig="".join(s[0] for s in c["segs"])
        print("  c%d %-8s x[%.0f,%.0f] y[%.0f,%.0f]" % (ci,sig,P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()))
        print("     起点(%.1f,%.1f)" % (c["start"][0],c["start"][1]))
        for k,s in enumerate(c["segs"]):
            e=s[-1]; ex=""
            if s[0]=="C": ex="  c1(%.0f,%.0f) c2(%.0f,%.0f)"%(s[1][0],s[1][1],s[2][0],s[2][1])
            print("      %d %-2s -> (%.1f,%.1f)%s"%(k,s[0],e[0],e[1],ex))
    print()