#!/usr/bin/env python3
# m_by0align - 新模块: 让 bar/body 接合点的 y 跟随各档自己的横笔下缘
#
# 根因: m_barple 写入固定 (xR, by0), by0 来自 400 档检测 ->
#       250 档 body 末点比横笔底低 23 单位 (撇尖冒出 = 异常线条)
#       900 档 body 末点比横笔底高 35 单位 (断点 = 台阶)
#
# 修法: 400 档定位 (bi, ci, ei), 三档各自取本档 bar 下缘作为 body 末点 y
#       只移动一个点的 y -> 段数/操作符不变 -> VF 安全
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get("WDS_SRC", "/workspace/wdsans2/build/masters_R31")
OUT = os.environ.get("WDS_OUT", "/workspace/wdsans2/build/masters_R32")
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
os.makedirs(OUT, exist_ok=True)

def bb(c):
    pts=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: pts.append(np.array(q,float))
        elif s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q": pts.extend([np.array(s[1],float),np.array(s[2],float)])
        else: pts.append(np.array(s[1],float))
    P=np.array(pts); return P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()

# ---- 1) 400 档检测: 找 (字形, bar轮廓idx, body轮廓idx) ----
f4 = TTFont(os.path.join(SRC, FN["400"]), lazy=True)
gs4 = f4.getGlyphSet(); cm4 = f4.getBestCmap()
idx = {}
if __name__ == "__main__":
    for cp in [c for c in cm4 if 0x4E00 <= c <= 0x9FFF]:
        rp = RecordingPen()
        try:
            gs4[cm4[cp]].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        for bi, c in enumerate(C):
            if "".join(s[0] for s in c["segs"]) != "LLL": continue
            bv = bb(c)
            if bv[3] <= 600: continue
            for ci, c2 in enumerate(C):
                if ci == bi: continue
                sig = "".join(s[0] for s in c2["segs"])
                if sig not in ("LCCC","LCLC"): continue
                b2 = bb(c2)
                if b2[3] <= 600 or b2[1] < 700: continue
                end = np.array(c2["segs"][-1][-1], float)
                if abs(end[0] - bv[1]) > 3: continue
                idx[cp] = [bi, ci]
                break
            if cp in idx: break
    f4.close()
    print("400档定位: %d 字" % len(idx))

    # ---- 2) 三档套用 ----
    for tag in ["250","400","900"]:
        src = os.path.join(SRC, FN[tag])
        ft = TTFont(src)
        gs = ft.getGlyphSet(); cmm = ft.getBestCmap()
        iso = ft.getGlyphOrder()
        n_fix = 0
        for cp, (bi, ci) in idx.items():
            if cp not in cmm: continue
            gn = cmm[cp]
            rp = RecordingPen()
            try:
                gs[gn].draw(rp)
            except Exception:
                continue
            C = contours_from_pen(rp.value)
            if bi >= len(C) or ci >= len(C): continue
            bar_bot = bb(C[bi])[2]
            segs = C[ci]["segs"]
            if not segs: continue
            end = np.array(segs[-1][-1], float)
            if abs(end[1] - bar_bot) < 1: continue
            NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
            last = list(NEW[ci]["segs"][-1])
            last[-1] = (end[0], bar_bot)
            NEW[ci]["segs"][-1] = last
            cff2 = ft["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
            old = csT[gn]
            csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
            n_fix += 1
        ft["post"].formatType = 3.0; ft["post"].glyphOrder = None
        p = os.path.join(OUT, FN[tag])
        ft.save(p); ft.close()
        print("  %s: 修正 %d 字 -> %s" % (tag, n_fix, p))

    json.dump({str(k): v for k, v in idx.items()}, open(os.path.join(OUT, "index.json"), "w"))
    print("done")
