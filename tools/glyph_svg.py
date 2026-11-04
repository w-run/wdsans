#!/usr/bin/env python3
"""字形 SVG 锚点查看器。

用途：把字形导出成带锚点 + 标尺的 SVG，用眼睛看结构，用标尺量细节。

  on 点   实心圆
  off 点  空心方块
  锚点编号 可选

标尺：每 100 单位一条淡线，基线/字面框/重心线加重。
"""
from __future__ import annotations
import argparse
import os
import sys

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.recordingPen import RecordingPen

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wds.contours import read_points

UPM = 1000


def load(path, wght=None):
    f = TTFont(path)
    if wght is not None and "fvar" in f:
        f = instancer.instantiateVariableFont(
            f, {"wght": wght}, inplace=True, updateFontNames=False, optimize=False
        )
    return f


def glyph_svg(font, ch, show_index=True, ruler=True, color="#111"):
    cmap = font.getBestCmap()
    name = cmap.get(ord(ch))
    if not name:
        raise SystemExit(f"字体里没有 {ch} (U+{ord(ch):04X})")
    gs = font.getGlyphSet()

    # 外框路径
    pen = SVGPathPen(gs)
    gs[name].draw(pen)
    d = pen.getCommands()

    contours = read_points(gs, name)
    pts = [(x, y, c) for c in contours for (x, y, on) in [(p.x, p.y, p.on) for p in c]]

    # 画布（y 轴翻转：字体 y 向上，SVG y 向下）
    pad = 120
    xs = [p.x for p in [pp for c in contours for pp in c]]
    ys = [p.y for p in [pp for c in contours for pp in c]]
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad
    w, h = x1 - x0, y1 - y0
    # 保证至少覆盖一个字面
    if w < 700: 
        cx = (x0 + x1) / 2; x0, x1 = cx - 450, cx + 450; w = x1 - x0
    if h < 700:
        cy = (y0 + y1) / 2; y0, y1 = cy - 450, cy + 450; h = y1 - y0

    def X(x): return x - x0
    def Y(y): return y1 - y

    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
               f'viewBox="0 0 {w:.0f} {h:.0f}">')
    out.append(f'<rect width="{w:.0f}" height="{h:.0f}" fill="white"/>')

    if ruler:
        # 每 100 单位的网格
        gx = int(x0 // 100 * 100)
        while gx <= x1:
            out.append(f'<line x1="{X(gx):.1f}" y1="0" x2="{X(gx):.1f}" y2="{h:.0f}" '
                       f'stroke="#e8e8e8" stroke-width="1"/>')
            gx += 100
        gy = int(y0 // 100 * 100)
        while gy <= y1:
            out.append(f'<line x1="0" y1="{Y(gy):.1f}" x2="{w:.0f}" y2="{Y(gy):.1f}" '
                       f'stroke="#e8e8e8" stroke-width="1"/>')
            gy += 100
        # 基线 / cap / x-height / 字面框
        for yy, col, lab in [(0, "#e33", "baseline 0"),
                             (733, "#39f", "cap 733"),
                             (880, "#9c9", "typoAsc 880"),
                             (-120, "#9c9", "typoDesc -120")]:
            if y0 - 50 <= yy <= y1 + 50:
                out.append(f'<line x1="0" y1="{Y(yy):.1f}" x2="{w:.0f}" y2="{Y(yy):.1f}" '
                           f'stroke="{col}" stroke-width="1.5" stroke-dasharray="6,4" opacity="0.85"/>')
                out.append(f'<text x="4" y="{Y(yy)-4:.1f}" font-size="16" fill="{col}" '
                           f'font-family="monospace">{lab}</text>')

    # 字形轮廓
    out.append(f'<g transform="translate({-x0:.1f},{y1:.1f}) scale(1,-1)">')
    out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.5"/>')
    out.append('</g>')

    # 锚点
    for i, (x, y, on) in enumerate(pts):
        cx, cy = X(x), Y(y)
        if on:
            out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="#fff" stroke="#d00" stroke-width="2"/>')
        else:
            out.append(f'<rect x="{cx-4:.1f}" y="{cy-4:.1f}" width="8" height="8" fill="#fff" stroke="#06c" stroke-width="1.5"/>')
        if show_index:
            out.append(f'<text x="{cx+7:.1f}" y="{cy-6:.1f}" font-size="13" fill="#666" '
                       f'font-family="monospace">{i}</text>')

    out.append(f'<text x="6" y="20" font-size="18" fill="#000" font-family="monospace">'
               f'{ch} U+{ord(ch):04X} {name}  轮廓{len(contours)} 点数{len(pts)}</text>')
    out.append('</svg>')
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chars", help="字符")
    ap.add_argument("--font", default="/workspace/wdsans/ref/NotoSansCJKsc-VF.ttf")
    ap.add_argument("--wght", type=int, default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-index", action="store_true")
    args = ap.parse_args()

    f = load(args.font, args.wght)
    svgs = [glyph_svg(f, ch, show_index=not args.no_index) for ch in args.chars]
    if len(svgs) == 1:
        open(args.out, "w", encoding="utf-8").write(svgs[0])
    else:
        # 并排
        open(args.out, "w", encoding="utf-8").write(svgs[0])
        for i, s in enumerate(svgs[1:], 1):
            open(args.out.replace(".svg", f"-{i}.svg"), "w", encoding="utf-8").write(s)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
