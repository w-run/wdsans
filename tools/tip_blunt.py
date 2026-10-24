"""尖端钝化：把笔末端过尖的"针尖"沿笔画方向切回来。

背景（实测）：思源的撇尾/捺尾收锋过长，末端厚度只有 1–4 单位（等于零），
下缘是内凹弧，看起来像被咬掉一块。鸿蒙/OPPO 的末端有厚度、下缘接近直线。

做法（只作用于指定区块，别处一个点都不动）：
  1. 区块内找离笔画中心最远的那个点 = 尖端 T
  2. 用区块内点的 PCA 主方向估笔画方向 u
  3. 沿 u 把 T 往回退 cut 距离得到切平面，把越过的点投影到平面上
  4. 结果：尖端变成一段短端面，厚度至少约 cut 的正弦分量

用法：
    python3 tip_blunt.py --font ref/shs/shs-400.otf --glyph 永 \
        --block ec-fe --cut 30 --out /tmp/t.png
"""
import argparse
import math
import subprocess
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen        # noqa: E402
from frame import X0, X1, Y_TOP, Y_BOT, cell_box, CELL   # noqa: E402

HEX = "0123456789abcdef"


def block_box(spec):
    """'ec-fe' → em 坐标矩形。"""
    a, b = spec.split("-") if "-" in spec else (spec, spec)
    ax, ay = cell_box(a)
    bx, by = cell_box(b)
    x0 = min(ax, bx)
    x1 = max(ax, bx) + CELL
    ytop = max(ay, by)
    ybot = min(ay, by) - CELL
    return x0, ytop, x1, ybot


def tip_blunt(cs, box, cut):
    x0, ytop, x1, ybot = box
    # 收集区块内的点
    inner = []
    for ci, c in enumerate(cs):
        for p in c:
            if x0 <= p[0] <= x1 and ybot <= p[1] <= ytop:
                inner.append((ci, p))
    if len(inner) < 8:
        return cs, None

    # 笔画方向：用区块内点的 PCA 主方向
    mx = sum(p[0] for _, p in inner) / len(inner)
    my = sum(p[1] for _, p in inner) / len(inner)
    sxx = sum((p[0] - mx) ** 2 for _, p in inner)
    syy = sum((p[1] - my) ** 2 for _, p in inner)
    sxy = sum((p[0] - mx) * (p[1] - my) for _, p in inner)
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ux, uy = math.cos(ang), math.sin(ang)

    # 尖端：沿 u 投影最远的点
    proj = [((p[0] - mx) * ux + (p[1] - my) * uy, p) for _, p in inner]
    _, tip = max(proj, key=lambda t: t[0])
    lim = (tip[0] - mx) * ux + (tip[1] - my) * uy - cut

    out = []
    moved = 0
    for c in cs:
        nc = []
        for p in c:
            if x0 <= p[0] <= x1 and ybot <= p[1] <= ytop:
                d = (p[0] - mx) * ux + (p[1] - my) * uy
                if d > lim:
                    nc.append((mx + ux * lim, my + uy * lim))
                    moved += 1
                    continue
            nc.append(p)
        # 去重
        clean = [nc[0]]
        for q in nc[1:]:
            if abs(q[0] - clean[-1][0]) > 0.4 or abs(q[1] - clean[-1][1]) > 0.4:
                clean.append(q)
        if clean[0] != clean[-1]:
            clean.append(clean[0])
        out.append(clean)
    return out, (round(tip[0]), round(tip[1]), moved)


def to_svg(cs, path, size=620, box=None):
    if box:
        x0, ytop, x1, ybot = box
    else:
        x0, ytop, x1, ybot = X0, Y_TOP, X1, Y_BOT
    w, h = x1 - x0, ytop - ybot
    d = []
    for c in cs:
        if len(c) < 3:
            continue
        d.append(f"M{c[0][0]:.1f} {c[0][1]:.1f}")
        for p in c[1:]:
            d.append(f"L{p[0]:.1f} {p[1]:.1f}")
        d.append("Z")
    hpx = int(size * h / w)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{hpx}" '
           f'viewBox="{x0} {-ytop} {w} {h}">'
           f'<rect x="{x0}" y="{-ytop}" width="{w}" height="{h}" fill="white"/>'
           f'<g transform="scale(1,-1)"><path d="{" ".join(d)}" fill="#111" '
           f'fill-rule="nonzero"/></g></svg>')
    open(path + ".svg", "w").write(svg)
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(hpx),
                    "-o", path, path + ".svg"], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--glyph", required=True)
    ap.add_argument("--block", required=True, help="格位区块，如 ec-fe")
    ap.add_argument("--cut", type=float, default=30.0, help="沿笔画方向切回的距离")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=620)
    ap.add_argument("--zoom", action="store_true", help="只渲染该区块")
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

    box = block_box(a.block)
    new, info = tip_blunt(cs, box, a.cut)
    to_svg(new, a.out, a.size, box if a.zoom else None)
    if info:
        print(f"saved {a.out}  区块 {a.block}  尖端 {info[:2]}  移动 {info[2]} 点  cut={a.cut}")
    else:
        print(f"saved {a.out}  区块内点太少，未处理")


if __name__ == "__main__":
    main()
