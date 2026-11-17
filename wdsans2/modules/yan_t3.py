import sys, os
sys.path.insert(0,'/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from canonpen3 import contours_from_pen
B='/workspace/wdsans2/build/'
cands=['masters_T1','masters_T2','masters_T3','masters_T4','masters_T5','masters_T6']
for d in cands:
    p=B+d+'/master-Regular-400.otf'
    if not os.path.exists(p):
        print('  %-12s (不存在)'%d); continue
    f=TTFont(p,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    rp=DecomposingRecordingPen(gs); gs[cm[ord('眼')]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    found=None
    for c in C:
        pts=[np.array(c['start'],float)]
        for s in c['segs']:
            if s[0]=='QM':
                for q in s[1]: pts.append(np.array(q,float))
            elif s[0]=='C': pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
            elif s[0]=='Q': pts.extend([np.array(s[1],float),np.array(s[2],float)])
            else: pts.append(np.array(s[1],float))
        P=np.array(pts)
        if 400<P[:,0].min()<470 and 650<P[:,0].max()<720 and P[:,1].max()<150:
            tip=P[np.argmax(P[:,0])]
            found=(round(tip[0]),round(tip[1]),len(c['segs']),''.join(s[0] for s in c['segs']))
    print('  %-12s %s'%(d, str(found) if found else '(无 c4)'))
