"""把 transforms.py 的算子接到字库上，批量产出 NEW。

参数按测量目标给：
    竖笔 75 → 78        stroke.delta = +1.5（单边）
    出脚归零            feet
    斜笔末端收方        terminal
    点填充率 0.42-0.45  dot
    弯钩张力            hook

用法：
    python3 make_new.py --font ref/shs/shs-400.otf --glyphs 口国乙永 \
        --ops feet,terminal --outdir /tmp/new
"""
import argparse
import json
import os
import subprocess
import sys

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import transforms as T          # noqa: E402
from metrics import signed_area  # noqa: E402
from relayout import drop_bar, bar_bottom, bbox   # noqa: E402
from frame import X0, X1, Y_TOP, Y_BOT   # noqa: E402

PARAMS = {
    "feet": {"stroke_width": 78.0, "ratio": 1.0},
    "terminal": {"angle_hv": 0.0, "angle_diag": 4.0, "stroke_width": 78.0,
                 "width_norm": 1.0},
    "dot": {"stroke_width": 78.0, "ratio": 0.95},
    "hook": {"strength": 0.30},
    "soften": {"tension": 1.03},
    "stroke": {"delta": 1.5},
    "face": {"target_w": 880, "target_h": 880},
}


def recording_to_svg(value):
    d = []
    for op, args in value:
        pts = [(p[0], p[1]) for p in args]
        if op == "moveTo":
            d.append(f"M{pts[0][0]:.2f} {pts[0][1]:.2f}")
        elif op == "lineTo":
            d.append(f"L{pts[0][0]:.2f} {pts[0][1]:.2f}")
        elif op == "curveTo":
            d.append("C" + " ".join(f"{x:.2f} {y:.2f}" for x, y in pts))
        elif op == "qCurveTo":
            d.append("Q" + " ".join(f"{x:.2f} {y:.2f}" for x, y in pts))
        elif op in ("closePath", "endPath"):
            d.append("Z")
        elif op == "addComponent":
            pass
    return " ".join(d)


def _bez(p0, p1, p2, p3, n=8):
    out = []
    for i in range(1, n + 1):
        t = i / n
        mt = 1 - t
        out.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0]
                    + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                    mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1]
                    + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def to_contours(value, steps=8):
    """RecordingPen 值 → 展平轮廓。

    ⚠️ 曲线必须按三次贝塞尔采样，只取端点会把所有曲线拉成直线。
    """
    cs = []
    cur = []
    for op, args in value:
        if op == "moveTo":
            if len(cur) > 2:
                cs.append(cur)
            cur = [tuple(args[0])]
        elif op == "lineTo":
            cur.append(tuple(args[0]))
        elif op == "curveTo":
            p1, p2, p3 = (tuple(p) for p in args)
            if cur:
                cur.extend(_bez(cur[-1], p1, p2, p3, steps))
            else:
                cur.append(p3)
        elif op == "qCurveTo":
            p3 = tuple(args[-1])
            if cur:
                # 二次转三次
                c1 = ((cur[-1][0] + 2 * args[-2][0]) / 3,
                      (cur[-1][1] + 2 * args[-2][1]) / 3)
                c2 = ((p3[0] + 2 * args[-2][0]) / 3, (p3[1] + 2 * args[-2][1]) / 3)
                cur.extend(_bez(cur[-1], c1, c2, p3, steps))
            else:
                cur.append(p3)
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


def refill(cs, target_h=None, pct=96.0):
    """去出脚之后把底横下移，回到原高的 pct%。只对"底横托底"的包围结构生效。"""
    order = sorted(range(len(cs)), key=lambda i: -abs(signed_area(cs[i])))
    if len(order) < 2:
        return cs, 0.0
    x0, y0, x1, y1 = bbox(cs)
    h0 = y1 - y0
    target = target_h if target_h else h0 * pct / 100.0
    ybar = bar_bottom(cs)
    if ybar is None:
        return cs, 0.0
    # 底横必须离字底不远，否则不是"托底"结构
    if ybar - y0 > 160:
        return cs, 0.0
    # 当前高度（去出脚后）
    h1 = y1 - y0
    if h1 >= target - 1:
        return cs, 0.0
    delta = target - h1
    return drop_bar(cs, delta), delta


def svg_for(value, size=440):
    w, h = X1 - X0, Y_TOP - Y_BOT
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="{X0} {-Y_TOP} {w} {h}">'
            f'<rect x="{X0}" y="{-Y_TOP}" width="{w}" height="{h}" fill="white"/>'
            f'<g transform="scale(1,-1)"><path d="{recording_to_svg(value)}" '
            f'fill="#111" fill-rule="nonzero"/></g></svg>')


def render(value, path, size=440):
    with open(path + ".svg", "w") as f:
        f.write(svg_for(value, size))
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size),
                    "-o", path, path + ".svg"], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--glyphs", required=True)
    ap.add_argument("--ops", default="feet,terminal")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--size", type=int, default=440)
    ap.add_argument("--refill", action="store_true",
                    help="去出脚后把底横下移，保持原高 96%")
    a = ap.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    ops = [o.strip() for o in a.ops.split(",") if o.strip()]
    params = {k: PARAMS[k] for k in ops if k in PARAMS}
    unknown = [o for o in ops if o not in PARAMS]
    if unknown:
        print(f"未知算子（忽略）: {unknown}", file=sys.stderr)

    font = TTFont(a.font)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    done, missing = [], []
    for ch in a.glyphs:
        gn = cmap.get(ord(ch))
        if not gn:
            missing.append(ch)
            continue
        pen = RecordingPen()
        gs[gn].draw(pen)
        _pts = [p for op, args in pen.value for p in args]
        h_orig = (max(p[1] for p in _pts) - min(p[1] for p in _pts)) if _pts else 0
        try:
            v = T.apply_all(pen.value, params)
        except Exception as e:
            print(f"[失败] {ch}: {type(e).__name__} {e}", file=sys.stderr)
            continue
        moved = 0.0
        if a.refill:
            cs = to_contours(v)
            cs2, moved = refill(cs, h_orig * 0.96)
            if moved:
                v = [("moveTo", (c[0],)) for c in []] or v
                # 直接把多边形路径写进 SVG（不再回 recording）
                d = []
                for c in cs2:
                    if len(c) < 3:
                        continue
                    d.append(f"M{c[0][0]:.2f} {c[0][1]:.2f}")
                    for q in c[1:]:
                        d.append(f"L{q[0]:.2f} {q[1]:.2f}")
                    d.append("Z")
                w, h = X1 - X0, Y_TOP - Y_BOT
                svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{a.size}" '
                       f'height="{a.size}" viewBox="{X0} {-Y_TOP} {w} {h}">'
                       f'<rect x="{X0}" y="{-Y_TOP}" width="{w}" height="{h}" fill="white"/>'
                       f'<g transform="scale(1,-1)"><path d="{" ".join(d)}" fill="#111" '
                       f'fill-rule="nonzero"/></g></svg>')
                out = os.path.join(a.outdir, f"{ch}.png")
                with open(out + ".svg", "w") as f:
                    f.write(svg)
                subprocess.run(["rsvg-convert", "-w", str(a.size), "-h", str(a.size),
                                "-o", out, out + ".svg"], check=True)
                done.append((ch, round(moved)))
                continue
        out = os.path.join(a.outdir, f"{ch}.png")
        render(v, out, a.size)
        done.append((ch, 0))
    font.close()
    json.dump({"done": done, "missing": missing, "ops": ops},
              open(os.path.join(a.outdir, "manifest.json"), "w"),
              ensure_ascii=False, indent=1)
    refilled = sum(1 for _, m in done if m)
    print(f"完成 {len(done)} 字 → {a.outdir}   回填 {refilled} 字   "
          f"缺字 {len(missing)}   算子 {ops}")


if __name__ == "__main__":
    main()
