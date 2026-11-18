#!/usr/bin/env python3
# scan_by0 - 全库扫描: body末点y 与 bar下缘不一致的情况 (400档检测)
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

R = "/workspace/wdsans2/build/masters_R31/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}

# 400 档检测出候选 (轮廓索引, seg索引)
f = TTFont(R + FN["400"], lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
hits = []
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
    rp = RecordingPen()
    try:
        gs[cm[cp]].draw(rp)
    except Exception:
        continue
    C = contours_from_pen(rp.value)
    bars = [i for i,c in enumerate(C) if bb(c)[3] > 600 and "".join(s[0] for s in c["segs"]) == "LLL"]
    for bi in bars:
        bbv = bb(C[bi]); bar_bot = bbv[2]; bar_right = bbv[1]
        for ci, c in enumerate(C):
            if ci == bi: continue
            sig = "".join(s[0] for s in c["segs"])
            if sig not in ("LCCC","LCLC"): continue
            b = bb(c)
            if b[3] <= 600 or b[1] < 700: continue
            end = np.array(c["segs"][-1][-1], float)
            if abs(end[0] - bar_right) > 3: continue
            hits.append((cp, bi, ci, len(c["segs"])-1, bar_bot, bar_right, end[1]))
            break
f.close()
print("400档候选: %d 处 / %d 字" % (len(hits), len(set(h[0] for h in hits))))

# 套用到三档, 统计 dy
tot = {"250":0,"400":0,"900":0}
bad = {"250":0,"400":0,"900":0}
for tag in ["250","400","900"]:
    ft = TTFont(R + FN[tag], lazy=True); g = ft.getGlyphSet(); cmm = ft.getBestCmap()
    for cp, bi, ci, ei, bbot400, bright400, eend400 in hits:
        if cp not in cmm: continue
        rp = RecordingPen()
        try:
            g[cmm[cp]].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        if bi >= len(C) or ci >= len(C): continue
        bbv = bb(C[bi])
        end = np.array(C[ci]["segs"][ei][-1], float) if ei < len(C[ci]["segs"]) else None
        if end is None: continue
        tot[tag] += 1
        if abs(end[1] - bbv[2]) > 1: bad[tag] += 1
    ft.close()
print("三档 dy 不一致统计:")
for tag in ["250","400","900"]:
    print("  %s: %d / %d 需修正 (%.0f%%)" % (tag, bad[tag], tot[tag], 100.0*bad[tag]/max(tot[tag],1)))