"""按骨架重画笔道：少锚点 + G1 连续 + 定宽扫描。

流程：
  1. 光栅化 → Zhang-Suen 细化 → 骨架（medial.py 的同一套）
  2. 取骨架的**最长测地路径**（两次 BFS 求直径），自动剪掉端部毛刺
  3. 沿路径等距取 N 个锚点，Catmull-Rom 转三次贝塞尔 —— 天然 G1 连续
  4. 沿曲线法线按局部笔宽扫出左右边界，合成闭合轮廓

为什么要 N 个锚点而不是照抄原曲线：
OPPO 的圆润是"很多小段拼出来的"，这里要的是"少量锚点 + 切向连续"，
即同样的形状、更少的节点。

用法：
    python3 rebuild.py --font ref/shs/shs-400.otf --glyph 乙 --anchors 6 \
        --out /tmp/rebuild_乙.png
"""
import argparse
import math
import subprocess
import sys
import tempfile

import numpy as np
from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen           # noqa: E402
from frame import X0, X1, Y_TOP, Y_BOT   # noqa: E402
from medial import rasterize, edt, skeleton   # noqa: E402


def longest_path(mask_pts):
    """骨架像素集合 → 最长测地路径（两次 BFS）。"""
    adj = {}
    for (x, y) in mask_pts:
        nb = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                q = (x + dx, y + dy)
                if q in mask_pts:
                    nb.append(q)
        adj[(x, y)] = nb

    def bfs(start):
        dist = {start: 0}
        prev = {start: None}
        q = [start]
        far = start
        while q:
            nq = []
            for u in q:
                for v in adj[u]:
                    if v not in dist:
                        dist[v] = dist[u] + 1
                        prev[v] = u
                        if dist[v] > dist[far]:
                            far = v
                        nq.append(v)
            q = nq
        return far, prev

    a, _ = bfs(next(iter(mask_pts)))
    b, prev = bfs(a)
    path = []
    cur = b
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return path[::-1]


def resample(path_pts, n):
    """按弧长等距取 n 个点（路径首尾保留）。"""
    if len(path_pts) <= n:
        return path_pts
    acc = [0.0]
    for i in range(1, len(path_pts)):
        acc.append(acc[-1] + math.dist(path_pts[i - 1], path_pts[i]))
    total = acc[-1]
    out = []
    for k in range(n):
        target = total * k / (n - 1)
        i = 0
        while i < len(acc) - 1 and acc[i + 1] < target:
            i += 1
        if i >= len(acc) - 1:
            out.append(path_pts[-1])
            continue
        t = (target - acc[i]) / max(1e-9, acc[i + 1] - acc[i])
        p0, p1 = path_pts[i], path_pts[i + 1]
        out.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))
    return out


def chaikin(P, iters=3):
    """Chaikin 角切割：反复把折线角削掉，收敛到 G1 光滑曲线，不会过冲。"""
    pts = list(P)
    for _ in range(iters):
        nxt = [pts[0]]
        for i in range(len(pts) - 1):
            p, q = pts[i], pts[i + 1]
            nxt.append((0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]))
            nxt.append((0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1]))
        nxt.append(pts[-1])
        pts = nxt
    return pts


def catmull_to_bezier(P):
    """Catmull-Rom → 三次贝塞尔控制点，返回每段的 (p0, c1, c2, p1)。"""
    n = len(P)
    ext = [P[0]] + list(P) + [P[-1]]
    segs = []
    for i in range(1, n):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        segs.append((p1, c1, c2, p2))
    return segs


def sample_bezier(segs, per=24):
    pts = []
    for (p0, c1, c2, p1) in segs:
        for i in range(per):
            t = i / per
            mt = 1 - t
            x = (mt ** 3 * p0[0] + 3 * mt * mt * t * c1[0]
                 + 3 * mt * t * t * c2[0] + t ** 3 * p1[0])
            y = (mt ** 3 * p0[1] + 3 * mt * mt * t * c1[1]
                 + 3 * mt * t * t * c2[1] + t ** 3 * p1[1])
            pts.append((x, y))
    pts.append(segs[-1][3])
    return pts


def sweep(center, widths):
    left, right = [], []
    n = len(center)
    for i in range(n):
        if i == 0:
            tx, ty = center[1][0] - center[0][0], center[1][1] - center[0][1]
        elif i == n - 1:
            tx, ty = center[-1][0] - center[-2][0], center[-1][1] - center[-2][1]
        else:
            tx, ty = (center[i + 1][0] - center[i - 1][0],
                      center[i + 1][1] - center[i - 1][1])
        L = math.hypot(tx, ty) or 1e-6
        nx, ny = -ty / L, tx / L
        h = widths[i] / 2.0
        left.append((center[i][0] + nx * h, center[i][1] + ny * h))
        right.append((center[i][0] - nx * h, center[i][1] - ny * h))
    return left + right[::-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--glyph", required=True)
    ap.add_argument("--anchors", type=int, default=6)
    ap.add_argument("--width", type=float, default=None, help="指定笔宽（默认取实测中位）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=420, help="输出 PNG 边长")
    ap.add_argument("--raster", type=int, default=560,
                    help="光栅化边长（骨架精度）；太大 EDT 会吃满内存")
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

    size = a.raster
    tmp = tempfile.mktemp(suffix=".png")
    rasterize(cs, tmp, size)
    from PIL import Image
    im = np.array(Image.open(tmp).convert("L"))
    mask = im < 128
    dist = edt(mask)
    sk = skeleton(mask)
    ys, xs = np.where(sk)
    skset = set((int(x), int(y)) for x, y in zip(xs, ys))
    if not skset:
        raise SystemExit("骨架为空")

    path_px = longest_path(skset)
    k = (X1 - X0) / size
    path = [(X0 + x * k, Y_TOP - y * k) for x, y in path_px]

    anchors = resample(path, max(8, a.anchors))
    center = chaikin(anchors, 3)

    # 局部笔宽：取骨架像素的 2*距离
    if a.width:
        widths = [a.width] * len(center)
    else:
        _ = None
        ws = []
        for (cx, cy) in center:
            px = int(round((cx - X0) / k))
            py = int(round((Y_TOP - cy) / k))
            px = max(0, min(size - 1, px))
            py = max(0, min(size - 1, py))
            ws.append(2 * dist[py, px] * k)
        med = float(np.median([w for w in ws if w > 5] or [78]))
        widths = [w if w > 5 else med for w in ws]

    outline = sweep(center, widths)

    d = [f"M{outline[0][0]:.1f} {outline[0][1]:.1f}"]
    for p in outline[1:]:
        d.append(f"L{p[0]:.1f} {p[1]:.1f}")
    d.append("Z")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{a.size}" '
           f'height="{a.size}" viewBox="{X0} {-Y_TOP} {X1-X0} {Y_TOP-Y_BOT}">'
           f'<rect x="{X0}" y="{-Y_TOP}" width="{X1-X0}" height="{Y_TOP-Y_BOT}" fill="white"/>'
           f'<g transform="scale(1,-1)"><path d="{" ".join(d)}" fill="#111" '
           f'fill-rule="nonzero"/></g></svg>')
    with open(a.out + ".svg", "w") as f:
        f.write(svg)
    subprocess.run(["rsvg-convert", "-w", str(a.size), "-h", str(a.size),
                    "-o", a.out, a.out + ".svg"], check=True)
    print(f"saved {a.out}  锚点 {len(anchors)}  平滑后 {len(center)} 点  "
          f"骨架长 {len(path_px)}px  笔宽中位 {float(np.median(widths)):.0f}")


if __name__ == "__main__":
    main()
