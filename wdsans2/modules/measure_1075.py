#!/usr/bin/env python3
# measure_1075 - 测 1075 字的左偏旁居中偏差 (vs OPPO)
# 左偏旁 = x 在左侧 45% 内、段数>=5 的封闭方框轮廓
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

def box_info(path, cps):
    f=TTFont(path, lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    out={}
    for cp in cps:
        if cp not in cm: continue
        rp=RecordingPen()
        try: gs[cm[cp]].draw(rp)
        except Exception: continue
        C=contours_from_pen(rp.value)
        if len(C)<2: continue
        ps=[allpts(c) for c in C]
        gx0=min(p[:,0].min() for p in ps); gx1=max(p[:,0].max() for p in ps)
        gw=gx1-gx0
        if gw<=0: continue
        # 左偏旁: x 中心在左 45%, 段数>=5
        box=[]; rest=[]
        for c,p in zip(C,ps):
            cx=(p[:,0].min()+p[:,0].max())/2
            if cx < gx0+gw*0.45 and len("".join(s[0] for s in c["segs"]))>=5:
                box.append(p)
            else:
                rest.append(p)
        if not box or not rest: continue
        by0=min(p[:,1].min() for p in box); by1=max(p[:,1].max() for p in box)
        ry0=min(p[:,1].min() for p in rest); ry1=max(p[:,1].max() for p in rest)
        out[cp]=((by0+by1)/2.0, (ry0+ry1)/2.0)
    f.close()
    return out

cps=json.load(open("/workspace/wdsans2/build/box_lr.json"))
print("加载 %d 字" % len(cps), flush=True)
R=box_info("/workspace/wdsans2/build/masters_R32/master-Regular-400.otf", cps)
print("R32: %d 字有左偏旁" % len(R), flush=True)
O=box_info("/workspace/wdsans/ref/ops/ops-400.ttf", cps)
print("OPPO: %d" % len(O), flush=True)
print()
ds=[]
for cp in R:
    if cp not in O: continue
    lc, rc = R[cp]
    lo, ro = O[cp]
    d = (lc-rc) - (lo-ro)
    ds.append((d, chr(cp)))
if ds:
    vals=sorted(x[0] for x in ds)
    import statistics
    print("我们 vs OPPO 的居中偏差 (正=我们偏高):")
    print("  n=%d  中位 %.0f  均值 %.0f" % (len(vals), statistics.median(vals), sum(vals)/len(vals)))
    print("  分位: P10=%.0f P25=%.0f P75=%.0f P90=%.0f" % (
        vals[int(len(vals)*.1)], vals[int(len(vals)*.25)],
        vals[int(len(vals)*.75)], vals[int(len(vals)*.9)]))
    print("  偏差>30 的字数: %d" % sum(1 for v in vals if v>30))
    print("  偏差<-30 的字数: %d" % sum(1 for v in vals if v<-30))
    ds.sort(key=lambda x:-abs(x[0]))
    print("  最大 15: " + " ".join("%s%+.0f"%(c,d) for d,c in ds[:15]))