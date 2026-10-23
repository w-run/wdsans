"""单字 → SVG（量化测算用）。

画框与格位**全部来自 frame.py**，与 glyph_view / montage 完全同一套：
    x ∈ [-20, 1020]，y ∈ [900, -140]
    x_px = x_em + 20
    y_px = 900 - y_em

画布默认 1040×1040，所以 **1 设计单位 = 1 像素**，量出来的像素值可直接当 em 单位用。
（以前这套工具自己用 1024，比预览少 8 单位边距，同一个字裁切范围都不一样，已废弃。）

可叠加：16×16 网格与十六进制格号、基线/字面参考线、轮廓节点与编号。

用法：
    python3 glyph_svg.py --font ref/shs/shs-400.otf --glyph 永 \
        --out 永.svg --grid --refs --points

    # 只要坐标文本，不依赖渲染环境
    python3 glyph_svg.py --font ref/shs/shs-400.otf --glyph 永 \
        --out 永.txt --coords
"""
import argparse
import os

from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

from frame import (X0, X1, Y_TOP, Y_BOT, GRID, CELL, WIDTH,      # noqa: F401
                   cell_name)

SIZE = int(WIDTH)          # 1040：1 em 单位 = 1 px


def px(x, y):
    """em 坐标 → 像素坐标（画布左上角为原点）。"""
    return x - X0, Y_TOP - y


class NodePen(BasePen):
    """收集节点：每条轮廓的 on/off 点，按顺序编号。"""

    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.contours = []
        self.cur = []

    def _moveTo(self, pt):
        self._flush()
        self.cur = [(pt, True, "move")]

    def _lineTo(self, pt):
        self.cur.append((pt, True, "line"))

    def _curveToOne(self, p1, p2, p3):
        self.cur.append((p1, False, "ctrl"))
        self.cur.append((p2, False, "ctrl"))
        self.cur.append((p3, True, "curve"))

    def _closePath(self):
        self._flush()

    def _endPath(self):
        self._flush()

    def _flush(self):
        if len(self.cur) > 1:
            self.contours.append(self.cur)
        self.cur = []

    def finish(self):
        self._flush()
        self.contours = [c for c in self.contours if len(c) > 1]
        return self.contours


def glyph_contours(font, char):
    cmap = font.getBestCmap()
    gname = cmap.get(ord(char))
    if not gname:
        raise SystemExit(f"字体里没有 {char!r}（U+{ord(char):04X}）")
    gs = font.getGlyphSet()
    pen = NodePen(gs)
    gs[gname].draw(pen)
    return gname, pen.finish()


def _path(contours):
    """按节点列表重建 path（y 已翻转到画布坐标）。"""
    d = []
    for c in contours:
        n = len(c)
        start = next((i for i, (_, on, _) in enumerate(c) if on), None)
        if start is None:
            continue
        x, y = px(*c[start][0])
        d.append(f"M{x:.1f} {y:.1f}")
        i = start
        cnt = 1
        while cnt < n:
            i = (i + 1) % n
            pt, on, _ = c[i]
            cnt += 1
            if on:
                x, y = px(*pt)
                d.append(f"L{x:.1f} {y:.1f}")
            else:
                i2 = (i + 1) % n
                i3 = (i2 + 1) % n
                x1, y1 = px(*pt)
                x2, y2 = px(*c[i2][0])
                x3, y3 = px(*c[i3][0])
                d.append(f"C{x1:.1f} {y1:.1f} {x2:.1f} {y2:.1f} {x3:.1f} {y3:.1f}")
                i = i3
                cnt += 2
        d.append("Z")
    return " ".join(d)


def build_svg(contours, grid=True, refs=True, points=False, title="", size=SIZE):
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {SIZE} {SIZE}">',
        f'<rect width="{SIZE}" height="{SIZE}" fill="#ffffff"/>',
    ]

    if grid:
        o.append('<g stroke="#e8e8e8" stroke-width="1">')
        for i in range(GRID + 1):
            v = i * CELL
            o.append(f'<line x1="{v:.1f}" y1="0" x2="{v:.1f}" y2="{SIZE}"/>')
            o.append(f'<line x1="0" y1="{v:.1f}" x2="{SIZE}" y2="{v:.1f}"/>')
        o.append("</g>")
        # 格位 = 两位十六进制（列在前、行在后），与 frame.cell_name 一致
        o.append('<g font-family="monospace" font-size="11" fill="#c8c8c8">')
        for ri in range(GRID):
            for ci in range(GRID):
                o.append(f'<text x="{ci*CELL+3:.0f}" y="{ri*CELL+13:.0f}">'
                         f'{cell_name(ci, ri)}</text>')
        o.append("</g>")

    if refs:
        o.append('<g stroke-width="1">')
        for yy, col, dash in ((880, "#88aaff", ' stroke-dasharray="6 4"'),
                              (800, "#dddddd", ' stroke-dasharray="3 5"'),
                              (0, "#ff8888", ""),
                              (-120, "#88aaff", ' stroke-dasharray="6 4"')):
            py = Y_TOP - yy
            o.append(f'<line x1="0" y1="{py:.1f}" x2="{SIZE}" y2="{py:.1f}" '
                     f'stroke="{col}"{dash}/>')
        o.append('<g font-family="monospace" font-size="15" text-anchor="end" '
                 'stroke="#ffffff" stroke-width="4" paint-order="stroke">')
        for yy, lab, col in ((880, "asc 880", "#88aaff"),
                             (800, "800", "#cccccc"),
                             (0, "baseline 0", "#ff8888"),
                             (-120, "desc -120", "#88aaff")):
            py = Y_TOP - yy
            o.append(f'<text x="{SIZE-6}" y="{py-6:.1f}" fill="{col}" '
                     f'stroke="#ffffff">{lab}</text>')
        o.append("</g></g>")

    o.append(f'<path d="{_path(contours)}" fill="#111" fill-rule="nonzero"/>')

    if points:
        o.append('<g stroke="none">')
        for ci, c in enumerate(contours):
            for ni, (pt, on, _) in enumerate(c):
                x, y = px(*pt)
                if on:
                    o.append(f'<rect x="{x-3:.1f}" y="{y-3:.1f}" width="6" height="6" '
                             f'fill="#ff4444"/>')
                else:
                    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" '
                             f'fill="#ffffff" stroke="#ff4444" stroke-width="1"/>')
        o.append("</g>")
        o.append('<g font-family="monospace" font-size="11" fill="#666666">')
        for ci, c in enumerate(contours):
            for ni, (pt, on, _) in enumerate(c):
                if not on:
                    continue
                x, y = px(*pt)
                o.append(f'<text x="{x+4:.1f}" y="{y-4:.1f}">{ci}.{ni}</text>')
        o.append("</g>")

    if title:
        o.append(f'<text x="8" y="{SIZE-6}" font-family="monospace" '
                 f'font-size="14" fill="#999999">{title}</text>')
    o.append("</svg>")
    return "\n".join(o)


def coords_text(contours, gname, char):
    lines = [f"{char} ({gname})  画布 {SIZE}×{SIZE}，1 em 单位 = 1 px",
             f"映射: x_px = x_em + {abs(X0):.0f}   y_px = {Y_TOP:.0f} - y_em",
             f"格位: 16×16，每格 {CELL:.0f}，列 0-f 行 0-f", ""]
    for ci, c in enumerate(contours):
        lines.append(f"轮廓 {ci}: {len(c)} 个节点")
        for ni, (pt, on, kind) in enumerate(c):
            x, y = px(pt[0], pt[1])
            col = min(GRID - 1, max(0, int((pt[0] - X0) / CELL)))
            row = min(GRID - 1, max(0, int((Y_TOP - pt[1]) / CELL)))
            lines.append(f"  {ci}.{ni:<3} ({pt[0]:7.1f},{pt[1]:7.1f})  "
                         f"px=({x:6.1f},{y:6.1f})  格 {cell_name(col, row)}  "
                         f"{'on ' if on else 'off'} {kind}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--glyph", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--grid", action="store_true", default=True)
    ap.add_argument("--no-grid", dest="grid", action="store_false")
    ap.add_argument("--refs", action="store_true", default=True)
    ap.add_argument("--no-refs", dest="refs", action="store_false")
    ap.add_argument("--points", action="store_true", help="标出节点与编号")
    ap.add_argument("--coords", action="store_true", help="输出坐标文本而不是 SVG")
    ap.add_argument("--size", type=int, default=SIZE, help=f"SVG 边长（默认 {SIZE}）")
    a = ap.parse_args()

    font = TTFont(a.font)
    gname, contours = glyph_contours(font, a.glyph)
    title = f"{os.path.basename(a.font)}  {a.glyph}  {gname}"

    if a.coords:
        with open(a.out, "w") as f:
            f.write(coords_text(contours, gname, a.glyph))
        print("saved", a.out, f"{sum(len(c) for c in contours)} 节点")
        return

    svg = build_svg(contours, a.grid, a.refs, a.points, title, a.size)
    with open(a.out, "w") as f:
        f.write(svg)
    print("saved", a.out, f"{a.size}×{a.size} 轮廓{len(contours)} "
                         f"节点{sum(len(c) for c in contours)}")
    font.close()


if __name__ == "__main__":
    main()
