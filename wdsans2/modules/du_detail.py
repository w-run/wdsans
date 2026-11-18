#!/usr/bin/env python3
# du_detail - 都 c6/c7 详细段结构
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

f=TTFont("/workspace/wdsans2/build/masters_R32/master-Regular-400.otf", lazy=True)
gs=f.getGlyphSet(); cm=f.getBestCmap()
rp=RecordingPen(); gs[cm[ord("都")]].draw(rp); f.close()
C=contours_from_pen(rp.value)
for ci in [6, 7]:
    c=C[ci]
    print("c%d %s  起点(%.1f,%.1f)" % (ci, "".join(s[0] for s in c["segs"]), c["start"][0], c["start"][1]))
    for k,s in enumerate(c["segs"]):
        e=s[-1]
        ex=""
        if s[0]=="C": ex="  c1(%.0f,%.0f) c2(%.0f,%.0f)"%(s[1][0],s[1][1],s[2][0],s[2][1])
        print("   %d %-2s -> (%.1f,%.1f)%s" % (k,s[0],e[0],e[1],ex))
    print()