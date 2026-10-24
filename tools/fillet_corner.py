"""单角倒圆：在指定区域里找最大的那个转角，用相切圆弧替换。

为什么不用窗口平滑：轮廓点极密，窗口平均会在段边界拉出缺口和尖刺。
倒圆是标准几何构造 —— 两条边各取切点，圆心在角平分线上，半径给定 ——
结果一定是光滑圆弧，且只影响这一个角。

用法：
    python3 fillet_corner.py --font ref/shs/shs-400.otf --glyph 乙 \
        --region 20,-70,320,220 --radius 120 --out /tmp/f.png
"""
import argparse
import math
import subprocess
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen        # noqa: E402
from frame import X0, X1, Y_TOP, Y_BOT   # noqa: E402

ARC_SEG = 12


def turn_at(pts, i):
    n = len(pts) - 1 if pts[0] == pts[-1] else len(pts)
    a, b, c = pts[(i - 3) % n], pts[i % n], pts[(i + 3) % n]
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    l1, l2 = math.hypot(*v1), math.hypot(*v2)
    if l1 < 1e-9 or l2 < 1e-9:
        return 0.0
    cosv = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
    return math.degrees(math.acos(cosv))


def fillet_one(pts, idx, radius):
    """在 idx 处倒半径 radius 的圆。返回新点列（未闭合）。"""
    n = len(pts) - 1 if pts[0] == pts[-1] else len(pts)
    b = pts[idx]
    # 沿两侧各走一段，取方向
    back = max(4, n // 40)
    fwd = max(4, n // 40)
    a = pts[(idx - back) % n]
    c = pts[(idx + fwd) % n]
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    l1, l2 = math.hypot(*v1), math.hypot(*v2)
    if l1 < 1e-9 or l2 < 1e-9:
        return pts
    u1 = (v1[0] / l1, v1[1] / l1)     # 指向角点
    u2 = (v2[0] / l2, v2[1] / l2)     # 离开角点
    cosv = max(-1.0, min(1.0, -u1[0] * u2[0] - u1[1] * u2[1]))
    ang = math.acos(cosv)              # 转角
    if ang < 0.15 or ang > math.pi - 0.05:
        return pts
    d = radius / math.tan(ang / 2)     # 切点到角的距离
    p1 = (b[0] - u1[0] * d, b[1] - u1[1] * d)
    p2 = (b[0] + u2[0] * d, b[1] + u2[1] * d)
    # 圆心：角平分线方向
    bx, by = (-u1[0] + u2[0]), (-u1[1] + u2[1])
    lb = math.hypot(bx, by)
    if lb < 1e-9:
        return pts
    bx, by = bx / lb, by / lb
    dist = radius / math.sin(ang / 2)
    ctr = (b[0] + bx * dist, b[1] + by * dist)
    a1 = math.atan2(p1[1] - ctr[1], p1[0] - ctr[0])
    a2 = math.atan2(p2[1] - ctr[1], p2[0] - ctr[0])
    da = a2 - a1
    while da > math.pi:
        da -= 2 * math.pi
    while da < -math.pi:
        da += 2 * math.pi
    arc = [(ctr[0] + radius * math.cos(a1 + da * k / ARC_SEG),
            ctr[1] + radius * math.sin(a1 + da * k / ARC_SEG))
           for k in range(ARC_SEG + 1)]
    # 用弧**精确替换**切点之间的那段：按最近点索引切，避免接缝错位
    i1 = min(range(n), key=lambda i: math.dist(pts[i], p1))
    i2 = min(range(n), key=lambda i: math.dist(pts[i], p2))
    if i1 > i2:
        i1, i2 = i2, i1
    out = list(pts[:i1]) + arc + list(pts[i2 + 1:])
    return out


def in_box(p, box):
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--glyph", required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--radius", type=float, default=120)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=440)
    ap.add_argument("--box", default=None,
                    help="只渲染这块区域 x0,y0,x1,y1（em 坐标），与 glyph_view 一致")
    a = ap.parse_args()
    box = tuple(float(v) for v in a.region.split(","))

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

    new_cs = []
    total = 0
    for c in cs:
        closed = c[0] == c[-1]
        pts = c[:-1] if closed else c
        n = len(pts)
        cand = [(turn_at(pts, i), i) for i in range(n) if in_box(pts[i], box)]
        if not cand:
            new_cs.append(list(c))
            continue
        ang, idx = max(cand)
        if ang < 25:
            new_cs.append(list(c))
            continue
        pts2 = fillet_one(pts, idx, a.radius)
        if closed:
            pts2 = list(pts2) + [pts2[0]]
        new_cs.append(pts2)
        total += 1

    if a.box:
        bx0, by0, bx1, by1 = [float(v) for v in a.box.split(",")]
        bx0, bx1 = min(bx0, bx1), max(bx0, bx1)
        by0, by1 = min(by0, by1), max(by0, by1)
        w, h = bx1 - bx0, by1 - by0
        ox, oy = bx0, by1
    else:
        ox, oy = X0, Y_TOP
        w, h = X1 - X0, Y_TOP - Y_BOT
    d = []
    for c in new_cs:
        if len(c) < 3:
            continue
        d.append(f"M{c[0][0]:.1f} {c[0][1]:.1f}")
        for p in c[1:]:
            d.append(f"L{p[0]:.1f} {p[1]:.1f}")
        d.append("Z")
    hpx = int(a.size * h / w) if w else a.size
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{a.size}" height="{hpx}" '
           f'viewBox="{ox} {-oy} {w} {h}">'
           f'<rect x="{ox}" y="{-oy}" width="{w}" height="{h}" fill="white"/>'
           f'<g transform="scale(1,-1)"><path d="{" ".join(d)}" fill="#111" '
           f'fill-rule="nonzero"/></g></svg>')
    with open(a.out + ".svg", "w") as f:
        f.write(svg)
    subprocess.run(["rsvg-convert", "-w", str(a.size), "-h", str(hpx),
                    "-o", a.out, a.out + ".svg"], check=True)
    print(f"saved {a.out}  倒圆 {total} 处  R={a.radius}")


if __name__ == "__main__":
    main()
