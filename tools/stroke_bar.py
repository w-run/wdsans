"""stroke_bar：把"楔形"笔画改成"等宽条"。

思源的斜笔（撇/捺/钩）和点，两侧是用弧线连接的，中间鼓起再收回，
视觉上像楔形、外扩。OPPO / HOS 的两侧是直线、间距恒定。

做法（核心是"垂直坐标归一"）：
  1. 对轮廓做主成分分析，得到笔画轴线 u 与垂直方向 n
  2. 把每个点投影成 (t, v)：t 沿轴、v 垂直
  3. 把 |v| 统一压到 w/2（w 取实测中位宽度）→ 两侧变平行直线
  4. 只在最末端 taper 区域内按比例收到 0（保留收锋）

点（dot）额外按 OPPO 的尺寸收短：轴长 333、宽 80。

用法：
    python3 stroke_bar.py --font ref/shs/shs-400.otf --glyph 永 \
        --out /tmp/yong_bar.png [--zoom]
"""
import argparse
import math
import subprocess
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frame import X0, X1, Y_TOP, Y_BOT   # noqa: E402

DOT_AXIS = 333.0
DOT_WIDTH = 80.0
MIN_AREA = 0.002
MAX_DOT_AREA = 0.055


def to_contours(v):
    cs, cur = [], []
    for op, args in v:
        if op == "moveTo":
            if len(cur) > 2:
                cs.append(cur)
            cur = [tuple(args[0])]
        elif op == "lineTo":
            cur.append(tuple(args[0]))
        elif op == "curveTo":
            cur.append(tuple(args[-1]))
        elif op in ("closePath", "endPath"):
            if len(cur) > 2:
                if cur[0] != cur[-1]:
                    cur.append(cur[0])
                cs.append(cur)
            cur = []
    if len(cur) > 2:
        if cur[0] != cur[-1]:
            cur.append(cur[0])
        cs.append(cur)
    return cs


def area(c):
    s = 0.0
    for i in range(len(c) - 1):
        s += c[i][0] * c[i + 1][1] - c[i + 1][0] * c[i][1]
    return abs(s) / 2


def pca(c):
    mx = sum(p[0] for p in c) / len(c)
    my = sum(p[1] for p in c) / len(c)
    sxx = sum((p[0] - mx) ** 2 for p in c)
    syy = sum((p[1] - my) ** 2 for p in c)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in c)
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
    return (mx, my), (math.cos(ang), math.sin(ang))


def rebuild_dot(c, axis_max=DOT_AXIS, width=DOT_WIDTH):
    """点：直接生成等宽平行四边形（不重映射原节点，避免拉成薄片）。"""
    (mx, my), (ux, uy) = pca(c)
    nx, ny = -uy, ux
    pts = c[:-1] if c[0] == c[-1] else c
    ts = [(p[0] - mx) * ux + (p[1] - my) * uy for p in pts]
    L = min(axis_max, max(ts) - min(ts))
    tc = (max(ts) + min(ts)) / 2
    h = width / 2
    a = (mx + ux * (tc - L / 2) - nx * h, my + uy * (tc - L / 2) - ny * h)
    b = (mx + ux * (tc + L / 2) - nx * h, my + uy * (tc + L / 2) - ny * h)
    d = (mx + ux * (tc + L / 2) + nx * h, my + uy * (tc + L / 2) + ny * h)
    e = (mx + ux * (tc - L / 2) + nx * h, my + uy * (tc - L / 2) + ny * h)
    return [a, b, d, e, a]


def barify(c, width=None, taper=0.22, force_axis=None):
    """把轮廓改成等宽条。返回新点列。"""
    (mx, my), (ux, uy) = pca(c)
    nx, ny = -uy, ux
    pts = c[:-1] if c[0] == c[-1] else c
    ts = [(p[0] - mx) * ux + (p[1] - my) * uy for p in pts]
    vs = [-(p[0] - mx) * uy + (p[1] - my) * ux for p in pts]
    t0, t1 = min(ts), max(ts)
    L = t1 - t0
    if L < 20:
        return list(c)
    w = width if width else 2 * (sum(abs(v) for v in vs) / len(vs))
    tc = (t0 + t1) / 2
    if force_axis:
        L = force_axis
        t1 = tc + L / 2
        t0 = tc - L / 2
    out = []
    for t, v in zip(ts, vs):
        tn = (t - t0) / L if L else 0
        s = 1.0
        if taper > 0 and tn > 1 - taper:         # 尾端收锋
            s = max(0.0, (1 - tn) / taper)
        sign = 1 if v >= 0 else -1
        vv = sign * (w / 2) * s
        # 端点面（|v| 接近 w/2）保持占满
        if abs(v) > w * 0.42 and s > 0.99:
            vv = sign * (w / 2)
        t2 = max(t0, min(t1, t))
        out.append((mx + ux * t2 + nx * vv, my + uy * t2 + ny * vv))
    out.append(out[0])
    return out


def to_svg(cs, path, size=520, box=None):
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
    hp = int(size * h / w)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{hp}" '
           f'viewBox="{x0} {-ytop} {w} {h}">'
           f'<rect x="{x0}" y="{-ytop}" width="{w}" height="{h}" fill="white"/>'
           f'<g transform="scale(1,-1)"><path d="{" ".join(d)}" fill="#111" '
           f'fill-rule="nonzero"/></g></svg>')
    open(path + ".svg", "w").write(svg)
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(hp),
                    "-o", path, path + ".svg"], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--glyph", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=520)
    ap.add_argument("--diag-min-aspect", type=float, default=2.0)
    ap.add_argument("--taper", type=float, default=0.22)
    ap.add_argument("--no-diag", dest="diag", action="store_false", default=True,
                    help="只处理点，跳过斜笔（斜笔需笔画分解，当前不可靠）")
    a = ap.parse_args()

    font = TTFont(a.font)
    gs = font.getGlyphSet()
    gn = font.getBestCmap().get(ord(a.glyph))
    if not gn:
        raise SystemExit(f"缺字 {a.glyph}")
    pen = RecordingPen()
    gs[gn].draw(pen)
    font.close()

    cs = to_contours(pen.value)
    out = []
    n_dot = n_bar = 0
    for c in cs:
        A = area(c) / 1e6            # em²
        xs = [p[0] for p in c]
        ys = [p[1] for p in c]
        (mx, my), (ux, uy) = pca(c)
        ts = [(p[0] - mx) * ux + (p[1] - my) * uy for p in c]
        vs = [-(p[0] - mx) * uy + (p[1] - my) * ux for p in c]
        Lp = max(ts) - min(ts)
        Wp = max(vs) - min(vs)
        aspect = Lp / max(1.0, Wp)          # 沿轴长 / 垂直宽
        # 点：面积小 + 两个方向都不宽（撇的 W 达 296，不能当点）
        if (MIN_AREA <= A <= MAX_DOT_AREA and aspect < 6
                and Wp <= 150 and Lp <= 450):
            out.append(rebuild_dot(c))
            n_dot += 1
        elif a.diag and aspect >= a.diag_min_aspect and 30 <= Wp <= 200:
            out.append(barify(c, taper=a.taper))
            n_bar += 1
        else:
            out.append(list(c))
    to_svg(out, a.out, a.size)
    print(f"saved {a.out}  点 {n_dot} 个  斜笔 {n_bar} 条  其余 {len(cs)-n_dot-n_bar} 条未动")


if __name__ == "__main__":
    main()
