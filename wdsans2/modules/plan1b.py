#!/usr/bin/env python3
# plan1b - 方案1 修正: 保留 body seg3 顶点, 只删回折段, bar 对齐到该顶点
#
# T6 250 c1: 起点(743,736) L->(736,736) C->(93,342) C->(110,313)
#            C->(768,725)  <- 拐角顶点(冲出点)
#            L->(750,739)  <- 回折段(要删)
# bar c2:    (745,737)->(400,737)->(400,708)->(745,708)
#
# 方案1b: 删 seg4, bar 右端 -> seg3终点.x (768);
#         seg3终点 y 保持不变(725), 这样斜边斜率自然延续
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

B = "/workspace/wdsans2/build/masters_T6/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
OUTD = "/workspace/wdsans2/build/plan1b"
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
    bar_i = None; body_i = None
    for ci, c in enumerate(C):
        b = bbox(c)
        if b[3] < 600: continue
        sig = "".join(s[0] for s in c["segs"])
        if sig == "LLL" and bar_i is None: bar_i = ci
        elif sig == "LCCCL": body_i = ci
    if bar_i is None or body_i is None:
        print("  %s: bar=%s body=%s" % (tag, bar_i, body_i)); f.close(); continue
    bar = C[bar_i]; body = C[body_i]
    bb = bbox(bar)
    apex = np.array(body["segs"][3][-1], float)   # 拐角顶点
    fold = np.array(body["segs"][4][-1], float)   # 回折终点
    tx = max(apex[0], fold[0])
    print("  %s: bar x1=%.0f  apex=(%.0f,%.0f)  fold=(%.0f,%.0f)  -> tx=%.0f" % (
        tag, bb[1], apex[0], apex[1], fold[0], fold[1], tx))
    NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
    nb = NEW[bar_i]
    nb["start"] = (tx, nb["start"][1])
    s2 = nb["segs"][2]
    nb["segs"][2] = ["L", (tx, s2[-1][1])]
    nbd = NEW[body_i]
    # 保留 seg3 的 y，只把 x 对齐到 tx；删掉 seg4 回折
    s3 = nbd["segs"][3]
    nbd["segs"][3] = ["C", s3[1], s3[2], (tx, apex[1])]
    del nbd["segs"][4:]
    print("       -> bar->%.0f, body seg3->(%.0f,%.0f), seg4 删除, 剩 %d 段" % (
        tx, tx, apex[1], len(nbd["segs"])))
    cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
    old = csT[gn]
    csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType = 3.0; f["post"].glyphOrder = None
    p = os.path.join(OUTD, "B_%s.otf" % tag)
    f.save(p); f.close()
    print("       saved " + p)