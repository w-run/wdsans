#!/usr/bin/env python3
"""verify_misalign - 验证 16px 碎裂是否来自 x 方向错位

方法: 对每个字，找出其所有轮廓，检查是否有【本应相连但 x 错开 1-3 单位】的接缝。
与 SHS 对比。
"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

F = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
}
CHARS = "数边全景政治必价以京这规法还海"

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

def near_miss(path, ch):
    """找两个轮廓之间 x 错开 1~4 单位、y 重叠的接缝"""
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen()
    try: gs[cm[ord(ch)]].draw(rp)
    except Exception:
        f.close(); return None
    f.close()
    C = contours_from_pen(rp.value)
    if len(C) < 2: return 0
    ps = [allpts(c) for c in C]
    n = 0
    for i in range(len(ps)):
        for j in range(i+1, len(ps)):
            a, b = ps[i], ps[j]
            ax0, ax1 = a[:,0].min(), a[:,0].max()
            bx0, bx1 = b[:,0].min(), b[:,0].max()
            ay0, ay1 = a[:,1].min(), a[:,1].max()
            by0, by1 = b[:,1].min(), b[:,1].max()
            # y 有重叠
            if ay1 < by0 or by1 < ay0: continue
            ov = min(ay1,by1) - max(ay0,by0)
            if ov < 50: continue
            # x 接近但不相交（间隙 0~4）
            gap = max(ax0 - bx1, bx0 - ax1)
            if 0 < gap <= 4:
                n += 1
    return n

print("=== 轮廓间 x 间隙 0~4 单位的接缝数（y 重叠 >=50）===")
print("%-4s %8s %8s   %s" % ("字", "我们", "SHS", "判定"))
tot_a = tot_b = 0
for ch in CHARS:
    a = near_miss(F["我们"], ch)
    b = near_miss(F["SHS"], ch)
    if a is None or b is None: continue
    tot_a += a; tot_b += b
    flag = "!!" if a > b else ""
    print("%-4s %8d %8d   %s" % (ch, a, b, flag))
print()
print("合计: 我们 %d / SHS %d  (差 %+d)" % (tot_a, tot_b, tot_a-tot_b))
