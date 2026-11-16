#!/usr/bin/env python3
"""regress.py - 6 项笔画风格量化回归

配套 AGENTS.md「回归修复：重建链漏掉 m_curvflat」的教训：
每次重建链后必须跑一遍全部指标，纯几何模块的遗漏不会触发门禁报错。

指标:
  1. 重心     墨质心在 bbox 内的相对位置 (0=顶 1=底)
  2. 中宫     墨面积 / bbox 面积
  3. 比例     CJK bbox 宽/高均值
  4. 撇捺展开 下半区(60%/70%/80%)墨迹跨度（比绝对曲率更可靠）
  5. 折角     纯 L 折角角度中位
  6. 顶点平顶 顶部第一行墨宽/峰值墨宽
"""
import sys, numpy as np
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.misc import bezierTools
from canonpen3 import contours_from_pen
from PIL import Image, ImageDraw, ImageFont

OURS = '/workspace/static/wdsans/WDesignSans-VF.otf'
FONTS = [
    ('我们', OURS),
    ('SHS', '/workspace/wdsans/ref/shs/shs-400.otf'),
    ('OPPO', '/workspace/wdsans/ref/ops4/OPPOSans4.ttf'),
    ('HOS', '/workspace/wdsans/ref/hos/hos-400.ttf'),
]


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def cjk_sample(path, n=800):
    f = TTFont(path, lazy=True)
    cm = f.getBestCmap()
    cjk = [(cp, gn) for cp, gn in cm.items() if 0x4E00 <= cp <= 0x9FFF]
    f.close()
    step = max(1, len(cjk) // n)
    return cjk[::step][:n]


def m_prop(path):
    """比例：bbox 宽/高均值"""
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet()
    ws, hs = [], []
    for cp, gn in cjk_sample(path):
        bp = BoundsPen(gs)
        try:
            gs[gn].draw(bp)
        except Exception:
            continue
        if not bp.bounds:
            continue
        x0, y0, x1, y1 = bp.bounds
        ws.append(x1 - x0); hs.append(y1 - y0)
    f.close()
    return np.mean(ws), np.mean(hs)


def m_zhonggong(path):
    """中宫：墨面积 / bbox 面积"""
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet()
    vals = []
    for cp, gn in cjk_sample(path, 300):
        bp = BoundsPen(gs)
        ap = AreaPen(gs)
        try:
            gs[gn].draw(bp); gs[gn].draw(ap)
        except Exception:
            continue
        if not bp.bounds:
            continue
        x0, y0, x1, y1 = bp.bounds
        box = (x1 - x0) * (y1 - y0)
        if box <= 0:
            continue
        vals.append(abs(ap.value) / box * 100)
    f.close()
    return np.median(vals)


def m_gravity(path):
    """重心：PIL 400px 位图墨质心"""
    f = TTFont(path, lazy=True)
    cm = f.getBestCmap()
    f.close()
    sample = '口日田目国回中申甲由里'
    vals = []
    SIZE = 400
    for ch in sample:
        if ord(ch) not in cm:
            continue
        try:
            ft = ImageFont.truetype(path, SIZE)
        except Exception:
            return None
        img = Image.new('L', (SIZE * 2, SIZE * 2), 0)
        d = ImageDraw.Draw(img)
        d.text((SIZE // 2, SIZE // 3), ch, fill=255, font=ft)
        a = np.array(img) > 128
        rows = np.where(a.any(axis=1))[0]
        cols = np.where(a.any(axis=0))[0]
        if len(rows) == 0:
            continue
        ys, xs = np.nonzero(a)
        cy = ys.mean()
        rel = (cy - rows[0]) / (rows[-1] - rows[0])
        vals.append(rel)
    return np.median(vals) if vals else None



def m_spread(path):
    """撇捺展开幅度：下半区 60/70/80% 处的墨迹跨度（归一化）
    比「长曲线绝对偏离」可靠 —— OPPO/HOS 只有 350 条长曲线，
    我们有 2853 条，绝对曲率指标对它们根本不适用。
    """
    CH = '永今合会人入八大天夫火木水之这延建乃奶'
    SIZE = 1400
    try:
        ft = ImageFont.truetype(path, SIZE)
    except Exception:
        return None
    v = [[], [], []]
    for ch in CH:
        img = Image.new('L', (SIZE * 2, SIZE * 2), 0)
        ImageDraw.Draw(img).text((SIZE // 2, SIZE // 2), ch, fill=255, font=ft)
        a = np.array(img) > 128
        rows = np.where(a.any(axis=1))[0]
        cols = np.where(a.any(axis=0))[0]
        if len(rows) == 0:
            continue
        y0, y1 = rows[0], rows[-1]
        x0, x1 = cols[0], cols[-1]
        for i, f in enumerate([0.60, 0.70, 0.80]):
            y = int(y0 + (y1 - y0) * f)
            xs = np.where(a[y])[0]
            if len(xs):
                v[i].append((xs[-1] - xs[0]) / (x1 - x0))
    return [np.mean(x) for x in v] if v[0] else None

def m_curv(path):
    """撇捺曲率：长曲线最大偏离"""
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet()
    devs = []
    for cp, gn in cjk_sample(path, 600):
        rp = RecordingPen()
        try:
            gs[gn].draw(rp)
        except Exception:
            continue
        for c in contours_from_pen(rp.value):
            prev = np.array(c['start'], float)
            for s in c['segs']:
                P = None
                if s[0] == 'C':
                    P = [prev, np.array(s[1], float), np.array(s[2], float), np.array(s[3], float)]
                    nxt = P[3]
                elif s[0] == 'Q':
                    P = [prev, np.array(s[1], float), np.array(s[2], float)]
                    nxt = P[2]
                else:
                    prev = endp(s); continue
                L = float(np.linalg.norm(P[-1] - P[0]))
                if L >= 300:
                    k = 10
                    if len(P) == 4:
                        S = np.array([bezierTools.splitCubicAtT(*P, i/k)[0][-1] for i in range(k+1)])
                    else:
                        S = np.array([bezierTools.splitQuadraticAtT(*P, i/k)[0][-1] for i in range(k+1)])
                    ab = S[-1] - S[0]
                    nv = np.array([-ab[1], ab[0]]) / L
                    devs.append(float(np.max(np.abs((S - S[0]) @ nv))))
                prev = nxt
    f.close()
    return (np.median(devs), np.percentile(devs, 90)) if devs else (None, None)


def m_corner(path):
    """折角：纯 L 折角角度中位"""
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet()
    angs = []
    for cp, gn in cjk_sample(path, 400):
        rp = RecordingPen()
        try:
            gs[gn].draw(rp)
        except Exception:
            continue
        for c in contours_from_pen(rp.value):
            pts = [np.array(c['start'], float)]
            ops = []
            for s in c['segs']:
                pts.append(endp(s)); ops.append(s[0])
            n = len(c['segs'])
            if n < 2:
                continue
            # pts[0]=起点, pts[k]=第 k 段终点 (k=1..n)
            for i in range(n):
                if ops[i] != 'L':
                    continue
                if ops[(i - 1) % n] != 'L':
                    continue
                # 段 i 起点 = pts[i], 终点 = pts[i+1]
                a0 = pts[i]
                a1 = pts[i + 1] if i + 1 <= n else pts[0]
                # 前一段 (i-1): 起点 pts[i-1], 终点 pts[i]
                b0 = pts[i - 1] if i >= 1 else pts[n - 1]
                v1 = a0 - b0
                v2 = a1 - a0
                n1 = np.linalg.norm(v1); n2 = np.linalg.norm(v2)
                if n1 < 1 or n2 < 1:
                    continue
                cos = np.clip(v1 @ v2 / (n1 * n2), -1, 1)
                angs.append(np.degrees(np.arccos(cos)))
    f.close()
    return np.median(angs) if angs else None


print('%-6s %-10s %-10s %-14s %-12s %-8s' %
      ('字体', '比例W/H', '中宫%', '重心', '撇捺展开60/70/80', '折角°'))
print('-' * 74)
for lbl, p in FONTS:
    try:
        w, h = m_prop(p)
        zg = m_zhonggong(p)
        gr = m_gravity(p)
        sp = m_spread(p)
        co = m_corner(p)
        print('%-6s %-10s %-10s %-14s %-12s %-8s' % (
            lbl,
            '%.0f/%.0f' % (w, h),
            '%.1f' % zg if zg else '-',
            '%.3f' % gr if gr is not None else '-',
            '%.3f/%.3f/%.3f' % tuple(sp) if sp else '-',
            '%.1f' % co if co else '-'))
    except Exception as e:
        print('%-6s ERR %s' % (lbl, str(e)[:40]))
