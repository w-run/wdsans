#!/usr/bin/env python3
"""m_ledge2 - 横折出头 v3: 覆盖「人字头」结构的顶部横笔

m_ledge (v2) 的 ymax 判据 `ymax < gy1 - 150` 排除了人字头字:
  朵  gmax=807 横笔 y1=807  -> 命中
  俞  gmax=845 横笔 y1=586  -> 差 259，被排除
  舍  gmax=847 横笔 y1=581  -> 差 266，被排除
  禽  gmax=845 横笔 y1=612  -> 差 233，被排除
  拿  gmax=860 横笔 y1=667  -> 差 193，被排除

原因: 人字头的撇捺从横笔上方升起，gmax 比横笔高 200~280。

v3 修正:
  1. ymax 窗口 150 -> 320
  2. 新增「居中」判据: |横笔中心 - 字面中心| <= 120
     （排除 村/辞/拜 等左侧偏旁的横笔）
  3. 新增「横笔上方无更宽横笔」检查，确保抓到的是主横笔

几何动作与 v2 完全一致（只平移 2 个点的 x，不动段数/操作符）
-> 三档天然一致。
"""
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R25')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R26')
TAGS = ['250', '400', '900']
FNMAP = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}

TARGET_MARGIN = {250: 35.0, 400: 90.0, 900: 110.0}
MIN_RATIO = 2.8
MAX_H = {250: 60.0, 400: 200.0, 900: 300.0}
YMAX_WIN = 320
CEN_TOL = 120
MIN_W = 300


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def allpts(C):
    xs = []; ys = []
    for c in C:
        xs.append(c['start'][0]); ys.append(c['start'][1])
        for s in c['segs']:
            if s[0] == 'QM':
                for p in s[1]:
                    xs.append(p[0]); ys.append(p[1])
            elif s[0] == 'C':
                xs.extend([s[1][0], s[2][0], s[3][0]])
                ys.extend([s[1][1], s[2][1], s[3][1]])
            elif s[0] == 'Q':
                xs.extend([s[1][0], s[2][0]])
                ys.extend([s[1][1], s[2][1]])
            else:
                xs.append(s[1][0]); ys.append(s[1][1])
    return min(xs), max(xs), min(ys), max(ys)


def find_bar(C, tag):
    """找居中的顶部主横笔: 3或4点纯L、宽/高>=MIN_RATIO、y 靠近顶部、居中"""
    gx0, gx1, gy0, gy1 = allpts(C)
    gcen = (gx0 + gx1) / 2
    best = None
    for ci, c in enumerate(C):
        segs = c['segs']
        if not all(s[0] == "L" for s in segs):
            continue
        if len(segs) not in (3, 4):
            continue
        P = np.array([[c["start"][0], c["start"][1]]] +
                     [[endp(s)[0], endp(s)[1]] for s in segs], float)
        x0, x1 = P[:, 0].min(), P[:, 0].max()
        y0, y1 = P[:, 1].min(), P[:, 1].max()
        w = x1 - x0; h = max(y1 - y0, 1)
        if w < MIN_W:
            continue
        if w / h < MIN_RATIO:
            continue
        if h > MAX_H[tag]:
            continue
        if y1 < gy1 - YMAX_WIN:
            continue
        cen = (x0 + x1) / 2
        if abs(cen - gcen) > CEN_TOL:
            continue
        if best is None or y1 > best[0]:
            best = (y1, ci, P, w, h, gx1, x0, x1)
    return best


def apply_extend(C, bar, target):
    y1, ci, P, w, h, gx1, x0, x1 = bar
    want = gx1 - target
    if x1 >= want - 0.5:
        return None      # 已经够长
    # 把该轮廓中 x 最大的点右移到 want
    maxx = P[:, 0].max()
    idxs = [i for i in range(len(P)) if abs(P[i, 0] - maxx) < 0.5]
    if not idxs or len(idxs) > 3:
        return None
    c = C[ci]
    new_start = np.array(c['start'], float)
    if abs(new_start[0] - maxx) < 0.5:
        new_start[0] = want
    new_segs = []
    for s in c["segs"]:
        if s[0] == 'L':
            p = np.array(s[1], float)
            if abs(p[0] - maxx) < 0.5:
                p[0] = want
            new_segs.append(['L', (p[0], p[1])])
        elif s[0] == 'C':
            new_segs.append(s)
        elif s[0] == 'Q':
            new_segs.append(s)
        else:
            new_segs.append(s)
    nc = {"start": (new_start[0], new_start[1]), "segs": new_segs}
    out = list(C)
    out[ci] = nc
    return out


def process(tag):
    src = os.path.join(SRC, FNMAP[tag])
    f = TTFont(src)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    cff2 = f['CFF2'].cff
    td = cff2[cff2.fontNames[0]]
    csT = td.CharStrings

    idx = {}
    if tag != "400":
        idx = json.load(open('/workspace/wdsans2/build/ledge2_idx.json'))
    else:
        target = TARGET_MARGIN[400]
        cjk = [(cp, gn) for cp, gn in cm.items() if 0x4E00 <= cp <= 0x9FFF]
        for cp, gn in cjk:
            rp = RecordingPen()
            try:
                gs[gn].draw(rp)
            except Exception:
                continue
            C = contours_from_pen(rp.value)
            b = find_bar(C, tag)
            if not b:
                continue
            if b[5] - b[7] <= target + 0.5:
                continue
            idx[str(cp)] = True
        json.dump(idx, open('/workspace/wdsans2/build/ledge2_idx.json', 'w'))
        print('  400档检测: %d 字' % len(idx), flush=True)

    done = 0; skip = 0
    for cps in idx:
        cp = int(cps)
        gn = cm.get(cp)
        if not gn:
            skip += 1; continue
        rp = RecordingPen()
        gs[gn].draw(rp)
        C = contours_from_pen(rp.value)
        b = find_bar(C, tag)
        if not b:
            skip += 1; continue
        NEW = apply_extend(C, b, TARGET_MARGIN[int(tag)])
        if NEW is None:
            skip += 1; continue
        old = csT[gn]
        try:
            csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
            done += 1
        except Exception:
            skip += 1

    print('  %s档: 改 %d, 跳过 %d' % (tag, done, skip), flush=True)
    f['post'].formatType = 3.0
    f['post'].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    f.save(os.path.join(OUTD, FNMAP[tag]))
    f.close()


for t in TAGS:
    process(t)
print('完成')