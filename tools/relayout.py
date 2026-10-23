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
    """只动**外框**和**框内那块洞**的底边，内芯（如玉的横画、点）一概不碰。

    之前对每条轮廓按自己的最低点移动，导致 国 里的 玉 底横和点被一起下移 —— 错。
    """
    order = sorted(range(len(cs)), key=lambda i: -abs(signed_area(cs[i])))
    move = set(order[:2])          # 0 = 外框，1 = 框内的洞
    out = []
    for i, c in enumerate(cs):
        if i not in move:
            out.append(list(c))
            continue
        ymin = min(p[1] for p in c)
        nc = [(x, y - delta) if y <= ymin + tol else (x, y) for (x, y) in c]
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
    ap.add_argument("--target-pct", type=float, default=96.0,
                    help="目标高度占原高的百分比（默认 96）")
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

    # 守卫：这不是"底横托底"的包围结构（门、同 这类半包围），不许动
    shrink = (h0 - h1) / h0
    if shrink > 0.15:
        print(f"跳过 {a.glyph}: 去出脚后缩水 {shrink*100:.1f}% > 15%，"
              f"说明底部不是一条横画（半包围结构不适用）")
        render(cs, a.out, a.size)
        return

    if a.target_h:
        delta = max(0.0, a.target_h - h1)
    else:
        target = h0 * a.target_pct / 100.0
        delta = max(0.0, target - h1)
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
