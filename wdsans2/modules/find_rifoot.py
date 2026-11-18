#!/usr/bin/env python3
# find_rifoot - 精确找「日/口/囗 偏旁 + 底部竖笔外伸」的字
#
# 「都」的诊断(400档):
#   c6 LLLLLL x[147,471] y[-16,374]  日的外框
#   c7 LLL    x[442,514] y[-60,374]  日右竖, 比外框低 44
# 对照组(仰/似/倒) 必须 0 命中
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

def find(C):
    if len(C) < 3: return None
    boxes=[]
    for i,c in enumerate(C):
        sig="".join(s[0] for s in c["segs"])
        if len(sig) < 5: continue
        P=allpts(c); x0,x1=P[:,0].min(),P[:,0].max(); y0,y1=P[:,1].min(),P[:,1].max()
        w,h=x1-x0,y1-y0
        if w<100 or h<100: continue
        if not (0.35 < w/h < 2.8): continue
        boxes.append((i,x0,x1,y0,y1))
    if not boxes: return None
    for i,c in enumerate(C):
        sig="".join(s[0] for s in c["segs"])
        if sig not in ("LLL","LLLL"): continue
        P=allpts(c); x0,x1=P[:,0].min(),P[:,0].max(); y0,y1=P[:,1].min(),P[:,1].max()
        w,h=x1-x0,y1-y0
        if h<150 or w>h*0.6: continue
        for bi,bx0,bx1,by0,by1 in boxes:
            if bi==i: continue
            if x0 > bx1-5 or x1 < bx1-120: continue
            if not (by0-5 <= y1 <= by1+5): continue   # 竖条顶端与方框齐
            d = by0 - y0
            if 20 < d < 90:
                return (bi,i,round(d))
    return None

R="/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
f=TTFont(R, lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
hits=[]
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
    rp=RecordingPen()
    try: gs[cm[cp]].draw(rp)
    except Exception: continue
    r=find(contours_from_pen(rp.value))
    if r: hits.append((chr(cp),)+r)
f.close()
print("命中 %d 字" % len(hits))
print("  " + "".join(h[0] for h in hits[:80]))
print()
抽查对照组 (应为空):")
ctl=set("仰似倒假做修代件住你他们")
bad=[h for h in hits if h[0] in ctl]
print("  误报: %s" % (bad if bad else "无"))