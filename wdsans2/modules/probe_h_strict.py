#!/usr/bin/env python3
"""严格测横笔端面: 只取纯 L 的细长轮廓（真横笔），看右端上下 x 差"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

FONTS = [("我们","/workspace/static/wdsans/WDesignSans-VF.otf"),
         ("SHS","/workspace/wdsans/ref/shs/shs-400.otf"),
         ("OPPO","/workspace/wdsans/ref/ops/ops-400.ttf"),
         ("HOS","/workspace/wdsans/ref/hos/hos-400.ttf")]
CHARS = ["十","一","二","三","干","工","五","正","生","平"]

def analyze(path, ch):
    f = TTFont(path, lazy=True); cm=f.getBestCmap(); gs=f.getGlyphSet()
    if ord(ch) not in cm: f.close(); return None
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    res=[]
    for c in C:
        segs=c["segs"]
        # 只要纯 L 轮廓
        if any(s[0]!="L" for s in segs): continue
        pts=[tuple(c["start"])]+[tuple(s[1]) for s in segs]
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        w=max(xs)-min(xs); h=max(ys)-min(ys)
        if w < 300 or h > 150 or h < 20: continue   # 细长横笔
        # 找最右 x 的点，看有几个不同 y 共享这个 x
        xr = max(xs)
        right_pts = [(p[0],p[1]) for p in pts if abs(p[0]-xr) < 0.5]
        y_at_right = sorted(set(p[1] for p in right_pts))
        # 端面垂直性: 右边缘的 y 跨度应等于 h（说明整条边都在 xr）
        span = (max(y_at_right)-min(y_at_right)) if len(y_at_right)>1 else 0
        res.append(dict(w=w, h=h, n_right=len(right_pts), span=span,
                        vert=1.0 if abs(span-h)<2 else span/max(1,h)))
    return res

print("=== 横笔右端面垂直性（1.00 = 整条端面在同一 x = 垂直平切）===")
print("%-4s %-6s %6s %6s %8s %8s  %s" % ("字","字体","宽","高","右端点数","垂直度","判定"))
print("-"*64)
ACC={}
for ch in CHARS:
    for lbl,p in FONTS:
        r = analyze(p,ch)
        if not r: continue
        for it in r:
            v = "垂直平切" if it["vert"] > 0.98 else ("近似垂直" if it["vert"]>0.85 else "斜切")
            print("%-4s %-6s %6.0f %6.0f %8d %8.3f  %s" % (
                ch,lbl,it["w"],it["h"],it["n_right"],it["vert"],v))
            ACC.setdefault(lbl,[]).append(it["vert"])
    print()
print("=== 汇总垂直度均值 ===")
for lbl,_ in FONTS:
    v=ACC.get(lbl)
    if v: print("  %-6s %.3f  (%d 个横笔)" % (lbl, float(np.mean(v)), len(v)))
