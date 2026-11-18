#!/usr/bin/env python3
"""endcut_audit - 笔末切角量化审计（此前未系统验证）

方法: 对每个字形，找「横笔」轮廓（窄长矩形），测其右端面的倾斜量。
      端面垂直 = 右上角与右下角 x 相同 -> dx = 0

对照组: 十/一/二/三/工/王 这类纯横笔字，三家都应是垂直端面。
"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS": "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS": "/workspace/wdsans/ref/hos/hos-400.ttf",
}

def allpts(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: P.append(np.array(q, float))
        elif s[0] == "C":
            P.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1],float), np.array(s[2],float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)

def bar_end_slant(C):
    """找横笔轮廓，返回右端面倾斜量列表 (dx, bar_h)"""
    out = []
    for c in C:
        P = allpts(c)
        x0, x1 = P[:,0].min(), P[:,0].max()
        y0, y1 = P[:,1].min(), P[:,1].max()
        w, h = x1-x0, y1-y0
        if h <= 0 or w/h < 4.0 or w < 150:
            continue          # 不是横笔
        # 右端: 取 x 接近 x1 的点 (容差 3), 看它们的 y 范围
        sel = P[P[:,0] > x1 - 3]
        if len(sel) < 2:
            continue
        # 上缘与下缘在右端处的 x
        top = P[np.abs(P[:,1] - y1) < 3]
        bot = P[np.abs(P[:,1] - y0) < 3]
        if len(top) < 2 or len(bot) < 2:
            continue
        tx = top[:,0].max()
        bx = bot[:,0].max()
        out.append((abs(tx - bx), h))
    return out

CHARS = "十一二三工王土地士干平正生目日田口回中申甲"
print("=== 横笔端面倾斜量 (dx, em单位; 0 = 完全垂直) ===")
print("%-6s %-22s %-22s %-22s %s" % ("字", "我们", "SHS", "OPPO", "HOS"))
agg = {}
for name, path in FONTS.items():
    try:
        f = TTFont(path, lazy=True)
        gs = f.getGlyphSet(); cm = f.getBestCmap()
        vals = []
        for ch in CHARS:
            if ord(ch) not in cm: continue
            rp = RecordingPen()
            try: gs[cm[ord(ch)]].draw(rp)
            except Exception: continue
            C = contours_from_pen(rp.value)
            for dx, h in bar_end_slant(C):
                vals.append(dx)
        f.close()
        agg[name] = vals
    except Exception as e:
        agg[name] = []

rows = []
for ch in CHARS:
    rows.append(ch)
print()
print("%-8s %-10s %-10s %-10s %-10s" % ("字体", "n", "中位dx", "均值dx", "最大dx"))
for name in FONTS:
    v = agg.get(name, [])
    if not v:
        print("%-8s (无数据)" % name); continue
    print("%-8s %-10d %-10.1f %-10.1f %-10.1f" % (
        name, len(v), float(np.median(v)), float(np.mean(v)), float(np.max(v))))
