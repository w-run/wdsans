#!/usr/bin/env python3
"""run_boxrad - 400档检测 + 三档套用 (VF 安全)

铁律: 三档各自检测会让命中集不同(实测 250档少14字) -> VF 构建失败。
做法: 400档检测出 (左偏旁轮廓索引列表), 三档套用同一索引,
      但每档用本档的 y 坐标计算拉伸量。
"""
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_boxrad

SRC = os.environ.get("WDS_SRC", "/workspace/wdsans2/build/masters_R32")
OUT = os.environ.get("WDS_OUT", "/workspace/wdsans2/build/masters_R33")
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
SW = {"250":29.0, "400":67.0, "900":127.0}
BASE_EXTEND, BASE_SW = 80.0, 67.0
os.makedirs(OUT, exist_ok=True)

cps = json.load(open("/workspace/wdsans2/build/box_lr.json"))

# ---- 1) 400 档检测: 记录左偏旁轮廓索引 ----
m_boxrad.BOTTOM_EXTEND = BASE_EXTEND
f4 = TTFont(os.path.join(SRC, FN["400"]), lazy=True)
gs4 = f4.getGlyphSet(); cm4 = f4.getBestCmap()
idx = {}
for cp in cps:
    if cp not in cm4: continue
    rp = RecordingPen()
    try: gs4[cm4[cp]].draw(rp)
    except Exception: continue
    C = contours_from_pen(rp.value)
    r = m_boxrad.split_lr(C)
    if not r: continue
    left, right = r
    idx[cp] = left
f4.close()
print("400档检测: %d 字有左偏旁" % len(idx))

# ---- 2) 三档套用同一索引 ----
for tag in ["250","400","900"]:
    ext = BASE_EXTEND * (SW[tag] / BASE_SW)
    src = os.path.join(SRC, FN[tag])
    f = TTFont(src)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
    n = 0; bad = 0
    for cp, left in idx.items():
        if cp not in cm:
            bad += 1; continue
        gn = cm[cp]
        rp = RecordingPen()
        try: gs[gn].draw(rp)
        except Exception:
            bad += 1; continue
        C = contours_from_pen(rp.value)
        if not left or max(left) >= len(C):
            bad += 1; continue
        # 本档 y 范围
        ps = [m_boxrad.allpts(c) for c in C]
        ly0 = min(ps[i][:,1].min() for i in left)
        ly1 = max(ps[i][:,1].max() for i in left)
        lh = ly1 - ly0
        if lh <= 0:
            bad += 1; continue
        new_y0 = ly0 - ext
        new_y1 = ly1
        th = new_y1 - new_y0
        NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
        for i in left:
            c = C[i]
            def ty(v, _y0=ly0, _lh=lh, _ny0=new_y0, _th=th):
                return _ny0 + (v - _y0) / _lh * _th
            st = c["start"]
            NEW[i]["start"] = (st[0], ty(st[1]))
            for k, s in enumerate(c["segs"]):
                ns = list(s)
                if s[0] == "QM":
                    ns[1] = [(q[0], ty(q[1])) for q in s[1]]
                elif s[0] == "C":
                    ns[1] = (s[1][0], ty(s[1][1]))
                    ns[2] = (s[2][0], ty(s[2][1]))
                    ns[3] = (s[3][0], ty(s[3][1]))
                elif s[0] == "Q":
                    ns[1] = (s[1][0], ty(s[1][1]))
                    ns[2] = (s[2][0], ty(s[2][1]))
                else:
                    ns[1] = (s[1][0], ty(s[1][1]))
                NEW[i]["segs"][k] = ns
        old = csT[gn]
        csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
        n += 1
    f["post"].formatType = 3.0; f["post"].glyphOrder = None
    p = os.path.join(OUT, FN[tag])
    f.save(p); f.close()
    print("  %s: 改动 %d, 异常 %d  (extend=%.0f)" % (tag, n, bad, ext))

json.dump({str(k): v for k, v in idx.items()}, open(os.path.join(OUT,"boxrad_index.json"), "w"))
print("done -> " + OUT)