#!/usr/bin/env python3
# run_radfoot2 - 400档检测 + 三档套用 (VF安全)
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_radfoot

SRC = "/workspace/wdsans2/build/masters_R33"
OUT = "/workspace/wdsans2/build/masters_R34"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
CHARS = "僘厥塑嵞朔槊磊蒴都鬬鬭"
os.makedirs(OUT, exist_ok=True)

# 1) 400档检测: 记录 (box_idx, vert_idx)
f4 = TTFont(os.path.join(SRC, FN["400"]), lazy=True)
gs4 = f4.getGlyphSet(); cm4 = f4.getBestCmap()
idx = {}
for ch in CHARS:
    if ord(ch) not in cm4: continue
    rp = RecordingPen()
    try: gs4[cm4[ord(ch)]].draw(rp)
    except Exception: continue
    C = contours_from_pen(rp.value)
    h = m_radfoot.find(C)
    if h: idx[ord(ch)] = [(x[0], x[1]) for x in h]
f4.close()
print("400档检测: %d 字 -> %s" % (len(idx), "".join(chr(k) for k in idx)))

# 2) 三档套用同一索引, 用本档的方框底缘作为目标 y
for tag in ["250","400","900"]:
    f = TTFont(os.path.join(SRC, FN[tag]))
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
    n = 0; bad = 0
    for cp, pairs in idx.items():
        if cp not in cm:
            bad += 1; continue
        gn = cm[cp]
        rp = RecordingPen()
        try: gs[gn].draw(rp)
        except Exception:
            bad += 1; continue
        C = contours_from_pen(rp.value)
        ps = [m_radfoot.allpts(c) for c in C]
        NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
        ok = True
        for bi, vi in pairs:
            if bi >= len(C) or vi >= len(C):
                ok = False; break
            target_y = ps[bi][:,1].min()   # 本档方框底缘
            c = NEW[vi]
            cur_y = ps[vi][:,1].min()      # 本档竖条底端
            st = c["start"]
            if abs(st[1] - cur_y) < 2:
                c["start"] = (st[0], target_y)
            for k, s in enumerate(c["segs"]):
                ns = list(s)
                if s[0] == "L" and abs(s[1][1] - cur_y) < 2:
                    ns[1] = (s[1][0], target_y)
                elif s[0] == "C":
                    if abs(s[3][1] - cur_y) < 2:
                        ns[3] = (s[3][0], target_y)
                    if abs(s[1][1] - cur_y) < 2:
                        ns[1] = (s[1][0], target_y)
                    if abs(s[2][1] - cur_y) < 2:
                        ns[2] = (s[2][0], target_y)
                c["segs"][k] = ns
        if not ok:
            bad += 1; continue
        old = csT[gn]
        csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
        n += 1
    f["post"].formatType = 3.0; f["post"].glyphOrder = None
    p = os.path.join(OUT, FN[tag])
    f.save(p); f.close()
    print("  %s: 改动 %d, 异常 %d" % (tag, n, bad))
print("done -> " + OUT)