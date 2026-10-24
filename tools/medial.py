"""笔道骨架（中线）：距离变换求脊线。

为什么不用扫描线：一条笔道在扫描线上只切出一个墨段，中点就是中线点，
但扫描方向是固定的 —— 横笔要竖着扫、竖笔要横着扫，转向的笔画（弯钩）
用任何一个方向都会失真。骨架没有这个问题。

流程：
  1. rsvg 光栅化（与预览同一渲染器，不自造光栅器）
  2. 精确欧氏距离变换（Felzenszwalb 两趟一维算法）
  3. 脊线 = 距离场的局部极大，沿扫描方向抽稀
  4. 最近邻串成路径，输出 em 坐标

用法：
    python3 medial.py --font ref/shs/shs-400.otf --glyph 乙 --out /tmp/m.png
"""
import argparse
import math
import subprocess
import sys
import tempfile

import numpy as np
from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen      # noqa: E402
from frame import X0, X1, Y_TOP, Y_BOT   # noqa: E402

SCALE = 2.0        # 光栅化倍率：1 em 单位 = 2 像素


def rasterize(cs, path, size):
    w, h = X1 - X0, Y_TOP - Y_BOT
    d = []
    for c in cs:
        d.append(f"M{c[0][0]:.1f} {c[0][1]:.1f}")
        for p in c[1:]:
            d.append(f"L{p[0]:.1f} {p[1]:.1f}")
        d.append("Z")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
           f'viewBox="{X0} {-Y_TOP} {w} {h}">'
           f'<rect x="{X0}" y="{-Y_TOP}" width="{w}" height="{h}" fill="white"/>'
           f'<g transform="scale(1,-1)"><path d="{" ".join(d)}" fill="black" '
           f'fill-rule="nonzero"/></g></svg>')
    with open(path + ".svg", "w") as f:
        f.write(svg)
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size),
                    "-o", path, path + ".svg"], check=True)


def edt_1d(f, n):
    """Felzenszwalb 一维平方距离变换。f 为初始代价，n 为长度。"""
    d = np.empty(n)
    v = np.zeros(n, dtype=int)
    z = np.zeros(n + 1)
    k = 0
    v[0] = 0
    z[0] = -np.inf
    z[1] = np.inf
    for q in range(1, n):
        while True:
            s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k])
            if s <= z[k]:
                k -= 1
            else:
                break
        k += 1
        v[k] = q
        z[k] = s
        z[k + 1] = np.inf
    k = 0
    for q in range(n):
        while z[k + 1] < q:
            k += 1
        d[q] = (q - v[k]) ** 2 + f[v[k]]
    return d


def edt(mask):
    """二维精确欧氏距离（到最近的 False 像素）。"""
    h, w = mask.shape
    big = 1e12
    f = np.where(mask, big, 0.0)
    # 列方向
    for x in range(w):
        f[:, x] = edt_1d(f[:, x], h)
    # 行方向
    for y in range(h):
        f[y, :] = edt_1d(f[y, :], w)
    return np.sqrt(f)


def skeleton(mask, max_iter=60):
    """Zhang-Suen 细化：得到 1 像素宽的中轴。"""
    img = mask.copy()

    def neighbours(I):
        P2 = np.roll(I, -1, 0)
        P3 = np.roll(np.roll(I, -1, 0), 1, 1)
        P4 = np.roll(I, 1, 1)
        P5 = np.roll(np.roll(I, 1, 0), 1, 1)
        P6 = np.roll(I, 1, 0)
        P7 = np.roll(np.roll(I, 1, 0), -1, 1)
        P8 = np.roll(I, -1, 1)
        P9 = np.roll(np.roll(I, -1, 0), -1, 1)
        return P2, P3, P4, P5, P6, P7, P8, P9

    for _ in range(max_iter):
        changed = False
        for step in (0, 1):
            P2, P3, P4, P5, P6, P7, P8, P9 = neighbours(img)
            B = (P2.astype(int) + P3 + P4 + P5 + P6 + P7 + P8 + P9)
            seq = [P2, P3, P4, P5, P6, P7, P8, P9, P2]
            A = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(int) for i in range(8))
            if step == 0:
                cond = (P2 & P4 & P6) == 0
                cond2 = (P4 & P6 & P8) == 0
            else:
                cond = (P2 & P4 & P8) == 0
                cond2 = (P2 & P6 & P8) == 0
            rm = img & (B >= 2) & (B <= 6) & (A == 1) & cond & cond2
            if rm.any():
                img = img & ~rm
                changed = True
        if not changed:
            break
    return img


def order_path(pts):
    """最近邻串成路径。"""
    if len(pts) < 3:
        return pts
    left = list(pts)
    # 从最左端开始
    cur = min(left, key=lambda p: p[0])
    left.remove(cur)
    path = [cur]
    while left:
        nxt = min(left, key=lambda p: (p[0] - cur[0]) ** 2 + (p[1] - cur[1]) ** 2)
        if (nxt[0] - cur[0]) ** 2 + (nxt[1] - cur[1]) ** 2 > 40 ** 2:
            break
        path.append(nxt)
        left.remove(nxt)
        cur = nxt
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--glyph", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=None)
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

    size = a.size or int((X1 - X0) * SCALE)
    tmp = tempfile.mktemp(suffix=".png")
    rasterize(cs, tmp, size)

    from PIL import Image
    im = np.array(Image.open(tmp).convert("L"))
    mask = im < 128
    dist = edt(mask)
    sk = skeleton(mask)
    ys, xs = np.where(sk)

    # 像素 → em 坐标
    k = (X1 - X0) / size
    pts = [(X0 + x * k, Y_TOP - y * k) for x, y in zip(xs, ys)]
    # 沿骨架串成路径（从端点开始，逐点走相邻）
    skset = set((int(x), int(y)) for x, y in zip(xs, ys))
    if skset:
        ends = [p for p in skset if sum((p[0] + dx, p[1] + dy) in skset
                                        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))) == 1]
        start = min(ends) if ends else min(skset)
        path_px, seen = [start], {start}
        cur = start
        while True:
            nxt = None
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                q = (cur[0] + dx, cur[1] + dy)
                if q in skset and q not in seen:
                    nxt = q
                    break
            if nxt is None:
                break
            path_px.append(nxt)
            seen.add(nxt)
            cur = nxt
        path_pts = [(X0 + x * k, Y_TOP - y * k) for x, y in path_px]
    else:
        path_pts = []

    # 叠加图
    import subprocess as sp
    w, h = size, size
    # 全部骨架点（不排序）—— 用于确认中轴位置
    circles = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="#1f6fd0"/>'
        for x, y in pts)
    d = []
    for c in cs:
        d.append(f"M{c[0][0]:.1f} {c[0][1]:.1f}")
        for p in c[1:]:
            d.append(f"L{p[0]:.1f} {p[1]:.1f}")
        d.append("Z")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="{X0} {-Y_TOP} {X1-X0} {Y_TOP-Y_BOT}">'
           f'<rect x="{X0}" y="{-Y_TOP}" width="{X1-X0}" height="{Y_TOP-Y_BOT}" fill="white"/>'
           f'<g transform="scale(1,-1)"><path d="{" ".join(d)}" fill="#e8e8e8" '
           f'fill-rule="nonzero"/></g>'
           f'<g transform="scale(1,-1)">{circles}</g></svg>')
    with open(a.out + ".svg", "w") as f:
        f.write(svg)
    sp.run(["rsvg-convert", "-w", str(w), "-h", str(h), "-o", a.out, a.out + ".svg"],
           check=True)
    ws = [2 * dist[int(round((Y_TOP - y) / k)), int(round((x - X0) / k))]
          for x, y in pts] if pts else []
    med = float(np.median(ws)) * k if ws else 0
    print(f"saved {a.out}  骨���点 {len(pts)}  可串路径 {len(path_pts)}  "
          f"笔宽中位 {med:.0f} em单位")


if __name__ == "__main__":
    main()
