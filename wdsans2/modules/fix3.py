#!/usr/bin/env python3
# fix3 - 保留 seg4, 只把 seg3 冲出点收到 bar_right (拐角消失)
#
# T6-250: seg3: C c1(341,367) c2(642,511) -> (768,725)
#         seg4: L -> (750,739)
# 方案A: seg3 终点 768->745, c2 也按比例移 (642->619)
# 方案B: seg3 不动, seg4 终点 (750,739) -> (745,739)  (只收一点点)
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

B = "/workspace/wdsans2/build/masters_T6/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
OUT = "/workspace/wdsans2/build/fix3"
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
    f0 = TTFont(B + FN[tag]); gs0 = f0.getGlyphSet(); cm0 = f0.getBestCmap()
    gn = cm0[ord("多")]
    rp = RecordingPen(); gs0[gn].draw(rp); f0.close()
    C = contours_from_pen(rp.value)
    bar_i = body_i = None
    for ci,c in enumerate(C):
        b=bb(c); sig="".join(s[0] for s in c["segs"])
        if b[3]<600: continue
        if sig=="LLL": bar_i=ci
        elif sig=="LCCCL": body_i=ci
    if bar_i is None or body_i is None:
        print("  %s: 跳过 bar=%s body=%s" % (tag,bar_i,body_i)); continue
    bar_right = bb(C[bar_i])[1]
    segs = C[body_i]["segs"]
    s3 = segs[3]
    apex = np.array(s3[-1], float)
    fold = np.array(segs[4][-1], float)
    print("  %s: bar_right=%.0f  seg3: c1=(%.0f,%.0f) c2=(%.0f,%.0f) end=(%.0f,%.0f)  fold=(%.0f,%.0f)" % (
        tag, bar_right, s3[1][0],s3[1][1], s3[2][0],s3[2][1], apex[0],apex[1], fold[0],fold[1]))
    for variant in ["A"]:
        f = TTFont(B + FN[tag])
        g2 = f.getGlyphSet(); c2m = f.getBestCmap()
        NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
        nbd = NEW[body_i]
        # 方案A: seg3 终点 768->bar_right, c2 按 end 的位移同步平移
        dx = bar_right - apex[0]
        c2x = s3[2][0] + dx; c2y = s3[2][1]
        nbd["segs"][3] = ["C", s3[1], (c2x, c2y), (bar_right, apex[1])]
        # seg4 终点同步左移一点保持收尾
        nbd["segs"][4] = ["L", (fold[0] + dx, fold[1])]
        print("        A: seg3 end->%.0f, c2->(%.0f,%.0f), seg4->(%.0f,%.0f)" % (
            bar_right, c2x, c2y, fold[0]+dx, fold[1]))
        cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
        old = csT[gn]
        csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
        f["post"].formatType = 3.0; f["post"].glyphOrder = None
        p = os.path.join(OUT, "A_%s.otf" % tag)
        f.save(p); f.close()
        print("        saved " + p)