#!/usr/bin/env python3
# plan1c - 三个变体一起试, 找最接近 OPPO 的形态
#
# C1: seg3->(tx, y_top), 删 seg4, bar->tx   (body 闭合边 = 横笔上缘)
# C2: seg3->(tx, y_bot), 删 seg4, bar->tx   (body 闭合边 = 横笔下缘)
# C3: seg3->(tx, y_mid), 删 seg4, bar->tx
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

B = "/workspace/wdsans2/build/masters_T6/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
OUTD = "/workspace/wdsans2/build/p1c"
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

for tag in ["250","400"]:
    src = B + FN[tag]
    for variant in ["c1","c2","c3"]:
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
            f.close(); continue
        bar = C[bar_i]; body = C[body_i]
        bb = bbox(bar)
        apex = np.array(body["segs"][3][-1], float)
        fold = np.array(body["segs"][4][-1], float)
        tx = max(apex[0], fold[0])
        y_top, y_bot = bb[3], bb[2]
        ty = {"c1": y_top, "c2": y_bot, "c3": (y_top+y_bot)/2.0}[variant]
        NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
        nb = NEW[bar_i]
        nb["start"] = (tx, nb["start"][1])
        s2 = nb["segs"][2]
        nb["segs"][2] = ["L", (tx, s2[-1][1])]
        nbd = NEW[body_i]
        s3 = nbd["segs"][3]
        nbd["segs"][3] = ["C", s3[1], s3[2], (tx, ty)]
        del nbd["segs"][4:]
        cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
        old = csT[gn]
        csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
        f["post"].formatType = 3.0; f["post"].glyphOrder = None
        p = os.path.join(OUTD, "%s_%s.otf" % (variant, tag))
        f.save(p); f.close()
        print("  %s %s: tx=%.0f ty=%.0f (y_top=%.0f y_bot=%.0f)" % (variant, tag, tx, ty, y_top, y_bot))