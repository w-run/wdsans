"""去出脚试验：把包围结构里竖笔探出底横的部分切掉。

做法：找到底横的下缘（字形中部纵向扫描的最低横带下沿），
把轮廓上低于该线的点全部抬到该线。包围结构底横以下只有出脚，直接钳制 y 即可。

用法：
    python3 strip_feet.py --font ref/shs/shs-400.otf --glyph 口 --out /tmp/after.png
"""
import argparse
import subprocess
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen        # noqa: E402
from detail import scan_runs       # noqa: E402
from frame import X0, X1, Y_TOP, Y_BOT   # noqa: E402


def bar_bottom(cs):
    """底横下缘：字形中部纵向扫描，最低那条横带的下端。"""
    pts = [q for c in cs for q in c]
    x0 = min(q[0] for q in pts)
    x1 = max(q[0] for q in pts)
    xc = (x0 + x1) / 2
    runs = scan_runs(cs, xc, "v")
    if not runs:
        return None
    return min(runs, key=lambda r: r[0])[0]


def strip(cs, ybar):
    out = []
    moved = 0
    for c in cs:
        nc = []
        for (x, y) in c:
            if y < ybar:
                nc.append((x, ybar))
                moved += 1
            else:
                nc.append((x, y))
        clean = [nc[0]]
        for p in nc[1:]:
            if abs(p[0] - clean[-1][0]) > 0.5 or abs(p[1] - clean[-1][1]) > 0.5:
                clean.append(p)
        if clean[0] != clean[-1]:
            clean.append(clean[0])
        out.append(clean)
    return out, moved


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
    ybar = bar_bottom(cs)
    new, moved = strip(cs, ybar)
    render(new, a.out, a.size)
    print(f"saved {a.out}  底横下缘 y={ybar:.0f}  抬起 {moved} 个点")


if __name__ == "__main__":
    main()
