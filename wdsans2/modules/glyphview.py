#!/usr/bin/env python3
"""glyphview.py - 字体字形对比查看器

功能:
  - 整字视图 / 按 em 坐标矩形裁剪放大
  - 可选坐标网格 (每 50/100 em 单位)
  - 多字体并排对比
  - 曲线一律走 SVGPathPen, 不做任何手工解析

用法:
  # 整字对比
  python glyphview.py --chars 延丝 --fonts a.otf:当前 b.otf:OPPO -o /tmp/out.png

  # 局部放大 (em 坐标, y 向上为正)
  python glyphview.py --chars 延 --fonts a.otf:当前 b.otf:OPPO \
      --win 0,430,-150,650 -o /tmp/out.png

  # 带网格
  python glyphview.py --chars 丝 --fonts a.otf:当前 --win 0,520,-120,720 --grid 50

字体 spec:  path.otf:标签[:wght]   第三段可选, 用于可变字体实例化
"""
import sys
import os
import argparse
import subprocess
import numpy as np

sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.varLib import instancer


def load_path(fp, ch, wght=None):
    """返回 (path_d, bounds)  -- bounds = (xMin,yMin,xMax,yMax)"""
    f = TTFont(fp)
    if wght is not None and 'fvar' in f:
        f = instancer.instantiateVariableFont(f, {'wght': wght})
    cm = f.getBestCmap()
    gs = f.getGlyphSet()
    gn = cm.get(ord(ch)) if cm else None
    if not gn:
        f.close()
        return None, None
    sp = SVGPathPen(gs)
    gs[gn].draw(sp)
    bp = BoundsPen(gs)
    gs[gn].draw(bp)
    f.close()
    return sp.getCommands(), bp.bounds


def parse_font_spec(s):
    parts = s.split(':')
    fp = parts[0]
    label = parts[1] if len(parts) > 1 else os.path.basename(fp)
    wght = float(parts[2]) if len(parts) > 2 else None
    return fp, label, wght


def build_svg(cells, win, grid, cell_w, out_path):
    """cells: [(label, d, bounds)]; win: (x0,x1,y0,y1) or None"""
    if win is None:
        allb = [c[2] for c in cells if c[2]]
        if not allb:
            raise ValueError('no bounds')
        x0 = min(b[0] for b in allb)
        y0 = min(b[1] for b in allb)
        x1 = max(b[2] for b in allb)
        y1 = max(b[3] for b in allb)
        pad = 40
        x0 -= pad; y0 -= pad; x1 += pad; y1 += pad
    else:
        x0, x1, y0, y1 = win

    n = len(cells)
    cell_h = int(cell_w * (y1 - y0) / (x1 - x0))
    W = cell_w * n
    H = cell_h

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H)]
    # 每格 clipPath: 字形超出单元格的部分被裁掉, 不侵入相邻格
    parts.append('<defs>')
    for i in range(len(cells)):
        parts.append('<clipPath id="cp%d"><rect x="%d" y="0" width="%d" height="%d"/></clipPath>' % (i, i * cell_w, cell_w, H))
    parts.append('</defs>')
    parts.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H))

    for i, (lbl, d, bb) in enumerate(cells):
        ox = i * cell_w
        # 每格白底 (避免相邻格字形视觉粘连)
        parts.append('<rect x="%d" y="0" width="%d" height="%d" fill="#ffffff"/>' % (ox, cell_w, H))
        if i > 0:
            parts.append('<line x1="%d" y1="0" x2="%d" y2="%d" stroke="#c00" stroke-width="2"/>' % (ox, ox, H))
        k = cell_w / (x1 - x0)
        parts.append('<g clip-path="url(#cp%d)">' % i)
        parts.append('<g transform="translate(%f,%f) scale(%f,%f) translate(%f,%f)">' % (
            ox, H, k, -k, -x0, -y0))
        if grid:
            parts.append('<g stroke="#d8d8d8" stroke-width="%.2f" fill="none">' % (0.7 * (x1 - x0) / cell_w))
            gx = int(np.floor(x0 / grid)) * grid
            while gx <= x1:
                parts.append('<line x1="%f" y1="%f" x2="%f" y2="%f"/>' % (gx, y0, gx, y1))
                gx += grid
            gy = int(np.floor(y0 / grid)) * grid
            while gy <= y1:
                parts.append('<line x1="%f" y1="%f" x2="%f" y2="%f"/>' % (x0, gy, x1, gy))
                gy += grid
            parts.append('</g>')
            # 坐标标注
            parts.append('<g fill="#888" font-size="%.1f" font-family="sans-serif">' % (16 * (x1 - x0) / cell_w))
            gx = int(np.floor(x0 / (grid * 2))) * grid * 2
            while gx <= x1:
                parts.append('<text x="%f" y="%f">%d</text>' % (gx + 3, y1 - 6, gx))
                gx += grid * 2
            gy = int(np.floor(y0 / (grid * 2))) * grid * 2
            while gy <= y1:
                parts.append('<text x="%f" y="%f">%d</text>' % (x0 + 3, gy - 3, gy))
                gy += grid * 2
            parts.append('</g>')
        if d:
            parts.append('<path d="%s" fill="#141414" fill-rule="nonzero"/>' % d)
        parts.append('</g>')
        parts.append('</g>')
        parts.append('<text x="%d" y="18" font-size="15" fill="#c00" font-family="sans-serif">%s</text>' % (ox + 6, lbl))

    parts.append('</svg>')
    sp = out_path.replace('.png', '.svg')
    with open(sp, 'w') as fh:
        fh.write('\n'.join(parts))
    subprocess.run(['rsvg-convert', '-w', str(W), '-h', str(H), '-o', out_path, sp], check=True)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chars', required=True, help='汉字串, 如 延丝')
    ap.add_argument('--fonts', required=True, nargs='+', help='path.otf:标签[:wght]')
    ap.add_argument('--win', default=None, help='x0,x1,y0,y1  em 坐标裁剪')
    ap.add_argument('--grid', type=int, default=0, help='网格间距(em单位), 0=关闭')
    ap.add_argument('--cell', type=int, default=440, help='单元格宽度 px')
    ap.add_argument('-o', '--out', required=True)
    a = ap.parse_args()

    fonts = [parse_font_spec(s) for s in a.fonts]
    win = None
    if a.win:
        v = [float(x) for x in a.win.split(',')]
        win = (v[0], v[1], v[2], v[3])

    for ch in a.chars:
        cells = []
        for fp, lbl, wght in fonts:
            d, bb = load_path(fp, ch, wght)
            if d is None:
                print('  %s 无 %s' % (lbl, ch))
                continue
            cells.append(('%s  %s' % (ch, lbl), d, bb))
        if not cells:
            continue
        out = a.out
        if len(a.chars) > 1:
            root, ext = os.path.splitext(a.out)
            out = '%s_%s%s' % (root, ch, ext)
        build_svg(cells, win, a.grid, a.cell, out)
        print('  -> %s' % out)


if __name__ == '__main__':
    main()
