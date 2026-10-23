"""多字体对照图：一张 SVG 里排多格，共用**一套连续网格**。

为什么不拼 PNG：拼接后每格各有一套网格，格线对不齐，
"这两个字是不是一样宽"这种问题就看不出来了。这里所有格在同一坐标系里，
格线横穿整张图，列与列直接可比。

两种模式：
  grid     行=字形，列=字体（默认）
  overlay  所有字体叠在同一格，按色区分 —— 看细节差异最直接

用法：
    # 四家 × 四字对照表
    python3 sheet.py --glyphs 口永国大 \
      --fonts "SHS400=ref/shs/shs-400.otf,HOS400=ref/hos/hos-400.ttf" \
      --out /tmp/sheet.svg --png

    # 叠图：只看 口 的差异在哪
    python3 sheet.py --glyphs 口 --overlay \
      --fonts "SHS400=ref/shs/shs-400.otf,OPPO400=ref/ops/ops-400.ttf" \
      --out /tmp/ov.svg --png

    # 放大到 d2-f3 这一块再看
    python3 sheet.py --glyphs 口 --crop d2-f3 --out /tmp/z.svg --png
"""
import argparse
import math
import os
import subprocess
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glyph_view import (X0, X1, Y_TOP, Y_BOT, GRID, CELL,   # noqa: E402
                        region_from_crop)

CELL_W = X1 - X0          # 1040
CELL_H = Y_TOP - Y_BOT    # 1040
COLORS = ["#111111", "#d13b3b", "#1f6fd0", "#0f9d58", "#a142f4", "#e08a00"]
MONO = "DejaVu Sans Mono, monospace"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def grid_lines(parts, ncols, nrows, rw, rh, rx0, rytop, sw=2.2):
    """网格按 em 绝对坐标画，每格平移过去 —— 所以整张图能对齐。"""
    parts.append(f'<g stroke="#e0e0e0" stroke-width="{sw}" fill="none">')
    ci0 = math.ceil((rx0 - X0) / CELL - 1e-6)
    ci1 = math.floor((rx0 + rw - X0) / CELL + 1e-6)
    ri0 = math.ceil((Y_TOP - rytop) / CELL - 1e-6)
    ri1 = math.floor((Y_TOP - (rytop - rh)) / CELL + 1e-6)
    for c in range(ncols):
        for ci in range(int(ci0), int(ci1) + 1):
            gx = X0 + c * rw + (X0 + ci * CELL - rx0)
            parts.append(f'<line x1="{gx:.2f}" y1="{-Y_TOP:.2f}" '
                         f'x2="{gx:.2f}" y2="{-Y_TOP + nrows * rh:.2f}"/>')
    for r in range(nrows):
        for ri in range(int(ri0), int(ri1) + 1):
            gy = -Y_TOP + r * rh + (rytop - (Y_TOP - ri * CELL))
            parts.append(f'<line x1="{X0:.2f}" y1="{gy:.2f}" '
                         f'x2="{X0 + ncols * rw:.2f}" y2="{gy:.2f}"/>')
    parts.append("</g>")


def cell_numbers(parts, ncols, nrows, rw, rh, rx0, rytop, fs=15):
    """每格内的 a1…h8，按 em 格位算。"""
    parts.append(f'<g font-family="{MONO}" font-size="{fs}" fill="#cccccc">')
    ci0 = int(math.ceil((rx0 - X0) / CELL - 1e-6))
    ri0 = int(math.ceil((Y_TOP - rytop) / CELL - 1e-6))
    for r in range(nrows):
        for c in range(ncols):
            for ri in range(ri0, ri0 + int(round(rh / CELL))):
                if ri >= GRID:
                    break
                for ci in range(ci0, ci0 + int(round(rw / CELL))):
                    if ci >= GRID:
                        break
                    gx = X0 + c * rw + (X0 + ci * CELL - rx0)
                    gy = -Y_TOP + r * rh + (rytop - (Y_TOP - ri * CELL))
                    parts.append(f'<text x="{gx + 5:.1f}" y="{gy + 19:.1f}">'
                                 f'{chr(ord("a") + ci)}{ri + 1}</text>')
    parts.append("</g>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True, help="标签=路径,标签=路径")
    ap.add_argument("--glyphs", required=True, help="字符，可多个")
    ap.add_argument("--out", required=True, help="输出 .svg；加 --png 另出 .png")
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--scale", type=float, default=1.0, help="PNG 每 em 单位的像素数")
    ap.add_argument("--no-grid", dest="grid", action="store_false", default=True)
    ap.add_argument("--numbers", action="store_true", help="叠格号 a1…h8")
    ap.add_argument("--overlay", action="store_true", help="所有字体叠在同一格")
    ap.add_argument("--crop", default=None, help="如 d2-f3，统一裁剪")
    ap.add_argument("--solid", action="store_true",
                    help="叠图模式默认画轮廓线；加此参数改为半透明实心")
    ap.add_argument("--stroke", type=float, default=6.0,
                    help="叠图轮廓线宽（em 单位，默认 6）")
    a = ap.parse_args()
    if a.overlay and a.solid:
        a.stroke = 0.0

    fonts = []
    for seg in a.fonts.split(","):
        lab, p = seg.split("=", 1)
        lab = lab.strip()
        if any(ord(ch) > 126 for ch in lab):
            print(f"警告：标签 {lab!r} 含非 ASCII，DejaVu 无中文字形会显示成空框；"
                  f"建议用 SHS/HOS/OPPO/WDO 这类拉丁标签", file=sys.stderr)
        fonts.append((lab, p.strip()))
    glyphs = []
    for c in a.glyphs:
        if c not in glyphs:
            glyphs.append(c)
    if a.overlay:
        glyphs = glyphs[:1]

    if a.crop:
        rx0, rytop, rx1, rybot = region_from_crop(a.crop)
    else:
        rx0, rytop, rx1, rybot = X0, Y_TOP, X1, Y_BOT
    rw, rh = rx1 - rx0, rytop - rybot

    data = {}
    for lab, p in fonts:
        font = TTFont(p)
        gs = font.getGlyphSet()
        cmap = font.getBestCmap()
        d = {}
        for ch in glyphs:
            gn = cmap.get(ord(ch))
            if gn:
                pen = SVGPathPen(gs)
                gs[gn].draw(pen)
                d[ch] = pen.getCommands()
            else:
                d[ch] = None
        data[lab] = d
        font.close()

    ncol = 1 if a.overlay else len(fonts)
    nrow = 1 if a.overlay else len(glyphs)
    sw, sh = ncol * rw, nrow * rh

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'width="{sw * a.scale:.0f}" height="{sh * a.scale:.0f}" '
             f'viewBox="{X0:.2f} {-Y_TOP:.2f} {sw:.2f} {sh:.2f}">',
             f'<rect x="{X0:.2f}" y="{-Y_TOP:.2f}" '
             f'width="{sw:.2f}" height="{sh:.2f}" fill="white"/>']

    if a.grid:
        grid_lines(parts, ncol, nrow, rw, rh, rx0, rytop)
        if a.numbers:
            cell_numbers(parts, ncol, nrow, rw, rh, rx0, rytop)

    if a.overlay:
        for i, (lab, _) in enumerate(fonts):
            d = data[lab][glyphs[0]]
            if not d:
                continue
            col = COLORS[i % len(COLORS)]
            if a.stroke > 0:
                parts.append(f'<g transform="translate({X0 - rx0:.2f},{rytop - Y_TOP:.2f}) scale(1,-1)">'
                             f'<path d="{d}" fill="none" '
                             f'stroke="{col}" stroke-width="{a.stroke}"/></g>')
            else:
                parts.append(f'<g transform="translate({X0 - rx0:.2f},{rytop - Y_TOP:.2f}) scale(1,-1)" '
                             f'opacity="0.5">'
                             f'<path d="{d}" fill="{col}" fill-rule="nonzero"/></g>')
        parts.append(f'<g font-family="{MONO}" font-size="26">')
        for i, (lab, _) in enumerate(fonts):
            ly = -rytop + 40 + i * 36
            col = COLORS[i % len(COLORS)]
            parts.append(f'<rect x="{rx0 + 14:.1f}" y="{ly - 19:.1f}" width="22" '
                         f'height="22" fill="{col}" opacity="0.75"/>')
            parts.append(f'<text x="{rx0 + 46:.1f}" y="{ly:.1f}" fill="#444444" '
                         f'stroke="white" stroke-width="4" paint-order="stroke">'
                         f'{esc(lab)}</text>')
        parts.append("</g>")
    else:
        for r, ch in enumerate(glyphs):
            for c, (lab, _) in enumerate(fonts):
                d = data[lab][ch]
                tx = X0 + c * rw - rx0
                ty = r * rh + (rytop - Y_TOP)
                if d:
                    parts.append(f'<g transform="translate({tx:.2f},{ty:.2f}) scale(1,-1)">'
                                 f'<path d="{d}" fill="black" fill-rule="nonzero"/></g>')
                else:
                    parts.append(f'<g font-family="{MONO}" font-size="44" fill="#dd0000">'
                                 f'<text x="{tx + 40:.1f}" y="{ty + 70:.1f}">'
                                 f'missing {esc(ch)}</text></g>')
        # 列标签（字体）+ 行标签（字）
        parts.append(f'<g font-family="{MONO}" font-size="24" fill="#555555" '
                     f'stroke="white" stroke-width="4" paint-order="stroke">')
        for c, (lab, _) in enumerate(fonts):
            for r in range(nrow):
                ty = -Y_TOP + r * rh
                parts.append(f'<text x="{X0 + c * rw + 10:.1f}" y="{ty + 30:.1f}">'
                             f'{esc(lab)}</text>')
        parts.append("</g>")
        parts.append(f'<g font-family="{MONO}" font-size="46" fill="#bbbbbb">')
        for r, ch in enumerate(glyphs):
            ty = -rytop + r * rh
            parts.append(f'<text x="{X0 + rw - 60:.1f}" y="{ty + sh / nrow - 16:.1f}">'
                         f'{esc(ch)}</text>')
        parts.append("</g>")

    parts.append("</svg>")
    with open(a.out, "w") as f:
        f.write("\n".join(parts))
    print("saved", a.out, f"{nrow}行×{ncol}列")

    if a.png:
        png = os.path.splitext(a.out)[0] + ".png"
        w, h = int(sw * a.scale), int(sh * a.scale)
        subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h),
                        "-o", png, a.out], check=True)
        print("saved", png, f"{w}×{h}")


if __name__ == "__main__":
    main()
