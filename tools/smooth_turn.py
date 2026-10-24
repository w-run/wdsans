"""局部平滑：只把指定区域内的轮廓做圆，其余原样保留。

为什么不全字重画：全字重画会丢掉端子形状、直角、笔宽变化，出来的东西不是这个字了。
真正常用的做法是"只动要动的那一段"——转折处平滑，其余一个点都不碰。

做法：
  1. 给定区域（em 坐标框），找出每条轮廓落在区域内的**连续点段**
  2. 对这些点段做 Chaikin 角切割（端点固定，不会移位）
  3. 段外点原样保留

效果：转折的曲率变连续，端子与直角完全不变。

用法：
    python3 smooth_turn.py --font ref/shs/shs-400.otf --glyph 乙 \
        --region 40,-60,420,300 --iters 2 --out /tmp/s.png
"""
import argparse
import subprocess
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen        # noqa: E402
from frame import X0, X1, Y_TOP, Y_BOT   # noqa: E402


def in_box(p, box):
    x0, y0, x1, y1 = box
    return x0 <= p[0] <= x1 and y0 <= p[1] <= y1


def runs_in_box(pts, box):
    """返回落在 box 内的连续点段的 (start, end) 索引（闭区间）。"""
    n = len(pts) - 1 if pts[0] == pts[-1] else len(pts)
    flags = [in_box(pts[i], box) for i in range(n)]
    if all(flags):
        return [(0, n - 1)]
    if not any(flags):
        return []
    # 找断点
    start = None
    runs = []
    for i in range(n):
        if flags[i] and start is None:
            start = i
        elif not flags[i] and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, n - 1))
    return runs


def window_smooth(pts, half):
    """对一段折线做窗口移动平均。点密集时 Chaikin 无效，必须按弧长窗口来。
    端点用一半权重渐入，避免接缝处跳变。"""
    n = len(pts)
    if n < 3 or half < 1:
        return list(pts)
    out = []
    for i in range(n):
        wsum = 0.0
        ax = ay = 0.0
        for k in range(-half, half + 1):
            j = i + k
            if j < 0 or j >= n:
                continue
            # 端点渐入：离边界越近权重越小
            edge = min(j, n - 1 - j)
            w = min(1.0, (edge + 1) / (half + 1.0))
            wsum += w
            ax += pts[j][0] * w
            ay += pts[j][1] * w
        out.append((ax / wsum, ay / wsum))
    # 端点强制不动
    out[0] = pts[0]
    out[-1] = pts[-1]
    return out


def chaikin_run(pts, iters=2):
    """对一段折线做 Chaikin，端点固定。"""
    seg = list(pts)
    for _ in range(iters):
        if len(seg) < 3:
            break
        nxt = [seg[0]]
        for i in range(len(seg) - 1):
            p, q = seg[i], seg[i + 1]
            nxt.append((0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]))
            nxt.append((0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1]))
        nxt.append(seg[-1])
        seg = nxt
    return seg


def smooth(cs, box, iters=2, half=18):
    out = []
    touched = 0
    for c in cs:
        closed = c[0] == c[-1]
        pts = c[:-1] if closed else c
        n = len(pts)
        runs = runs_in_box(pts, box)
        if not runs:
            out.append(list(c))
            continue
        # 从段外开始重建，保证顺序
        new = []
        idx_set = {}
        for (a, b) in runs:
            idx_set[a] = b
        i = 0
        while i < n:
            if i in idx_set:
                b = idx_set[i]
                # 两端各多借 half 个点做上下文（**不能用 % 回绕**，
                # 闭合轮廓回绕会跨到笔道另一侧，把点拽过去）
                lo = max(0, i - half)
                hi = min(n - 1, b + half)
                pre = i - lo
                seg = [pts[k] for k in range(lo, hi + 1)]
                sm = window_smooth(seg, half)
                new.extend(sm[pre:pre + (b - i + 1)])
                touched += 1
                i = b + 1
            else:
                new.append(pts[i])
                i += 1
        if closed:
            new.append(new[0])
        out.append(new)
    return out, touched


def to_svg(cs, path, size=440):
    w, h = X1 - X0, Y_TOP - Y_BOT
    d = []
    for c in cs:
        if len(c) < 3:
            continue
        d.append(f"M{c[0][0]:.1f} {c[0][1]:.1f}")
        for p in c[1:]:
            d.append(f"L{p[0]:.1f} {p[1]:.1f}")
        d.append("Z")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
           f'viewBox="{X0} {-Y_TOP} {w} {h}">'
           f'<rect x="{X0}" y="{-Y_TOP}" width="{w}" height="{h}" fill="white"/>'
           f'<g transform="scale(1,-1)"><path d="{" ".join(d)}" fill="#111" '
           f'fill-rule="nonzero"/></g></svg>')
    with open(path + ".svg", "w") as f:
        f.write(svg)
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size),
                    "-o", path, path + ".svg"], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--glyph", required=True)
    ap.add_argument("--region", required=True, help="x0,y0,x1,y1（em 坐标）")
    ap.add_argument("--iters", type=int, default=2)
    ap.add_argument("--window", type=int, default=18,
                    help="平滑窗口半宽（点数）；点很密，取 15-25 才看得出效果")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=440)
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
    new, touched = smooth(cs, box, a.iters, a.window)
    to_svg(new, a.out, a.size)
    print(f"saved {a.out}  平滑 {touched} 段  区域 {box}")


if __name__ == "__main__":
    main()
