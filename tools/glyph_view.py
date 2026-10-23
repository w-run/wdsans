"""单字形预览：字体轮廓 → SVG → PNG（rsvg-convert）。

为什么走 SVG：
- 不经过 @font-face，**不存在静默回退到系统字体**的问题
- 路径数据就是字形坐标，量化精确
- 同一份 SVG 既能预览，也能直接看坐标

固定画框（em 坐标，1000 upm）：
    x ∈ [-20, 1020]   y ∈ [900, -140]
    → 1040 × 1040 的正方形，基线 y=0 距顶部 900
    → 8×8 网格，每格 130 单位，列 a–h（左到右），行 1–8（上到下）

用法：
    # 整字 + 网格
    python3 glyph_view.py --font a.otf --glyph 永 --out yong.png --grid

    # 只取 d2 到 f3 这一块（含网格坐标的精确裁剪）
    python3 glyph_view.py --font a.otf --glyph 永 --out crop.png --crop d2-f3

    # 导出 SVG 自己看坐标
    python3 glyph_view.py --font a.otf --glyph 永 --out yong.svg --svg
"""
import argparse
import os
import subprocess
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

# ---- 固定画框 ----
X0, X1 = -20.0, 1020.0
Y_TOP, Y_BOT = 900.0, -140.0
GRID = 8
CELL = (X1 - X0) / GRID          # 130


def glyph_svg_path(font, glyph_name):
    gs = font.getGlyphSet()
    pen = SVGPathPen(gs)
    gs[glyph_name].draw(pen)
    return pen.getCommands()


def cell_box(name):
    """把 'd2' 转成 (x, y) 的 em 坐标矩形。"""
    col = name[0].lower()
    row = int(name[1:])
    ci = ord(col) - ord("a")
    ri = row - 1
    if not (0 <= ci < GRID and 0 <= ri < GRID):
        raise SystemExit(f"格子编号越界: {name}")
    x = X0 + ci * CELL
    y = Y_TOP - ri * CELL
    return x, y


def region_from_crop(spec):
    """'d2-f3' -> (x0, y0, x1, y1)"""
    if "-" in spec:
        a, b = spec.split("-")
    else:
        a = b = spec
    ax, ay = cell_box(a)
    bx, by = cell_box(b)
    x0, x1 = sorted((ax, bx + CELL))
    # y 轴向下：ay/by 是格子**顶边**，所以底边要再减一个 CELL
    ytop = max(ay, by)
    ybot = min(ay, by) - CELL
    return x0, ytop, x1, ybot


def build_svg(path_d, box, draw_grid, grid_labels=True, stroke=1.0):
    x0, ytop, x1, ybot = box
    w, h = x1 - x0, ytop - ybot
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{w:.2f}" height="{h:.2f}" '
        f'viewBox="{x0:.2f} {-ytop:.2f} {w:.2f} {h:.2f}">',
        f'<rect x="{x0}" y="{-ytop}" width="{w}" height="{h}" fill="white"/>',
        # 字形：SVG 的 y 轴向下，所以用 scale(1,-1) 翻转
        f'<g transform="translate(0,0) scale(1,-1)">',
        f'<path d="{path_d}" fill="black" fill-rule="nonzero"/>',
        f'</g>',
    ]
    if draw_grid:
        parts.append(f'<g stroke="#e6e6e6" stroke-width="{stroke}" fill="none">')
        for i in range(GRID + 1):
            gx = x0 + i * CELL
            parts.append(f'<line x1="{gx:.2f}" y1="{-ytop:.2f}" x2="{gx:.2f}" y2="{-ybot:.2f}"/>')
            gy = ytop - i * CELL
            parts.append(f'<line x1="{x0:.2f}" y1="{-gy:.2f}" x2="{x1:.2f}" y2="{-gy:.2f}"/>')
        parts.append("</g>")
        # 格号不在 SVG 里画（rsvg 没有字体会出豆腐块），改由 PIL 叠加
    parts.append("</svg>")
    return "\n".join(parts)


def _label_cells(png_path, box, w_px, h_px):
    """在 PNG 上叠格号（a1…h8），用 PIL 内置位图字体，无需 fontconfig。"""
    from PIL import Image, ImageDraw
    x0, ytop, x1, ybot = box
    im = Image.open(png_path).convert("L")
    d = ImageDraw.Draw(im)
    sx = w_px / (x1 - x0)
    sy = h_px / (ytop - ybot)
    ci0 = int(round((x0 - X0) / CELL))
    ri0 = int(round((Y_TOP - ytop) / CELL))
    ncol = int(round((x1 - x0) / CELL))
    nrow = int(round((ytop - ybot) / CELL))
    for ri in range(nrow):
        for ci in range(ncol):
            col = ci0 + ci
            row = ri0 + ri
            if not (0 <= col < GRID and 0 <= row < GRID):
                continue
            cx = x0 + ci * CELL
            cy = ytop - ri * CELL
            px = int((cx - x0) * sx) + 3
            py = int((ytop - cy) * sy) + 2
            if px > w_px - 18 or py > h_px - 10:
                continue
            d.text((px, py), f"{chr(ord('a') + col)}{row + 1}", fill=190)
    im.save(png_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--glyph", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--grid", action="store_true", help="叠加 8×8 网格与编号")
    ap.add_argument("--crop", default=None, help="如 d2-f3：只看这个矩形区域")
    ap.add_argument("--size", type=int, default=1024, help="PNG 边长（默认 1024）")
    ap.add_argument("--svg", action="store_true", help="输出 SVG 而不是 PNG")
    a = ap.parse_args()

    font = TTFont(a.font)
    cmap = font.getBestCmap()
    gname = cmap.get(ord(a.glyph))
    if not gname:
        raise SystemExit(f"字体里没有字符 {a.glyph!r}（U+{ord(a.glyph):04X}）")
    path_d = glyph_svg_path(font, gname)

    box = region_from_crop(a.crop) if a.crop else (X0, Y_TOP, X1, Y_BOT)
    svg = build_svg(path_d, box, draw_grid=a.grid)

    if a.svg:
        with open(a.out, "w") as f:
            f.write(svg)
        print("saved", a.out, f"(viewBox {box})")
        return

    tmp = a.out + ".svg"
    with open(tmp, "w") as f:
        f.write(svg)
    x0, ytop, x1, ybot = box
    w_px = a.size
    h_px = max(1, int(round(a.size * (ytop - ybot) / (x1 - x0))))
    subprocess.run(["rsvg-convert", "-w", str(w_px), "-h", str(h_px),
                    "-o", a.out, tmp], check=True)
    if a.grid:
        _label_cells(a.out, box, w_px, h_px)
    print("saved", a.out, f"{w_px}×{h_px} 区域={box}")


if __name__ == "__main__":
    main()
