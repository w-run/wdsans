#!/usr/bin/env python3
# tail250 - 撇末端 (seg2终点/seg3) 细节: R31 vs R32 vs T6
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

def dump(path, lbl):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    for c in C:
        sig = "".join(s[0] for s in c["segs"])
        if sig != "LCCC": continue
        pts=[np.array(c["start"],float)]
        for s in c["segs"]:
            if s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
            else: pts.append(np.array(s[1],float))
        P=np.array(pts)
        if P[:,1].max()<600 or P[:,0].max()<600: continue
        print("=== %s ===" % lbl)
        print("  起点 (%.1f,%.1f)" % (c["start"][0], c["start"][1]))
        for k,s in enumerate(c["segs"]):
            e = s[-1]
            ex = ""
            if s[0]=="C":
                ex = "  c1=(%.0f,%.0f) c2=(%.0f,%.0f)" % (s[1][0],s[1][1],s[2][0],s[2][1])
            print("   %d %-2s -> (%.1f,%.1f)%s" % (k,s[0],e[0],e[1],ex))
        # 末端厚度: seg2终点(内缘起) 到 seg3最后一段的距离
        p_in = np.array(c["segs"][2][-1], float)
        p_end = np.array(c["segs"][3][-1], float)
        print("   seg2终点(内缘) (%.1f,%.1f)  seg3终点 (%.1f,%.1f)  dx=%.0f dy=%.0f" % (
            p_in[0],p_in[1],p_end[0],p_end[1], p_end[0]-p_in[0], p_end[1]-p_in[1]))
        print()
        return

for p, l in [("/workspace/wdsans2/build/masters_T6/master-ExtraLight-250.otf","T6-250"),
             ("/workspace/wdsans2/build/masters_R31/master-ExtraLight-250.otf","R31-250"),
             ("/workspace/wdsans2/build/masters_R32/master-ExtraLight-250.otf","R32-250")]:
    dump(p, l)