#!/usr/bin/env python3
# verify_R33 - 三档效果验证 vs SHS
import sys, json
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_boxrad

D="/workspace/wdsans2/build/masters_R33/"
FN={"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
SN={250:"shs-250.otf",400:"shs-400.otf",900:"shs-900.otf"}
idx=json.load(open(D+"boxrad_index.json"))

def leftbox(path, ch, left_ids=None):
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    if ord(ch) not in cm: f.close(); return None
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    ps=[m_boxrad.allpts(c) for c in C]
    if left_ids is None:
        gx0=min(p[:,0].min() for p in ps); gx1=max(p[:,0].max() for p in ps); gw=gx1-gx0
        cand=[]
        for i,p in enumerate(ps):
            x0,x1=p[:,0].min(),p[:,0].max(); y0,y1=p[:,1].min(),p[:,1].max()
            w=x1-x0; h=y1-y0
            if w<100 or h<100: continue
            if not (0.25<w/h<2.5): continue
            if x0>gx0+gw*0.25: continue
            cand.append(i)
        if not cand: return None
        left_ids=[cand[0]]
    y0=min(ps[i][:,1].min() for i in left_ids); y1=max(ps[i][:,1].max() for i in left_ids)
    return y0,y1,y1-y0,(y0+y1)/2

CH="叫叨叩叽叮叱昨晴暗晚旺昧昭昕晌晖明"
for w in [250,400,900]:
    print("=== %d 档 ===" % w)
    print("%-2s | %-30s | %-30s" % ("ch","R33","SHS"))
    ok=0; tot=0
    for ch in CH:
        lid = idx.get(str(ord(ch)))
        a=leftbox(D+FN[str(w)], ch, lid)
        b=leftbox("/workspace/wdsans/ref/shs/"+SN[w], ch)
        if not a or not b: continue
        tot+=1
        dh = abs(a[2]-b[2]); dc = abs(a[3]-b[3])
        if dh<25 and dc<25: ok+=1
        print("  %-2s | h%3.0f c%3.0f                 | h%3.0f c%3.0f                 | dh%+3.0f dc%+3.0f" % (
            ch, a[2],a[3], b[2],b[3], a[2]-b[2], a[3]-b[3]))
    print("  --> %d/%d 匹配(误差<25)" % (ok,tot))
    print()