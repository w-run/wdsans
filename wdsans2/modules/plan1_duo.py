#!/usr/bin/env python3
# plan1_duo - 方案1 试验: 横笔延伸到字面右缘 + 斜切端面, 仅「多」, 三档
#
# 设计:
#   T6 body c1 末端有  C->(796,726)  L->(748,756)  即 SHS 的拐角
#   方案1: 横笔 bar 右端延到 TARGET_X(T6 的 796 或字面右界)
#          然后从 bar 右上角斜切到 body 的斜边, 形成单一斜切面
#   三档各自计算, 但保存统一的段结构 (点数量/类型一致) -> VF 安全
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

B = "/workspace/wdsans2/build/masters_T6/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
OUTD = "/workspace/wdsans2/build/plan1"
os.makedirs(OUTD, exist_ok=True)

def bbox(c):
    pts = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: pts.append(np.array(q, float))
        elif s[0] == "C":
            pts.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
        elif s[0] == "Q":
            pts.extend([np.array(s[1],float), np.array(s[2],float)])
        else:
            pts.append(np.array(s[1], float))
    P = np.array(pts)
    return P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()

for tag in ["250","400","900"]:
    src = B + FN[tag]
    f = TTFont(src)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    gn = cm[ord("多")]
    rp = RecordingPen(); gs[gn].draw(rp)
    C = contours_from_pen(rp.value)
    # 找 bar(LLL 上横) 和 body(LCCCL, 含拐角)
    bar_i = None; body_i = None
    for ci, c in enumerate(C):
        b = bbox(c)
        if b[3] < 600: continue
        sig = "".join(s[0] for s in c["segs"])
        if sig == "LLL" and bar_i is None:
            bar_i = ci
        elif sig == "LCCCL":
            body_i = ci
    if bar_i is None or body_i is None:
        print("  %s: 未找到目标轮廓 bar=%s body=%s" % (tag, bar_i, body_i))
        f.close(); continue
    bar = C[bar_i]; body = C[body_i]
    bb = bbox(bar); bd = bbox(body)
    # body 的斜切段: seg3 -> (px,py)  seg4(L) -> (qx,qy)
    s3 = body["segs"][3]; s4 = body["segs"][4]
    p3 = np.array(s3[-1], float)
    p4 = np.array(s4[-1], float)
    print("  %s: bar x[%.0f,%.0f] y[%.0f,%.0f] | body seg3->(%.0f,%.0f) seg4->(%.0f,%.0f)" % (
        tag, bb[0], bb[1], bb[2], bb[3], p3[0], p3[1], p4[0], p4[1]))
    # 方案1: bar 右端 -> max(p3.x, p4.x, bb[1])  即延伸到斜切顶点
    target_x = max(p3[0], p4[0])
    # bar 上缘 y, 下缘 y
    y_top = bb[3]; y_bot = bb[2]
    NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
    # 1) bar 右端延到 target_x (起点 + seg2 终点)
    nb = NEW[bar_i]
    nb["start"] = (target_x, nb["start"][1])
    s2 = nb["segs"][2]
    nb["segs"][2] = ["L", (target_x, s2[-1][1])]
    # 2) body: seg3 终点 -> (target_x, y_top); seg4 终点 -> (target_x - sw*?, y_top) 形成斜切
    nbd = NEW[body_i]
    sw = y_top - y_bot   # 横笔厚度，用作斜切宽度参考
    nbd["segs"][3] = ["C", s3[1], s3[2], (target_x, y_top)]
    nbd["segs"][4] = ["L", (target_x, y_top + (p4[1]-p3[1]))] if False else ["L", (p4[0], y_top)]
    print("       -> bar右端 %.0f, body seg3->(%.0f,%.0f) seg4->(%.0f,%.0f)" % (
        target_x, target_x, y_top, p4[0], y_top))
    cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
    old = csT[gn]
    csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType = 3.0; f["post"].glyphOrder = None
    p = os.path.join(OUTD, "P1_%s.otf" % tag)
    f.save(p); f.close()
    print("       saved " + p)