"""原始矢量算子（新实现）。

不经过像素骨架，也不把曲线展平成多边形。所有修改都发生在原始曲线段上；
未明确修改的曲线段逐字保留。

SVG 与字体坐标都使用 y 向上；只在 SVG 最外层做一次 scale(1,-1)。
"""
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
import math

FRAME = (-20.0, 900.0, 1020.0, -140.0)  # x0, y_top, x1, y_bottom


class AllSegmentsPen(RecordingPen):
    """把多控制点的 qCurveTo 展开成独立的二次曲线，避免漏画后半段。"""
    def qCurveTo(self, *points):
        # TrueType 允许多个 off-curve 控制点，fontTools 的 qCurveTo 可能
        # 在最后一个 off-curve 处无明确 on-curve 终点；按规则插入中点。
        if len(points) < 2:
            return
        current = self.value[-1][1][-1] if self.value and self.value[-1][0] != 'moveTo' else self.value[-1][1][0]
        # 从上一个点的坐标开始，顺序展开每两个控制点之间的中点。
        for i in range(len(points) - 2):
            c = points[i]
            nxt = points[i + 1]
            mid = ((c[0] + nxt[0]) / 2, (c[1] + nxt[1]) / 2)
            self.value.append(('qCurveTo', (c, mid)))
        self.value.append(('qCurveTo', points[-2:]))


def read_glyph(path, ch):
    font = TTFont(path)
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord(ch)]
    pen = AllSegmentsPen()
    gs[name].draw(pen)
    font.close()
    contours, current = [], []
    for op, args in pen.value:
        if op == "moveTo":
            if current:
                contours.append(current)
            current = [(op, args)]
        elif op in ("lineTo", "curveTo", "qCurveTo"):
            current.append((op, args))
        elif op in ("closePath", "endPath"):
            current.append(("closePath", ()))
            contours.append(current)
            current = []
    if current:
        contours.append(current)
    return contours


def path_data(contours):
    out = []
    for contour in contours:
        for op, args in contour:
            if op == "moveTo":
                out.append("M" + xy(args[0]))
            elif op == "lineTo":
                out.append("L" + xy(args[0]))
            elif op == "curveTo":
                out.append("C" + " ".join(xy(p) for p in args))
            elif op == "qCurveTo":
                # 独立二次曲线必须写成 Q，不能像旧版那样丢掉。
                out.append("Q" + " ".join(xy(p) for p in args))
            elif op == "closePath":
                out.append("Z")
    return " ".join(out)


def xy(p):
    return f"{p[0]:.2f},{p[1]:.2f}"


def svg(contours, box=FRAME, width=640, fill="#111", extras=""):
    x0, yt, x1, yb = box
    w, h = x1 - x0, yt - yb
    height = round(width * h / w)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="{x0} {-yt} {w} {h}">'
            f'<rect x="{x0}" y="{-yt}" width="{w}" height="{h}" fill="white"/>'
            f'<g transform="scale(1,-1)">'
            f'<path d="{path_data(contours)}" fill="{fill}" fill-rule="nonzero"/>'
            f'{extras}</g></svg>')


def endpoints(contour):
    points = []
    start = None
    for op, args in contour:
        if op == "moveTo":
            start = tuple(args[0])
        elif op in ("lineTo", "curveTo", "qCurveTo"):
            if start is not None:
                points.append(start)
            start = tuple(args[-1])
    return points


def dot_index(contours):
    """只选择候选点笔画：短、面积小、不是长撇捺。索引供后续定位。"""
    candidates = []
    for i, c in enumerate(contours):
        pts = endpoints(c)
        if len(pts) < 3 or len(pts) > 8:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if w < 120 or h < 40 or w > 470 or h > 300:
            continue
        # 永的撇长达 700 多，不能用面积替代长度判据
        if max(w, h) / max(1, min(w, h)) < 4.2:
            candidates.append((max(w, h), i))
    return min(candidates)[1] if candidates else None


def dot_oppo():
    """OPPO 永的点的几何：斜端面 + 两条同向上拱的长边。

    坐标来自源字体轮廓，不使用轴长/宽度近似。
    二次曲线的控制点向 +y 偏移 14，曲线实际拱量为 7。
    """
    A = (340.0, 782.0)
    B = (364.0, 842.0)
    C = (673.0, 724.0)
    D = (646.0, 662.0)
    # A→B 是短端面，B→C 下长边，C→D 另一端面，D→A 上长边。
    lower_mid = ((B[0] + C[0]) / 2, (B[1] + C[1]) / 2 + 14)
    upper_mid = ((D[0] + A[0]) / 2, (D[1] + A[1]) / 2 + 14)
    # 二次转三次，CFF 也能直接写入
    def cubic(p, q, control):
        c1 = (p[0] + 2 * (control[0] - p[0]) / 3,
              p[1] + 2 * (control[1] - p[1]) / 3)
        c2 = (q[0] + 2 * (control[0] - q[0]) / 3,
              q[1] + 2 * (control[1] - q[1]) / 3)
        return c1, c2
    c1, c2 = cubic(B, C, lower_mid)
    c3, c4 = cubic(D, A, upper_mid)
    return [
        ("moveTo", (A,)),
        ("lineTo", (B,)),
        ("curveTo", (c1, c2, C)),
        ("lineTo", (D,)),
        ("curveTo", (c3, c4, A)),
        ("closePath", ()),
    ]


def replace_dot(contours):
    idx = dot_index(contours)
    if idx is None:
        raise ValueError("没有找到点笔画")
    result = list(contours)
    result[idx] = dot_oppo()
    return result, idx


def metrics(contour):
    pts = endpoints(contour)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return {"nodes": len(pts), "x": [min(xs), max(xs)], "y": [min(ys), max(ys)]}


if __name__ == "__main__":
    import argparse
    import subprocess
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", required=True)
    parser.add_argument("--glyph", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--dot", action="store_true", help="只重建点，其他曲线原样保留")
    args = parser.parse_args()
    cs = read_glyph(args.font, args.glyph)
    changed = None
    if args.dot:
        cs, changed = replace_dot(cs)
    text = svg(cs)
    with open(args.out, "w") as f:
        f.write(text)
    subprocess.run(["rsvg-convert", "-o", args.out + ".png", args.out], check=True)
    print(f"saved {args.out}.png  contours={len(cs)}  dot={changed}")
