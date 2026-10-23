"""包围结构重排：去出脚 + 底横下移回填。

为什么需要两步：直接把出脚钳掉，字会矮 6–12%（口 790 → 705）。
OPPO 的做法不是"砍掉出脚"，而是**把底横整体下移，让它自己成为最低点**。

做法（顺序不能反）：
    1. 钳制出脚：轮廓上低于底横下缘的点，抬到该线
    2. 底横下移：外轮廓的底边、以及洞的底边，**同时**下移 delta
       （只移外轮廓会把底横拉厚；两边一起移，厚度不变、洞变高）

用法：
    python3 relayout.py --font ref/shs/shs-400.otf --glyph 口 \
        --drop 55 --out /tmp/kou.png
"""
import argparse
import subprocess
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen, signed_area   # noqa: E402
from detail import scan_runs               # noqa: E402
from frame import X0, X1, Y_TOP, Y_BOT     # noqa: E402


def bar_bottom(cs):
    pts = [q for c in cs for q in c]
    xc = (min(q[0] for q in pts) + max(q[0] for q in pts)) / 2
    runs = scan_runs(cs, xc, "v")
    return min(runs, key=lambda r: r[0])[0] if runs else None


def strip_feet(cs, ybar):
    out = []
    for c in cs:
        nc = [(x, ybar if y < ybar else y) for (x, y) in c]
        out.append(dedup(nc))
    return out


def dedup(pts):
    clean = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - clean[-1][0]) > 0.5 or abs(p[1] - clean[-1][1]) > 0.5:
            clean.append(p)
    if clean[0] != clean[-1]:
        clean.append(clean[0])
    return clean


def drop_bar(cs, delta, tol=2.0):
    """外轮廓底边 + 每个洞的底边，同时下移 delta。"""
    out = []
    for c in cs:
        ys = [p[1] for p in c]
        ymin = min(ys)
        nc = []
        for (x, y) in c:
            # 只动各轮廓自己的"底边"：距该轮廓最低点 tol 以内
            nc.append((x, y - delta) if y <= ymin + tol else (x, y))
        out.append(dedup(nc))
    return out


def bbox(cs):
    pts = [q for c in cs for q in c]
    return (min(q[0] for q in pts), min(q[1] for q in pts),
            max(q[0] for q in pts), max(q[1] for q in pts))


def to_svg_path(cs):
    d = []
    for pts in cs:
        if len(pts) < 3:
            continue
        d.append(f"M{pts[0][0]:.1f} {pts[0][1]:.1f}")
        for p in pts[1:]:
            d.append(f"L{p[0]:.1f} {p[1]:.1f}")
        d.append("Z")
    return " ".join(d)


def render(cs, path, size=520):
    w, h = X1 - X0, Y_TOP - Y_BOT
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="{X0} {-Y_TOP} {w} {h}">',
        f'<rect x="{X0}" y="{-Y_TOP}" width="{w}" height="{h}" fill="white"/>',
        '<g transform="scale(1,-1)">',
        f'<path d="{to_svg_path(cs)}" fill="black" fill-rule="nonzero"/>',
        '</g></svg>',
    ]
    tmp = path + ".svg"
    with open(tmp, "w") as f:
        f.write("\n".join(svg))
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size),
                    "-o", path, tmp], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--glyph", required=True)
    ap.add_argument("--drop", type=float, default=55.0, help="底横下移量")
    ap.add_argument("--target-h", type=float, default=None,
                    help="目标总高；给了就按它反推下移量，忽略 --drop")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=520)
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

    x0, y0, x1, y1 = bbox(cs)
    h0 = y1 - y0
    ybar = bar_bottom(cs)
    cs1 = strip_feet(cs, ybar)
    _, y0b, _, y1b = bbox(cs1)
    h1 = y1b - y0b

    if a.target_h:
        delta = max(0.0, a.target_h - h1)
    else:
        delta = a.drop
    cs2 = drop_bar(cs1, delta)
    _, y0c, _, y1c = bbox(cs2)
    h2 = y1c - y0c

    render(cs2, a.out, a.size)
    print(f"saved {a.out}")
    print(f"  原高 {h0:.0f}  去出脚 {h1:.0f} (−{100*(h0-h1)/h0:.1f}%)  "
          f"底横下移 {delta:.0f} → {h2:.0f}  ({100*h2/h0:.0f}% of 原高)")
    print(f"  底横下缘 {ybar:.0f} → {ybar - delta:.0f}")


if __name__ == "__main__":
    main()
