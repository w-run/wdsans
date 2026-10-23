"""批量单字形预览：每个字体 × 每个字 → 一张独立的 1024px 图。

与 glyph_view.py 共用同一套 em 画框与网格编号，保证跨字体、跨字形的
格子编号指向同一块物理区域（这是逐像素对比的前提）。

用法：
    python3 glyph_suite.py --tag A \
        --fonts "shs=思源350=/tmp/p0/shs350.otf,v=variant=/tmp/p0/v_all.otf" \
        --glyphs 永国回 --outdir /var/minis/workspace/preview/A

产出：
    A/shx_永.png         整字 + 8×8 网格
    A/shx_永_index.txt   每个格子的墨水占比（定位细节用）
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glyph_view import (X0, X1, Y_TOP, Y_BOT, GRID, CELL,
                        glyph_svg_path, build_svg, region_from_crop, _label_cells)

from fontTools.ttLib import TTFont
from PIL import Image
import numpy as np


def render_one(font_path, char, out_png, crop=None, grid=True, size=1024):
    font = TTFont(font_path)
    cmap = font.getBestCmap()
    gname = cmap.get(ord(char))
    if not gname:
        return False, f"缺字 {char}"
    path_d = glyph_svg_path(font, gname)
    box = region_from_crop(crop) if crop else (X0, Y_TOP, X1, Y_BOT)
    svg = build_svg(path_d, box, draw_grid=grid)
    tmp = out_png + ".svg"
    with open(tmp, "w") as f:
        f.write(svg)
    x0, ytop, x1, ybot = box
    w = size
    h = max(1, int(round(size * (ytop - ybot) / (x1 - x0))))
    subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), "-o", out_png, tmp],
                   check=True)
    os.remove(tmp)
    if grid:
        _label_cells(out_png, box, w, h)
    return True, gname


def cell_index(png_path, box):
    """统计全图 8×8 各格的墨水占比，写成索引文本。"""
    x0, ytop, x1, ybot = box
    im = Image.open(png_path).convert("L")
    a = np.array(im) < 128
    H, W = a.shape
    rows = []
    ci0 = int(round((x0 - X0) / CELL))
    ri0 = int(round((Y_TOP - ytop) / CELL))
    ncol = int(round((x1 - x0) / CELL))
    nrow = int(round((ytop - ybot) / CELL))
    for ri in range(nrow):
        line = []
        for ci in range(ncol):
            r0 = int(ri * H / nrow); r1 = int((ri + 1) * H / nrow)
            c0 = int(ci * W / ncol); c1 = int((ci + 1) * W / ncol)
            frac = float(a[r0:r1, c0:c1].mean()) if r1 > r0 and c1 > c0 else 0.0
            col = ci0 + ci; row = ri0 + ri
            if 0 <= col < GRID and 0 <= row < GRID:
                line.append(f"{chr(ord('a') + col)}{row + 1}={frac:.2f}")
        rows.append("  ".join(line))
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="set")
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--glyphs", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--crop", default=None)
    ap.add_argument("--no-grid", action="store_true")
    a = ap.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    fonts = [tuple(x.split("=", 2)) for x in a.fonts.split(",")]
    box = region_from_crop(a.crop) if a.crop else (X0, Y_TOP, X1, Y_BOT)

    ok, fail = 0, []
    for key, label, path in fonts:
        for ch in a.glyphs:
            name = f"{key}_{ch}" + (f"_{a.crop}" if a.crop else "")
            out = os.path.join(a.outdir, f"{name}.png")
            good, info = render_one(path, ch, out, a.crop, not a.no_grid)
            if not good:
                fail.append((key, ch, info)); continue
            ok += 1
            with open(os.path.join(a.outdir, f"{name}_index.txt"), "w") as f:
                f.write(f"字体: {label}\n字形: {ch} ({info})\n区域: {box}\n\n")
                f.write(cell_index(out, box))
    print(f"完成 {ok} 张，失败 {len(fail)}")
    for f_ in fail:
        print("  失败:", f_)


if __name__ == "__main__":
    main()
