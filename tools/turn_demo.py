"""转折规范样张：直角 / 定值圆弧 / 曲率连续，三种处理的差别。

为什么需要这张图：
"拐角圆润"不是把角磨圆就完事。三种做法观感完全不同：

  A 直角        两段直线硬接，转折处曲率无穷大
  B 定值圆弧    插入半径 R 的圆弧。位置连续、切向连续（G1），
                但曲率在接点处从 0 突跳到 1/R —— 眼睛仍能看到"接缝"
  C 曲率连续    曲率从 0 平滑升到峰值再降回 0（回旋线/clothoid），
                没有突跳，这就是"过渡自然"

参数：主笔宽 W，转角 90°，两种处理用相同的外接尺寸，便于对比。

用法：
    python3 turn_demo.py --out /tmp/turn.png --width 78 --radius 200
"""
import argparse
import math
import subprocess


def polyline_to_path(pts):
    if not pts:
        return ""
    d = [f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for p in pts[1:]:
        d.append(f"L{p[0]:.1f} {p[1]:.1f}")
    d.append("Z")
    return " ".join(d)


def sweep(center, width):
    """沿中心线用固定宽度扫出闭合轮廓（法向偏移）。"""
    left, right = [], []
    n = len(center)
    for i in range(n):
        if i == 0:
            tx, ty = center[1][0] - center[0][0], center[1][1] - center[0][1]
        elif i == n - 1:
            tx, ty = center[-1][0] - center[-2][0], center[-1][1] - center[-2][1]
        else:
            tx, ty = center[i + 1][0] - center[i - 1][0], center[i + 1][1] - center[i - 1][1]
        L = math.hypot(tx, ty) or 1e-6
        nx, ny = -ty / L, tx / L
        h = width / 2.0
        left.append((center[i][0] + nx * h, center[i][1] + ny * h))
        right.append((center[i][0] - nx * h, center[i][1] - ny * h))
    return left + right[::-1]


def center_sharp(L, W, r):
    """直角：从 (0,L) 竖直到 (L,0) 横，直接拐。"""
    return [(0, L), (0, 0), (L, 0)]


def center_arc(L, W, r):
    """定值圆弧：半径 r 的 1/4 圆接两段直线。"""
    pts = [(0, L)]
    for i in range(1, 12):
        t = i / 12
        pts.append((0, L - t * (L - r)))
    cx, cy = r, r
    for i in range(0, 21):
        th = math.pi + (math.pi / 2) * i / 20        # 180° → 270°
        pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
    for i in range(1, 12):
        t = i / 12
        pts.append((r + t * (L - r), 0))
    return pts


def center_clothoid(L, W, r, n=60):
    """曲率连续：曲率沿弧长线性上升再下降（对称的缓入缓出）。"""
    # 用参数化的积分构造：前半段曲率 0→k，后半段 k→0
    total = math.pi / 2            # 总转角
    S = r * math.pi / 2            # 弧长
    # ∫ k ds = kmax * 2S/π = total  →  kmax = total*π/(2S)
    kmax = total * math.pi / (2 * S)
    pts = [(0, L)]
    # 直段
    lead = (L - r)
    for i in range(1, 10):
        t = i / 10
        pts.append((0, L - t * lead))
    # 缓入缓出弧：曲率 k(s) = kmax * sin(pi * s / S)
    x, y, th = 0.0, L - lead, -math.pi / 2      # 朝下
    steps = n
    ds = S / steps
    for i in range(steps):
        s = (i + 0.5) * ds
        k = kmax * math.sin(math.pi * s / S)
        th += k * ds
        x += math.cos(th) * ds
        y += math.sin(th) * ds
        pts.append((x, y))
    # 收尾直线
    ex, ey = pts[-1]
    for i in range(1, 10):
        t = i / 10
        pts.append((ex + t * (L - ex), ey))
    return pts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=float, default=78)
    ap.add_argument("--radius", type=float, default=190)
    ap.add_argument("--size", type=int, default=420)
    a = ap.parse_args()

    L = 470.0
    W = a.width
    r = a.radius
    cells = [
        ("A  sharp", center_sharp(L, W, r)),
        ("B  arc R", center_arc(L, W, r)),
        ("C  clothoid", center_clothoid(L, W, r)),
    ]

    pad = 60
    cellw = L + pad * 2
    cellh = L + pad * 2
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'width="{cellw*3}" height="{cellh}" viewBox="0 0 {cellw*3} {cellh}">',
           f'<rect width="{cellw*3}" height="{cellh}" fill="white"/>']
    for i, (lab, ctr) in enumerate(cells):
        ox = i * cellw + pad
        oy = pad
        # y 轴向上：翻转
        pts = [(ox + x, cellh - oy - y) for (x, y) in ctr]
        outline = sweep(pts, W)
        svg.append(f'<path d="{polyline_to_path(outline)}" fill="#111" '
                   f'fill-rule="nonzero"/>')
        svg.append(f'<text x="{ox}" y="{cellh-14}" font-family="DejaVu Sans, sans-serif" '
                   f'font-size="20" fill="#444444">{lab}</text>')
    svg.append("</svg>")
    with open(a.out + ".svg", "w") as f:
        f.write("\n".join(svg))
    subprocess.run(["rsvg-convert", "-w", str(cellw * 3), "-h", str(cellh),
                    "-o", a.out, a.out + ".svg"], check=True)
    print("saved", a.out)


if __name__ == "__main__":
    main()
