import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_c2lift
f=TTFont("/workspace/wdsans2/build/masters_R34/master-Regular-400.otf",lazy=True)
gs=f.getGlyphSet(); cm=f.getBestCmap()
rp=RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
C=contours_from_pen(rp.value)
for bi,bar in enumerate(C):
    sig="".join(s[0] for s in bar["segs"])
    if sig!="LLL" or len(bar["segs"])!=3: continue
    pb=m_c2lift.allpts(bar)
    bw=pb[:,0].max()-pb[:,0].min(); bh=pb[:,1].max()-pb[:,1].min()
    print("bar c%d: w=%.0f h=%.0f ratio=%.2f right=%.0f bot=%.0f top=%.0f" % (bi,bw,bh,bw/bh,pb[:,0].max(),pb[:,1].min(),pb[:,1].max()))
    print("  过 ratio 检验:", bw/bh >= 1.8 and bw >= 200)
for ci,body in enumerate(C):
    sig="".join(s[0] for s in body["segs"])
    if len(body["segs"])!=4: continue
    pb2=m_c2lift.allpts(body)
    e=np.array(body["segs"][3][3],float)
    print("body c%d sig=%s end=(%.0f,%.0f) ymax=%.0f" % (ci,sig,e[0],e[1],pb2[:,1].max()))
print()
print("find() ->", m_c2lift.find(C))