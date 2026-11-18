import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
def allpts(c):
    P=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: P.append(np.array(q,float))
        elif s[0]=="C": P.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q": P.extend([np.array(s[1],float),np.array(s[2],float)])
        else: P.append(np.array(s[1],float))
    return np.array(P)
for lbl,p in [("R32","/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"),
              ("SHS","/workspace/wdsans/ref/shs/shs-400.otf")]:
    f=TTFont(p,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    rp=RecordingPen(); gs[cm[ord("叫")]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    print("%s 叫 (%d contours):" % (lbl, len(C)))
    for ci,c in enumerate(C):
        P=allpts(c); sig="".join(s[0] for s in c["segs"])
        print("  c%2d %-12s x[%4.0f,%4.0f] y[%4.0f,%4.0f]" % (ci,sig[:12],P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()))
    print()