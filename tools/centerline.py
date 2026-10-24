"""笔道中心线提取：从轮廓的内外边界配对求中线。

做法：
  1. 沿笔画走向做一维扫描（横画沿 x 扫，竖画沿 y 扫），得到墨段
  2. 相邻两个墨段（上/下 或 左/右）的边界视为同一条笔道的两条边
  3. 两条边成对取中点 → 中心线；两者的间距 → 笔宽

局限（重要）：弯钩处笔道转向，单一方向的扫描会失效。
所以本工具是"验证用"：先在**直笔**上验证中心线与笔宽是否可信，
确认精度后再谈弯钩重画。

用法：
    python3 centerline.py --font ref/shs/shs-400.otf --glyph 乙 \
        --axis y --out /tmp/center_乙.png
"""
import argparse
import subprocess
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen          # noqa: E402
from detail import scan_runs         # noqa: E402
from frame import X0, X1, Y_TOP, Y_BOT   # noqa: E402


def extract(cs, axis="y", step=4.0, tol=140.0):
    """axis='y'：逐 y 扫横向墨段，相邻两段配对（竖笔）。
       axis='x'：逐 x 扫纵向墨段，相邻两段配对（横笔）。
    返回 [(扫描坐标, 中点, 宽度)]。
    """
    pts = [q for c in cs for q in c]
    if axis == "y":
        lo, hi = min(q[1] for q in pts), max(q[1] for q in pts)
        scan, run = "h", "v"
    else:
        lo, hi = min(q[0] for q in pts), max(q[0] for q in pts)
        scan, run = "v", "h"

    out = []
    t = lo
    while t < hi:
        runs = scan_runs(cs, t, scan)
        runs = [(a, b) for a, b in runs if b - a > 8]
        # 相邻两段间距在 tol 内，视为同一条笔道的两边
        for i in range(len(runs) - 1):
            a0, b0 = runs[i]
            a1, b1 = runs[i + 1]
            gap = a1 - b0
            if 0 < gap <= tol:
                mid = (b0 + a1) / 2
                width = gap
                out.append((t, mid, width))
                break          # 每个扫描位只取第一对，避免串道
        t += step
    return out


def to_svg(cs, samples, axis, path, size=620):
    w, h = X1 - X0, Y_TOP - Y_BOT
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
         f'viewBox="{X0} {-Y_TOP} {w} {h}">',
         f'<rect x="{X0}" y="{-Y_TOP}" width="{w}" height="{h}" fill="white"/>',
         '<g transform="scale(1,-1)">']
    d = []
    for c in cs:
        d.append(f"M{c[0][0]:.1f} {c[0][1]:.1f}")
        for p in c[1:]:
            d.append(f"L{p[0]:.1f} {p[1]:.1f}")
        d.append("Z")
    o.append(f'<path d="{" ".join(d)}" fill="#dddddd" fill-rule="nonzero"/>')
    # 中心线
    line = []
    for (t, mid, wd) in samples:
        line.append((mid, t) if axis == "y" else (t, mid))
    if len(line) > 1:
        pd = [f"M{line[0][0]:.1f} {line[0][1]:.1f}"]
        for p in line[1:]:
            pd.append(f"L{p[0]:.1f} {p[1]:.1f}")
        o.append(f'<path d="{" ".join(pd)}" fill="none" stroke="#e03030" '
                 f'stroke-width="4"/>')
    for (t, mid, wd) in samples[::8]:
        x, y = (mid, t) if axis == "y" else (t, mid)
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#1f6fd0"/>')
    o.append("</g></svg>")
    with open(path + ".svg", "w") as f:
        f.write("\n".join(o))
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size),
                    "-o", path, path + ".svg"], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--glyph", required=True)
    ap.add_argument("--axis", default="y", choices=["x", "y"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=620)
    a = ap.parse_args()
    font = TTFont(a.font)
    gs = font.getGlyphSet()
    gn = font.getBestCmap().get(ord(a.glyph))
    if not gn:
        raise SystemExit(f"缺字 {a.glyph}")
    pen = FlatPen(gs)
    gs[gn].draw(pen)
    pen._end()
    cs = pen.contours
    font.close()
    s = extract(cs, a.axis)
    to_svg(cs, s, a.axis, a.out, a.size)
    if s:
        ws = [x[2] for x in s]
        print(f"saved {a.out}  采样 {len(s)} 点  笔宽 中位 {sorted(ws)[len(ws)//2]:.0f} "
              f"范围 {min(ws):.0f}..{max(ws):.0f}")
    else:
        print(f"saved {a.out}  未提取到中心线")


if __name__ == "__main__":
    main()
