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
for lbl,p in [("T6","/workspace/wdsans2/build/masters_T6/master-ExtraLight-250.otf"),
              ("R34","/workspace/wdsans2/build/masters_R34/master-ExtraLight-250.otf"),
              ("SHS","/workspace/wdsans/ref/shs/shs-250.otf")]:
    f=TTFont(p,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    rp=RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    print("=== %s ===" % lbl)
    for ci,c in enumerate(C):
        P=allpts(c); sig="".join(s[0] for s in c["segs"])
        if P[:,1].max() < 600: continue
        print("  c%d %-8s nseg=%d x[%4.0f,%4.0f] y[%4.0f,%4.0f]" % (ci,sig,len(c["segs"]),P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()))
        if len(c["segs"])>=4:
            for k,s in enumerate(c["segs"]):
                e=s[-1]; ex=""
                if s[0]=="C": ex=" c1(%.0f,%.0f) c2(%.0f,%.0f)"%(s[1][0],s[1][1],s[2][0],s[2][1])
                print("      %d %s -> (%.0f,%.0f)%s"%(k,s[0],e[0],e[1],ex))
    print()