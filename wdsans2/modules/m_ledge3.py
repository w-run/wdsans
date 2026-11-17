#!/usr/bin/env python3
"""m_ledge3 - 横折出头 v3：加「右侧阻挡」判据

🔴 m_ledge (v2) 的严重误报:
  R15 -> R16 实际改动 2645 字，其中 2033 字单点位移 > 150 单位。
  最严重 601 单位（覴），把左侧偏旁的横笔拖到字面右界。

根因: 判据只要求「横笔靠近字顶 + 够宽」，
      没检查横笔右侧是否还有其它部件（左右结构字）。
  例: 到 x[61,578] -> x[70,822]，把「至」的横笔拉过「刂」。
      理 x[53,947] 的横笔是「王」的，拉过去盖住「里」。

v3 新增「右侧阻挡」判据:
  横笔 y 带内，右侧若存在其它轮廓 -> 该横笔不是整字顶横 -> 跳过
  只有右侧完全空旷（上下结构，如 各/冬/条/备/务）才延伸。
"""
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R15')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_L3')
FNMAP = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}

TARGET = {250: 35.0, 400: 90.0, 900: 110.0}
MIN_RATIO = 2.8
MAX_H = {250: 60.0, 400: 200.0, 900: 300.0}
MIN_W = 300


def endp(s):
    if s[0]=='QM': return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def bbox_of(c):
    P = np.array([[c["start"][0],c["start"][1]]] + [[endp(s)[0],endp(s)[1]] for s in c["segs"]], float)
    return P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()


def find_bar(C, tag):
    gx1 = max(bbox_of(c)[1] for c in C)
    gy1 = max(bbox_of(c)[3] for c in C)
    best = None
    for ci, c in enumerate(C):
        segs = c['segs']
        if not all(s[0]=="L" for s in segs):
            continue
        if len(segs) not in (3, 4):
            continue
        x0, x1, y0, y1 = bbox_of(c)
        w = x1 - x0; h = max(y1 - y0, 1)
        if w < MIN_W:
            continue
        if w / h < MIN_RATIO:
            continue
        if h > MAX_H[tag]:
            continue
        if y1 < gy1 - 150:
            continue
        if best is None or y1 > best[0]:
            best = (y1, ci, x0, x1, y0, y1)
    if not best:
        return None
    y1, ci, bx0, bx1, by0, by1 = best
    # 🔴 v3 新增: 右侧阻挡检查
    for j, c in enumerate(C):
        if j == ci:
            continue
        ox0, ox1, oy0, oy1 = bbox_of(c)
        if oy1 < by0 or oy0 > by1:
            continue
        if ox0 > bx1 + 2:
            return None      # 右侧有部件 -> 不是整字顶横
    return best


def apply_extend(C, bar, target):
    y1, ci, bx0, bx1, by0, by1 = bar
    gx1 = max(bbox_of(c)[1] for c in C)
    want = gx1 - target
    if bx1 >= want - 0.5:
        return None
    c = C[ci]
    maxx = max([c["start"][0]] + [endp(s)[0] for s in c["segs"]])
    ns = np.array(c["start"], float)
    if abs(ns[0] - maxx) < 0.5:
        ns[0] = want
    new_segs = []
    for s in c["segs"]:
        if s[0] == "L" and abs(s[1][0] - maxx) < 0.5:
            new_segs.append(("L", (want, s[1][1])))
        else:
            new_segs.append(s)
    out = list(C)
    out[ci] = {"start": (ns[0], ns[1]), "segs": new_segs}
    return out


def process(tag):
    src = os.path.join(SRC, FNMAP[tag])
    f = TTFont(src)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    cff2 = f['CFF2'].cff
    td = cff2[cff2.fontNames[0]]
    csT = td.CharStrings

    idxf = "/workspace/wdsans2/build/ledge3_idx.json"
    if tag != "400":
        idx = json.load(open(idxf))
    else:
        idx = {}
        for cp, gn in cm.items():
            if not (0x4E00 <= cp <= 0x9FFF):
                continue
            rp = RecordingPen()
            try:
                gs[gn].draw(rp)
            except Exception:
                continue
            C = contours_from_pen(rp.value)
            b = find_bar(C, 400)
            if not b:
                continue
            gx1 = max(bbox_of(x)[1] for x in C)
            if gx1 - b[3] > TARGET[400] + 0.5:
                idx[str(cp)] = True
        json.dump(idx, open(idxf, "w"))
        print("  400档检测: %d 字" % len(idx), flush=True)

    done = 0; skip = 0
    for cps in idx:
        cp = int(cps)
        gn = cm.get(cp)
        if not gn:
            skip += 1; continue
        rp = RecordingPen()
        gs[gn].draw(rp)
        C = contours_from_pen(rp.value)
        b = find_bar(C, int(tag))
        if not b:
            skip += 1; continue
        NEW = apply_extend(C, b, TARGET[int(tag)])
        if NEW is None:
            skip += 1; continue
        old = csT[gn]
        try:
            csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
            done += 1
        except Exception:
            skip += 1

    print("  %s档: 改 %d, 跳过 %d" % (tag, done, skip), flush=True)
    f['post'].formatType = 3.0
    f['post'].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    f.save(os.path.join(OUTD, FNMAP[tag]))
    f.close()


for t in ['400', '250', '900']:
    process(t)
print('done')