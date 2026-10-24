"""去针尖：把笔画末端的两条曲线用一段直线端面连接。

背景（按字体原始曲线核对，非推测）：
- OPPO 的撇末段曲线终点是 (84,-43)，闭合回起点 (34,11)，
  两者之间天然是一条直线端面，长 73.6、方向 -47°
- SHS 的撇在 (35,40) 有一个曲线中间点，两侧曲线在它会合，
  形成一根针尖，没有端面

做法：只动尖端附近的曲线，中间补一条直线；其余原始曲线逐字保留。
支持 CFF 三次与 TrueType 二次曲线。
"""
import math


def segments(contour):
    segs = []
    for op, args in contour:
        if op == "moveTo":
            start = args[0]
        elif op in ("lineTo", "curveTo", "qCurveTo"):
            segs.append({"op": op, "args": args, "start": start, "end": args[-1]})
            start = args[-1]
    return segs


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def split_cubic(s, t):
    p0 = s["start"]
    c1, c2, p3 = s["args"]
    a01, a12, a23 = lerp(p0, c1, t), lerp(c1, c2, t), lerp(c2, p3, t)
    a012, a123 = lerp(a01, a12, t), lerp(a12, a23, t)
    m = lerp(a012, a123, t)
    return (p0, a01, a012, m), (m, a123, a23, p3)


def split_quad(s, t):
    p0 = s["start"]
    c, p3 = s["args"]
    a01, a12 = lerp(p0, c, t), lerp(c, p3, t)
    m = lerp(a01, a12, t)
    return (p0, a01, m), (m, a12, p3)


def head_seg(s, t):
    if s["op"] == "curveTo":
        h, _ = split_cubic(s, t)
        return ("curveTo", h[1:4]), h[3]
    if s["op"] == "qCurveTo":
        h, _ = split_quad(s, t)
        return ("qCurveTo", h[1:3]), h[2]
    return ("lineTo", (s["end"],)), s["end"]


def tail_seg(s, t):
    if s["op"] == "curveTo":
        _, tl = split_cubic(s, t)
        return ("curveTo", tl[1:4]), tl[0]
    if s["op"] == "qCurveTo":
        _, tl = split_quad(s, t)
        return ("qCurveTo", tl[1:3]), tl[0]
    return ("lineTo", (s["start"],)), s["start"]


def deblunt(contour, tip, cut_in=0.80, cut_out=0.80):
    """把尖端两侧曲线截断并用直线端面连接。

    cut_in  进入段从起点保留的比例
    cut_out 离开段从终点倒推保留的比例
    返回 (新轮廓, A, B)
    """
    segs = segments(contour)
    k = next((i for i, s in enumerate(segs) if tuple(s["end"]) == tuple(tip)), None)
    if k is None:
        return list(contour), None, None
    pre, post = segs[k], segs[(k + 1) % len(segs)]
    hop, A = head_seg(pre, cut_in)
    top, B = tail_seg(post, 1 - cut_out)

    out = [("moveTo", (segs[0]["start"],))]
    for i, s in enumerate(segs):
        if i < k:
            out.append((s["op"], s["args"]))
        elif i == k:
            out.append(hop)
            out.append(("lineTo", (B,)))
            out.append(top)
        elif i == (k + 1) % len(segs):
            pass
        else:
            out.append((s["op"], s["args"]))
    out.append(("closePath", ()))
    return out, A, B


if __name__ == "__main__":
    import subprocess
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    import vector_ops as V

    base = V.read_glyph("ref/shs/shs-400.otf", "永")
    for cut in (0.78, 0.82, 0.86):
        pie, A, B = deblunt(base[1], (35.0, 40.0), cut, cut)
        na, C, D = deblunt(base[2], (965.0, 50.0), cut, cut)
        new = [base[0], pie, na]
        path = f"/tmp/dbn_{int(cut*100)}.svg"
        with open(path, "w") as f:
            f.write(V.svg(new, V.FRAME, 600))
        subprocess.run(["rsvg-convert", "-o", path + ".png", path], check=True)
        print(cut, "pie", tuple(round(v, 1) for v in A), tuple(round(v, 1) for v in B),
              "na", tuple(round(v, 1) for v in C), tuple(round(v, 1) for v in D))
