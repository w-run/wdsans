#!/usr/bin/env python3
"""m_chufoot - 去掉「出」类字的右下伸脚（对齐 OPPO 形态）

用户反馈: 「出」右下出脚没去掉

### 四家实测（400 档，底边）
我们  最低边 x[813,895] 宽 82   <- 只有右竖到底（SHS 形态）
SHS   最低边 x[814,895] 宽 81   <- 同上
HOS   最低边 x[804,885] 宽 81   <- 同上
OPPO  最低边 x[118,870] 宽 752  <- 整个底横到底，无伸脚  <<< 目标

### 轮廓结构（400 档，4 个轮廓）
c0 x[457,539] y[ 18,839]  中竖
c1 x[813,895] y[-79,340]  右下竖  <- 下探到 -79
c2 x[149,855] y[403,748]  上半部
c3 x[104,853] y[-23,339]  下半部轮廓，底横下缘 -23、右端 853

缺陷: 底横右端 853 落在右竖 813~895 内 -> 40 单位重叠，
      且右竖比底横低 56 单位 -> 视觉上是「右下出脚」。

### 修法（纯点坐标移动，不改段数/操作符）
1. 底横右端 x: 853 -> 813（贴住右竖左缘，消除重叠）
2. 右竖下端 y: -79 -> -23（与底横下缘齐平，消除伸脚）
三档天然一致。
"""
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R27')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R28')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}

CAND = '出祟粜屈拙咄础茁黜'


def allpts(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for p in s[1]: P.append(np.array(p, float))
        elif s[0] == "C":
            P.extend([np.array(s[1], float), np.array(s[2], float), np.array(s[3], float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1], float), np.array(s[2], float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)


def find_foot(C, tag=400):
    """找右竖 + 底横的伸脚结构"""
    # 🔴 粗字重笔画变厚：900档竖笔宽可达 164，阈值必须按档位放宽
    MAXW = {250: 110, 400: 140, 900: 200}[tag]
    if len(C) < 2:
        return None
    gx1 = max(allpts(c)[:,0].max() for c in C)
    gy0 = min(allpts(c)[:,1].min() for c in C)
    vert = None
    for i, c in enumerate(C):
        P = allpts(c)
        x0, x1 = P[:,0].min(), P[:,0].max()
        y0, y1 = P[:,1].min(), P[:,1].max()
        w = x1 - x0; h = y1 - y0
        if h > 250 and w < MAXW and x0 > gx1 - 200 and x1 > gx1 - 80 and y0 < gy0 + 50:
            if vert is None or y0 < allpts(C[vert])[:,1].min():
                vert = i
    if vert is None:
        return None
    vP = allpts(C[vert])
    vx0 = vP[:,0].min(); vy0 = vP[:,1].min()
    # 找底横：宽大且 y0 靠字底，右端伸入右竖内
    bar = None
    for i, c in enumerate(C):
        if i == vert:
            continue
        P = allpts(c)
        x0, x1 = P[:,0].min(), P[:,0].max()
        y0 = P[:,1].min()
        w = x1 - x0
        if w < 400:
            continue
        if y0 > gy0 + 120:
            continue
        if x1 - vx0 < 8:     # 未伸入右竖
            continue
        if bar is None or x1 > allpts(C[bar])[:,0].max():
            bar = i
    if bar is None:
        return None
    by0 = allpts(C[bar])[:,1].min()
    bx1 = allpts(C[bar])[:,0].max()
    return {"vert": vert, "bar": bar, "vx0": vx0, "bx1": bx1, "by0": by0, "vy0": vy0}


def fix(C, info):
    vx0 = info["vx0"]; by0 = info["by0"]
    bx1 = info["bx1"]; vy0 = info["vy0"]
    out = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
    # 1) 底横右端 -> vx0
    b = out[info["bar"]]
    ns = list(b["start"])
    if abs(ns[0] - bx1) < 1.0:
        ns[0] = vx0
    segs = []
    for s in b["segs"]:
        if s[0] == "L" and abs(s[1][0] - bx1) < 1.0:
            segs.append(["L", (vx0, s[1][1])])
        else:
            segs.append(s)
    out[info["bar"]] = {"start": tuple(ns), "segs": segs}
    # 2) 右竖下端 -> by0
    if abs(vy0 - by0) < 1.0:
        return None     # 已经齐平，无需改
    v = out[info["vert"]]
    ns2 = list(v["start"])
    if abs(ns2[1] - vy0) < 1.0:
        ns2[1] = by0
    segs2 = []
    for s in v["segs"]:
        if s[0] == "L" and abs(s[1][1] - vy0) < 1.0:
            segs2.append(["L", (s[1][0], by0)])
        else:
            segs2.append(s)
    out[info["vert"]] = {"start": tuple(ns2), "segs": segs2}
    return out


def process(tag):
    src = os.path.join(SRC, FN[tag])
    f = TTFont(src)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    cff2 = f["CFF2"].cff
    td = cff2[cff2.fontNames[0]]
    csT = td.CharStrings
    idxf = "/workspace/wdsans2/build/chufoot_idx.json"
    if tag != "400":
        idx = json.load(open(idxf))
    else:
        idx = []
        for ch in CAND:
            cp = ord(ch)
            if cp not in cm:
                continue
            rp = RecordingPen()
            gs[cm[cp]].draw(rp)
            C = contours_from_pen(rp.value)
            if find_foot(C, 400):
                idx.append(cp)
        json.dump(idx, open(idxf, "w"))
        print("  400档: %d/%d 字命中 %s" % (len(idx), len(CAND), "".join(chr(c) for c in idx)), flush=True)

    done = 0; skip = 0
    for cp in idx:
        gn = cm.get(cp)
        if not gn:
            skip += 1; continue
        rp = RecordingPen()
        gs[gn].draw(rp)
        C = contours_from_pen(rp.value)
        info = find_foot(C, int(tag))
        if not info:
            skip += 1; continue
        NEW = fix(C, info)
        if NEW is None:
            skip += 1; continue
        old = csT[gn]
        try:
            csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
            done += 1
        except Exception:
            skip += 1
    print("  %s档: 改 %d, 跳过 %d" % (tag, done, skip), flush=True)
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    f.save(os.path.join(OUTD, FN[tag]))
    f.close()


if __name__ == "__main__":
    for t in ['400', '250', '900']:
        process(t)
    print("done")
