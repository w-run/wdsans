#!/usr/bin/env python3
# rad_same - 验证: 同部首部件的轮廓尺寸是否一致
import sys, json
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

def leftcontours(path, chars):
    f=TTFont(path, lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    out=[]
    for ch in chars:
        if ord(ch) not in cm: continue
        rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp)
        C=contours_from_pen(rp.value)
        if len(C)<2: continue
        ps=[allpts(c) for c in C]
        gx0=min(p[:,0].min() for p in ps); gx1=max(p[:,0].max() for p in ps)
        gw=gx1-gx0
        # 最左侧的轮廓
        cand=[(p[:,0].min(), p, "".join(s[0] for s in c["segs"])) for c,p in zip(C,ps)
              if (p[:,0].min()+p[:,0].max())/2 < gx0+gw*0.45]
        if not cand: continue
        cand.sort(key=lambda x: x[0])
        _, P0, sig = cand[0]
        w=P0[:,0].max()-P0[:,0].min(); h=P0[:,1].max()-P0[:,1].min()
        out.append((ch, round(w), round(h), round(P0[:,1].min()), round(P0[:,1].max()), sig))
    f.close()
    return out

O="/workspace/wdsans/ref/ops/ops-400.ttf"
S="/workspace/wdsans/ref/shs/shs-400.otf"
R="/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
CH="叫叨叩叶叹叽叼叭叮叱"
for lbl,p in [("OPPO",O),("SHS",S),("R32",R)]:
    print("=== %s 口旁字的最左轮廓 ===" % lbl)
    for ch,w,h,y0,y1,sig in leftcontours(p, CH):
        print("  %s  宽%3d 高%3d  y[%4d,%4d]  %s" % (ch,w,h,y0,y1,sig[:12]))
    print()