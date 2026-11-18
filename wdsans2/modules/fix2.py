#!/usr/bin/env python3
# fix2 - 只删回折段, 不拉横笔 (保留 T6 的横笔长度)
#
# T6-250: bar x->745,  body seg3->(768,725) seg4->(750,739)
# 方案: 删除 seg4 (回折段), 把 seg3 终点收到 (745, 725)
#       即横笔不动, 撇的冲出点收到横笔端点
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

B = "/workspace/wdsans2/build/masters_T6/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
OUT = "/workspace/wdsans2/build/fix2"
os.makedirs(OUT, exist_ok=True)

def bb(c):
    pts=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: pts.append(np.array(q,float))
        elif s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        else: pts.append(np.array(s[1],float))
    P=np.array(pts); return P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()

for tag in ["250","400","900"]:
    f = TTFont(B + FN[tag])
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    gn = cm[ord("多")]
    rp = RecordingPen(); gs[gn].draw(rp)
    C = contours_from_pen(rp.value)
    bar_i = body_i = None
    for ci,c in enumerate(C):
        b=bb(c); sig="".join(s[0] for s in c["segs"])
        if b[3]<600: continue
        if sig=="LLL": bar_i=ci
        elif sig=="LCCCL": body_i=ci
    if bar_i is None or body_i is None:
        print("  %s: bar=%s body=%s" % (tag,bar_i,body_i)); f.close(); continue
    bar_bb = bb(C[bar_i])
    bar_right = bar_bb[1]
    segs = C[body_i]["segs"]
    apex = np.array(segs[3][-1], float)
    fold = np.array(segs[4][-1], float)
    print("  %s: bar_right=%.0f apex=(%.0f,%.0f) fold=(%.0f,%.0f)" % (
        tag, bar_right, apex[0],apex[1], fold[0],fold[1]))
    NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
    nbd = NEW[body_i]
    s3 = nbd["segs"][3]
    # seg3 终点 x 收到 bar_right, y 保持 apex.y
    nbd["segs"][3] = ["C", s3[1], s3[2], (bar_right, apex[1])]
    del nbd["segs"][4:]
    print("       -> seg3->(%.0f,%.0f), seg4删除, bar不动" % (bar_right, apex[1]))
    cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
    old = csT[gn]
    csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType = 3.0; f["post"].glyphOrder = None
    p = os.path.join(OUT, "D_%s.otf" % tag)
    f.save(p); f.close()
    print("       saved " + p)