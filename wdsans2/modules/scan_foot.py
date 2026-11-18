#!/usr/bin/env python3
# scan_foot - 全库扫: 左偏旁「日/口/囗」底部有出脚的字符
#
# 判据: 字符左侧区域(x < 60% 字宽) 有一个 LLL/LLLL 竖条轮廓,
#       其 y_bottom 明显低于同区域的"外框"轮廓 y_bottom
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

def bb(c):
    pts=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: pts.append(np.array(q,float))
        elif s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q": pts.extend([np.array(s[1],float),np.array(s[2],float)])
        else: pts.append(np.array(s[1],float))
    P=np.array(pts); return P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()

R="/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
f=TTFont(R, lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
cands=[]
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
    rp=RecordingPen()
    try: gs[cm[cp]].draw(rp)
    except Exception: continue
    C=contours_from_pen(rp.value)
    if not C: continue
    allb=[bb(c) for c in C]
    gx0=min(b[0] for b in allb); gx1=max(b[1] for b in allb)
    gw=gx1-gx0
    if gw <= 0: continue
    left_lim = gx0 + gw*0.62
    # 左侧轮廓
    L=[(i,bb(c),"".join(s[0] for s in c["segs"])) for i,c in enumerate(C) if bb(c)[1] < left_lim]
    if len(L) < 2: continue
    # 找最长的"外框"(段数>=5) 作为参照
    frames=[x for x in L if len(x[2])>=5]
    if not frames: continue
    fy0=min(x[1][2] for x in frames)
    # 找竖条(LLL/LLLL) 且底部低于外框
    for i,b,sig in L:
        if sig not in ("LLL","LLLL"): continue
        if b[2] < fy0 - 20:
            cands.append((chr(cp), i, round(b[2]), round(fy0), round(b[2]-fy0)))
            break
f.close()
print("左侧部首底部出脚候选: %d 字" % len(cands))
for c,i,yb,fy,d in cands[:60]:
    print("  %s  轮廓%d 底=%.0f 参照=%.0f 出脚=%.0f" % (c,i,yb,fy,d))