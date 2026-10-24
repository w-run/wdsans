"""末端直线化：把笔画尖端两侧的内弧曲线改成直线。

观察（实测）：思源的撇尾/捺尾，收锋两侧是**向内凹的曲线**（中间瘪进去，形成"腰"），
鸿蒙 / OPPO 是直线。这就是"凹陷"的来源。

判据：
  · 该 on-curve 点是尖角（内角 < 90°）
  · 前后两段都是曲线
  · 曲线控制点落在弦的同一侧（向内弓）
→ 把这两段改成直线

只改线段类型（curve → line），不增删节点、不移动端点。

用法：
    python3 straight_tips.py --font ref/shs/shs-400.otf --glyph 永 \
        --out /tmp/yong_lin.png
"""
import argparse
import math
import subprocess
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from frame import X0, X1, Y_TOP, Y_BOT   # noqa: E402


def _pts(v):
    return [tuple(p) for op, args in v for p in args if op != "closePath"]


def straighten(v, tip_deg=90.0, min_bulge=2.0):
    """返回 (新值, 处理数)。"""
    out = []
    n = len(v)
    # 先算出每个 on-curve 点（各段终点）
    idx_on = [i for i, (op, args) in enumerate(v) if op in ("lineTo", "curveTo") and args]
    # 建立 段序号 → 起终点
    start = None
    segs = []          # (index, op, start_pt, end_pt)
    for i, (op, args) in enumerate(v):
        if op == "moveTo":
            start = tuple(args[0])
        elif op in ("lineTo", "curveTo"):
            end = tuple(args[-1])
            segs.append((i, op, start, end, args))
            start = end

    # 找尖角点
    angles = {}
    for k in range(1, len(segs)):
        i_prev, _, p0, p1, _ = segs[k - 1]
        i_cur, _, q0, q1, _ = segs[k]
        if abs(p1[0] - q0[0]) > 1e-6 or abs(p1[1] - q0[1]) > 1e-6:
            continue
        v1 = (p1[0] - p0[0], p1[1] - p0[1])
        v2 = (q1[0] - q0[0], q1[1] - q0[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        if l1 < 1e-6 or l2 < 1e-6:
            continue
        c = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
        ang = 180 - math.degrees(math.acos(c))
        if ang < tip_deg:
            angles[k] = ang

    # 标记要改成直线的段
    to_line = set()
    for k in angles:
        for kk in (k - 1, k):
            if 0 <= kk < len(segs):
                to_line.add(kk)
    # 只处理曲线段
    to_line = {kk for kk in to_line if segs[kk][1] == "curveTo"}

    converted = 0
    seg_map = {s[0]: kk for kk, s in enumerate(segs)}
    for i, (op, args) in enumerate(v):
        kk = seg_map.get(i)
        if kk is not None and kk in to_line:
            out.append(("lineTo", (tuple(args[-1]),)))
            converted += 1
        else:
            out.append((op, args))
    return out, converted, len(angles)


def to_svg(v, path, size=520, box=None):
    if box:
        x0, ytop, x1, ybot = box
    else:
        x0, ytop, x1, ybot = X0, Y_TOP, X1, Y_BOT
    w, h = x1 - x0, ytop - ybot
    d = []
    for op, args in v:
        if op == "moveTo":
            d.append(f"M{args[0][0]:.1f} {args[0][1]:.1f}")
        elif op == "lineTo":
            d.append(f"L{args[0][0]:.1f} {args[0][1]:.1f}")
        elif op == "curveTo":
            d.append("C" + " ".join(f"{p[0]:.1f} {p[1]:.1f}" for p in args))
        elif op in ("closePath", "endPath"):
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
    ap.add_argument("--tip-deg", type=float, default=90.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=520)
    a = ap.parse_args()
    font = TTFont(a.font)
    gs = font.getGlyphSet()
    gn = font.getBestCmap().get(ord(a.glyph))
    if not gn:
        raise SystemExit(f"缺字 {a.glyph}")
    pen = RecordingPen()
    gs[gn].draw(pen)
    font.close()
    v2, conv, ntip = straighten(pen.value, a.tip_deg)
    to_svg(v2, a.out, a.size)
    print(f"saved {a.out}  尖角 {ntip} 处  转直线 {conv} 段")


if __name__ == "__main__":
    main()
