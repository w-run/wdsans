#!/usr/bin/env python3
"""rend.py - 精确渲染: 所有曲线展平为折线, 避免 QM 处理错误"""
import sys, os, subprocess
import numpy as np
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
from fontTools.pens.basePen import BasePen


class FlatPen(BasePen):
    def __init__(self, gs, steps=40):
        super().__init__(gs)
        self.steps = steps
        self.subs = []
        self.cur = None

    def _moveTo(self, p):
        self.cur = [tuple(p)]
        self.subs.append(self.cur)

    def _lineTo(self, p):
        self.cur.append(tuple(p))

    def _curveToOne(self, p1, p2, p3):
        p0 = np.array(self.cur[-1], float)
        c1 = np.array(p1, float); c2 = np.array(p2, float); p3a = np.array(p3, float)
        for i in range(1, self.steps + 1):
            t = i / self.steps; mt = 1 - t
            q = mt**3*p0 + 3*mt*mt*t*c1 + 3*mt*t*t*c2 + t**3*p3a
            self.cur.append((q[0], q[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = np.array(self.cur[-1], float)
        c1 = np.array(p1, float); p2a = np.array(p2, float)
        for i in range(1, self.steps + 1):
            t = i / self.steps; mt = 1 - t
            q = mt*mt*p0 + 2*mt*t*c1 + t*t*p2a
            self.cur.append((q[0], q[1]))

    def _closePath(self):
        pass


def load_flat(fp, ch):
    f = TTFont(fp)
    cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    gs = f.getGlyphSet()
    pen = FlatPen(gs, 40)
    gs[cm[ord(ch)]].draw(pen)
    f.close()
    return pen.subs


def svg_path(subs):
    out = []
    for sub in subs:
        out.append('M %.2f %.2f' % (sub[0][0], -sub[0][1]))
        for p in sub[1:]:
            out.append('L %.2f %.2f' % (p[0], -p[1]))
        out.append('Z')
    return ' '.join(out)


def render(fp, ch, win, path, w=700):
    subs = load_flat(fp, ch)
    if subs is None:
        return None
    x0, x1, y0, y1 = win
    vx = x0; vy = -y1; vw = x1 - x0; vh = y1 - y0
    hh = int(w * vh / vw)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="%f %f %f %f"><rect x="%f" y="%f" width="%f" height="%f" fill="white"/>'
           '<path d="%s" fill="black"/></svg>') % (w, hh, vx, vy, vw, vh, vx, vy, vw, vh, svg_path(subs))
    open(path, 'w').write(svg)
    pp = path.replace('.svg', '.png')
    subprocess.run(['rsvg-convert', '-w', str(w), path, '-o', pp], capture_output=True)
    return pp


def full_bbox(fp, ch):
    subs = load_flat(fp, ch)
    if not subs:
        return None
    P = np.vstack([np.array(s) for s in subs])
    return float(P[:, 0].min()), float(P[:, 0].max()), float(P[:, 1].min()), float(P[:, 1].max())
