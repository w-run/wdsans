"""斜笔末端收方：把冲出去的尖喙压成竖直端面。

思源的 `乙/飞/乃` 在斜笔接入横画处不留端面，顶边直接折进斜笔，
形成一个尖点加一个台阶。HOS / OPPO 把横画收在竖直端面上。

做法（局部钳制，不动别处）：
    1. 取顶边（y 接近字顶的那批点）的最右 x  → xcut
    2. 在该横画的 y 带内，把 x > xcut 的点全部投影到 x = xcut
    3. 结果是一条竖直端面，长度自然等于该处的墨厚（约一个笔宽）

用法：
    python3 square_ends.py --font ref/shs/shs-400.otf --glyph 乙 --out /tmp/yi.png
"""
import argparse
import subprocess
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen          # noqa: E402
from detail import scan_runs         # noqa: E402
from frame import X0, X1, Y_TOP, Y_BOT   # noqa: E402


def bbox(cs):
    pts = [q for c in cs for q in c]
    return (min(q[0] for q in pts), min(q[1] for q in pts),
            max(q[0] for q in pts), max(q[1] for q in pts))


def square_end(cs, top_tol=6.0):
    """返回 (新轮廓, xcut, y带)。"""
    x0, y0, x1, y1 = bbox(cs)
    pts = [q for c in cs for q in c]
    top = [p for p in pts if p[1] >= y1 - top_tol]
    if not top:
        return cs, None, None
    xcut = max(p[0] for p in top)
    # 该横画的 y 带：在 xcut 内侧 20 单位处纵向扫描，取最高那条带
    runs = scan_runs(cs, xcut - 20, "v")
    if not runs:
        return cs, None, None
    # 只取"包含顶边"的那一条带 —— 否则会把整根竖笔当成横带
    probe = y1 - top_tol - 2
    band = [r for r in runs if r[0] - 1 <= probe <= r[1] + 1]
    if not band:
        band = [min(runs, key=lambda r: abs(r[1] - y1))]
    yb0, yb1 = band[0]
    ylo, yhi = yb0 - 2, yb1 + top_tol

    out = []
    moved = 0
    for c in cs:
        nc = []
        for (x, y) in c:
            if x > xcut and ylo <= y <= yhi:
                nc.append((xcut, y))
                moved += 1
            else:
                nc.append((x, y))
        clean = [nc[0]]
        for p in nc[1:]:
            if abs(p[0] - clean[-1][0]) > 0.4 or abs(p[1] - clean[-1][1]) > 0.4:
                clean.append(p)
        if clean[0] != clean[-1]:
            clean.append(clean[0])
        out.append(clean)
    return out, xcut, (ylo, yhi, moved)


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


def render(cs, path, size=460):
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
    ap.add_argument("--size", type=int, default=460)
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

    new, xcut, info = square_end(cs)
    if info and (info[2] > 30 or (info[1] - info[0]) > 140):
        print(f"跳过 {a.glyph}: 投影 {info[2]} 点 / 带高 {info[1]-info[0]:.0f}，"
              f"说明这不是\"斜笔从横端斜切出去\"，而是横折结构，不能按收方处理")
        render(cs, a.out, a.size)
        return
    render(new, a.out, a.size)
    if xcut is None:
        print(f"saved {a.out}  未找到顶边，未改动")
    else:
        ylo, yhi, moved = info
        print(f"saved {a.out}  xcut={xcut:.0f}  带 y={ylo:.0f}..{yhi:.0f}  "
              f"投影 {moved} 点  端面长 {yhi-ylo:.0f}")


if __name__ == "__main__":
    main()
