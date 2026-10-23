"""单字 → 1024×1024 SVG（可量化测算用）。

设计目标：**打开就能量**。
- 画布 1024×1024，em 坐标与像素 1:1（1 设计单位 = 1 px）
- 可选叠加：16×16 网格、基线/字面参考线、轮廓节点与编号
- 同时可导出节点坐标文本，做纯数值测算

坐标映射（画布左上角为原点）：
    x_px = x_em + 12          （em x ∈ [-12, 1012]）
    y_px = 900 - y_em         （em y ∈ [-124, 900]，基线在 y_px=900）

用法：
    python3 glyph_svg.py --font ref/shs/shs-350.otf --glyph 永 --out 永.svg \
        --grid --refs --points

    # 只要坐标，不要图
    python3 glyph_svg.py --font ... --glyph 永 --out 永.txt --coords
"""
import argparse
import math
import os

from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

# ---- 固定画框：1 em 单位 = 1 px ----
SIZE = 1024
X_EM_MIN, X_EM_MAX = -12.0, 1012.0
Y_EM_MIN, Y_EM_MAX = -124.0, 900.0
GRID = 16
CELL = SIZE / GRID          # 64 px


def px(x, y):
    return x - X_EM_MIN, Y_EM_MAX - y


class NodePen(BasePen):
    """收集节点：每条轮廓的 on/off 点，按顺序编号。"""

    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.contours = []
        self.cur = []
        self.start_pt = None

    def _moveTo(self, pt):
        self._flush()
        self.cur = [(pt, True, "move")]
        self.start_pt = pt

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


def path_data(contours):
    """用节点列表重建 path（直线+三次曲线）。"""
    d = []
    for c in contours:
        # 起点：第一个 on 点
        start = None
        for pt, on, kind in c:
            if on:
                start = pt
                break
        if start is None:
            continue
        d.append(f"M{start[0]:.1f} {start[1]:.1f}")
        i = c.index(next(x for x in c if x[1]))
        n = len(c)
        cnt = 0
        while cnt < n:
            i = (i + 1) % n
            pt, on, kind = c[i]
            cnt += 1
            if on:
                d.append(f"L{pt[0]:.1f} {pt[1]:.1f}")
            else:
                c1 = pt
                c2 = c[(i + 1) % n][0]
                p3 = c[(i + 2) % n][0]
                d.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p3[0]:.1f} {p3[1]:.1f}")
                i = (i + 2) % n
                cnt += 2
        d.append("Z")
    return " ".join(d)


def build_svg(contours, path_d, grid=True, refs=True, points=False, title=""):
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
        f'viewBox="0 0 {SIZE} {SIZE}">',
        '<rect width="1024" height="1024" fill="#ffffff"/>',
    ]

    if grid:
        out.append('<g stroke="#e8e8e8" stroke-width="1">')
        for i in range(GRID + 1):
            v = i * CELL
            out.append(f'<line x1="{v:.1f}" y1="0" x2="{v:.1f}" y2="{SIZE}"/>')
            out.append(f'<line x1="0" y1="{v:.1f}" x2="{SIZE}" y2="{v:.1f}"/>')
        out.append("</g>")
        out.append('<g font-family="monospace" font-size="16" fill="#bbbbbb">')
        for ri in range(GRID):
            for ci in range(GRID):
                out.append(f'<text x="{ci*CELL+3:.0f}" y="{ri*CELL+14:.0f}" '
                           f'font-size="12">{chr(ord("a")+ci)}{ri+1}</text>')
        out.append("</g>")

    if refs:
        out.append('<g stroke-width="1">')
        for yy, lab, col, dash in ((880, "asc 880", "#88aaff", ' stroke-dasharray="6 4"'),
                                   (800, "800", "#dddddd", ' stroke-dasharray="3 5"'),
                                   (0, "baseline 0", "#ff8888", ""),
                                   (-120, "desc -120", "#88aaff", ' stroke-dasharray="6 4"')):
            py = Y_EM_MAX - yy
            out.append(f'<line x1="0" y1="{py:.1f}" x2="1024" y2="{py:.1f}" '
                       f'stroke="{col}"{dash}/>')
        # 标签统一靠右、带白描边，避免压住字形
        out.append('<g font-family="monospace" font-size="15" text-anchor="end" '
                   'stroke="#ffffff" stroke-width="4" paint-order="stroke">')
        for yy, lab, col in ((880, "asc 880", "#88aaff"),
                             (800, "800", "#cccccc"),
                             (0, "baseline 0", "#ff8888"),
                             (-120, "desc -120", "#88aaff")):
            py = Y_EM_MAX - yy
            out.append(f'<text x="1018" y="{py-6:.1f}" fill="{col}" '
                       f'stroke="#ffffff">{lab}</text>')
        out.append("</g>")
        out.append("</g>")

    # 字形（SVG 的 y 轴向下，这里直接用已转换的坐标重建，避免二次翻转错误）
    out.append(f'<path d="{_to_px_path(contours)}" fill="#111" fill-rule="nonzero"/>')

    if points:
        out.append('<g fill="none" stroke="#ff4444" stroke-width="1">')
        for ci, c in enumerate(contours):
            for ni, (pt, on, kind) in enumerate(c):
                x, y = px(pt[0], pt[1])
                if on:
                    out.append(f'<rect x="{x-3:.1f}" y="{y-3:.1f}" width="6" height="6" '
                               f'fill="#ff4444" stroke="none"/>')
                else:
                    out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="#ffffff"/>')
        out.append("</g>")
        out.append('<g font-family="monospace" font-size="11" fill="#666666">')
        for ci, c in enumerate(contours):
            for ni, (pt, on, kind) in enumerate(c):
                if not on:
                    continue
                x, y = px(pt[0], pt[1])
                out.append(f'<text x="{x+4:.1f}" y="{y-4:.1f}">{ci}.{ni}</text>')
        out.append("</g>")

    out.append(f'<text x="8" y="1016" font-family="monospace" font-size="14" '
               f'fill="#999999">{title}</text>')
    out.append("</svg>")
    return "\n".join(out)


def _to_px_path(contours):
    d = []
    for c in contours:
        n = len(c)
        on_idx = [i for i, (_, on, _) in enumerate(c) if on]
        if not on_idx:
            continue
        start = on_idx[0]
        x, y = px(*c[start][0])
        d.append(f"M{x:.1f} {y:.1f}")
        i = start
        cnt = 1
        while cnt < n:
            i = (i + 1) % n
            pt, on, kind = c[i]
            cnt += 1
            if on:
                x, y = px(*pt)
                d.append(f"L{x:.1f} {y:.1f}")
            else:
                c1 = pt
                i2 = (i + 1) % n
                c2 = c[i2][0]
                i3 = (i2 + 1) % n
                p3 = c[i3][0]
                x1, y1 = px(*c1); x2, y2 = px(*c2); x3, y3 = px(*p3)
                d.append(f"C{x1:.1f} {y1:.1f} {x2:.1f} {y2:.1f} {x3:.1f} {y3:.1f}")
                i = i3
                cnt += 2
        d.append("Z")
    return " ".join(d)


def coords_text(contours, gname, char):
    lines = [f"{char} ({gname})  画布 1024×1024，1 em 单位 = 1 px",
             f"映射: x_px = x_em + {abs(X_EM_MIN):.0f}   y_px = {Y_EM_MAX:.0f} - y_em", ""]
    for ci, c in enumerate(contours):
        lines.append(f"轮廓 {ci}: {len(c)} 个节点")
        for ni, (pt, on, kind) in enumerate(c):
            x, y = px(pt[0], pt[1])
            lines.append(f"  {ci}.{ni:<3} ({pt[0]:7.1f},{pt[1]:7.1f})  "
                         f"px=({x:6.1f},{y:6.1f})  {'on ' if on else 'off'} {kind}")
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
    a = ap.parse_args()

    font = TTFont(a.font)
    gname, contours = glyph_contours(font, a.glyph)
    title = f"{os.path.basename(a.font)}  {a.glyph}  {gname}"

    if a.coords:
        with open(a.out, "w") as f:
            f.write(coords_text(contours, gname, a.glyph))
        print("saved", a.out, f"{sum(len(c) for c in contours)} 节点")
        return

    svg = build_svg(contours, "", a.grid, a.refs, a.points, title)
    with open(a.out, "w") as f:
        f.write(svg)
    print("saved", a.out, f"{SIZE}×{SIZE} 轮廓{len(contours)} 节点{sum(len(c) for c in contours)}")


if __name__ == "__main__":
    main()
