#!/usr/bin/env python3
"""m_ledge - 顶部横笔右端延伸（横折出头）

问题（AGENTS.md 第 7 节「横折出头」，代表字 丝 延 各）:

量化发现（2026-11-15，fontTools 精确点位）:
  顶部横笔的右端余量（字形右界 - 横笔右端）:
    字    我们    OPPO    HOS
    各    171     121     0
    冬    180     135     0
    条    206     122     0
    备    191     122     0
    务    126     126     0

  -> 我们的顶部横笔右端收得太紧，比 OPPO 平均多 60 em，比 HOS 多 160 em
  -> 视觉上就是「横折不出头」，OPPO/HOS 的横笔更向右侧伸展

修法:
  找「顶部横笔」（4 点纯 L 轮廓、宽 >= 3.5×高、y 接近字形顶部），
  把该横笔右端的 2 个点延伸到目标位置:
    目标右端 = 字形右界 - target_margin
  只移动这 2 个点的 x，不动其它点 -> 三档段数/操作符不变

目标余量（按字重缩放，OPPO/HOS 居中取 90）:
  250: 35   400: 90   900: 175

🔴 必须三档预筛：若某档找不到合格横笔或延伸会导致负宽度，整字跳过
"""
import sys, os, json
import numpy as np
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_MOD26')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD29')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}
TARGET_MARGIN = {'250': 35.0, '400': 90.0, '900': 110.0}
MIN_RATIO = 2.8         # 宽/高 至少 2.8（900档横笔 h 可达 127，比例自然降至 3.3）
MAX_H = {'250': 60.0, '400': 200.0, '900': 300.0}


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def cpts(c):
    P = [np.array(c['start'], float)]
    for s in c['segs']:
        P.append(endp(s))
    return np.array(P, float)


def find_top_bar(C, max_h):
    """找顶部横笔: 4 点纯 L、宽/高 >= MIN_RATIO、y 最高"""
    if not C:
        return None
    allP = np.vstack([cpts(c) for c in C])
    gy1 = allP[:, 1].max()
    gx1 = allP[:, 0].max()
    best = None
    for ci, c in enumerate(C):
        if len(c['segs']) != 3:
            continue
        if any(s[0] != 'L' for s in c['segs']):
            continue
        P = cpts(c)
        if len(P) != 4:
            continue
        w = float(P[:, 0].max() - P[:, 0].min())
        h = float(P[:, 1].max() - P[:, 1].min())
        if h <= 0 or h > max_h:
            continue
        if w / h < MIN_RATIO:
            continue
        ymax = float(P[:, 1].max())
        if ymax < gy1 - 150:
            continue          # 不是顶部
        if best is None or ymax > best[0]:
            best = (ymax, ci, P, w, h, gx1)
    return best


def apply_extend(C, bar, target_margin):
    """把横笔右端 2 个点的 x 延伸到 字形右界 - target_margin"""
    ymax, ci, P, w, h, gx1 = bar
    x_target = gx1 - target_margin
    # 当前右端
    x_cur = float(P[:, 0].max())
    if x_target <= x_cur + 1:
        return None            # 不需要延伸
    c = C[ci]
    NEW = []
    for k, cc in enumerate(C):
        if k != ci:
            NEW.append({'start': (cc['start'][0], cc['start'][1]),
                        'segs': [list(x) for x in cc['segs']]})
            continue
        # 该轮廓 4 点纯 L: start = p0, segs[i] 终点 = p(i+1)
        pts = cpts(cc)
        # 找出 x 最大的点索引（右端 2 个）
        order = np.argsort(-pts[:, 0])
        right_idx = set(int(i) for i in order[:2])
        new_start = pts[0].copy()
        if 0 in right_idx:
            new_start[0] = x_target
        new_segs = []
        for m, s in enumerate(cc['segs']):
            e = np.array(s[1], float)
            if (m + 1) in right_idx:
                e[0] = x_target
            new_segs.append(['L', (float(e[0]), float(e[1]))])
        NEW.append({'start': (float(new_start[0]), float(new_start[1])),
                    'segs': new_segs})
    return NEW


def try_apply(gs, gn, tag):
    rp = RecordingPen()
    try:
        gs[gn].draw(rp)
    except Exception:
        return None
    C = contours_from_pen(rp.value)
    bar = find_top_bar(C, MAX_H[tag])
    if bar is None:
        return None
    return apply_extend(C, bar, TARGET_MARGIN[tag])


def seg_signature(contours):
    return '|'.join(''.join('C' if s[0] == 'C' else 'Q' if s[0] == 'Q'
                            else 'M' if s[0] == 'QM' else 'L' for s in c['segs'])
                    for c in contours)


def main():
    os.makedirs(OUTD, exist_ok=True)
    cjk = None
    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        if cjk is None:
            cm = f.getBestCmap()
            cjk = [(cp, gn) for cp, gn in cm.items() if 0x4E00 <= cp <= 0x9FFF]
            print('扫描 %d 个 CJK…' % len(cjk), flush=True)
        f.close()
        break

    gss = {}
    for tag in ['250', '400', '900']:
        ff = TTFont(SRC + '/' + FN[tag], lazy=True)
        gss[tag] = ff.getGlyphSet()

    # 三档预筛：三档都必须能应用
    index = []
    for cp, gn in cjk:
        ok = True
        for tag in ['250', '400', '900']:
            if try_apply(gss[tag], gn, tag) is None:
                ok = False
                break
        if ok:
            index.append({'g': gn, 'cp': cp})
    for tag in ['250', '400', '900']:
        gss[tag].font.close() if hasattr(gss[tag], 'font') else None
    print('三档都能延伸: %d 字' % len(index), flush=True)
    with open('/workspace/wdsans2/build/idx_ledge.json', 'w') as fh:
        json.dump(index, fh)
    if not index:
        return

    sigs = {}
    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        gs = f.getGlyphSet()
        cff2 = f['CFF2'].cff
        td = cff2[cff2.fontNames[0]]
        csT = td.CharStrings
        done = 0
        sig_map = {}
        for it in index:
            gn = it['g']
            NEW = try_apply(gs, gn, tag)
            if NEW is None:
                continue
            old = csT[gn]
            csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
            sig_map[gn] = seg_signature(NEW)
            done += 1
        sigs[tag] = sig_map
        print('  %s: 应用 %d' % (tag, done), flush=True)
        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()

    common = set(sigs['250']) & set(sigs['400']) & set(sigs['900'])
    bad = [g for g in common
           if not (sigs['250'][g] == sigs['400'][g] == sigs['900'][g])]
    print()
    print('三档都改: %d 字' % len(common))
    print('签名不一致: %d 字 %s' % (len(bad), bad[:6]), flush=True)


main()
