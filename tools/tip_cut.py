"""只截短笔画末端，不重画主体。

算法：
1. 找到轮廓上指定尖端 T 的索引 k。
2. 沿两侧边缘分别向前回退弧长 cut，得到 A、B。
3. 用 A→B 的直线端面替换 T 和两侧被截掉的尾段。
4. A 前、B 后的原始曲线段逐字保留。

支持 CFF 三次、TrueType 二次曲线。末端仍在原曲线上，切线方向保持一致。
"""
import math
import subprocess
import sys
import vector_ops as V


def split_segments(contour):
    segments = []
    start = None
    for op, args in contour:
        if op == "moveTo":
            start = tuple(args[0])
        elif op in ("lineTo", "curveTo", "qCurveTo"):
            end = tuple(args[-1])
            segments.append({"op": op, "args": args, "start": start, "end": end})
            start = end
    return segments


def point(seg, t):
    if seg["op"] == "lineTo":
        a, b = seg["start"], seg["end"]
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    if seg["op"] == "qCurveTo":
        a, c, b = seg["start"], seg["args"][0], seg["args"][1]
        u = 1 - t
        return (u * u * a[0] + 2 * u * t * c[0] + t * t * b[0],
                u * u * a[1] + 2 * u * t * c[1] + t * t * b[1])
    a, c1, c2, b = seg["start"], *seg["args"]
    u = 1 - t
    return (u ** 3 * a[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * b[0],
            u ** 3 * a[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * b[1])


def split(seg, t):
    """De Casteljau 分割，返回 (前段, 后段)。"""
    if seg["op"] == "lineTo":
        mid = point(seg, t)
        return ({"op": "lineTo", "args": (mid,), "start": seg["start"], "end": mid},
                {"op": "lineTo", "args": (seg["end"],), "start": mid, "end": seg["end"]})
    a, b = seg["start"], seg["end"]
    if seg["op"] == "qCurveTo":
        c = seg["args"][0]
        p01 = lerp(a, c, t)
        p12 = lerp(c, b, t)
        p = lerp(p01, p12, t)
        return ({"op": "qCurveTo", "args": (p01, p), "start": a, "end": p},
                {"op": "qCurveTo", "args": (p12, b), "start": p, "end": b})
    c1, c2, _ = seg["args"]
    p01, p12, p23 = lerp(a, c1, t), lerp(c1, c2, t), lerp(c2, b, t)
    p012, p123 = lerp(p01, p12, t), lerp(p12, p23, t)
    p = lerp(p012, p123, t)
    return ({"op": "curveTo", "args": (p01, p012, p), "start": a, "end": p},
            {"op": "curveTo", "args": (p123, p23, b), "start": p, "end": b})


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def length(seg, n=160):
    last = point(seg, 0.0)
    total = 0.0
    for i in range(1, n + 1):
        p = point(seg, i / n)
        total += math.dist(last, p)
        last = p
    return total


def backward(segments, k, distance):
    """从段 k 的末端向前退 distance，返回 (段索引, t, 点)。"""
    left = distance
    j = k
    while left > 0:
        seg = segments[j]
        L = length(seg)
        if left <= L:
            # 目标参数满足：从段起点到切点的弧长 = 整段长 - 回退量。
            target = L - left
            lo, hi = 0.0, 1.0
            for _ in range(28):
                mid = (lo + hi) / 2
                if length({**seg, "end": point(seg, mid), "args": args_prefix(seg, mid)}) > target:
                    hi = mid
                else:
                    lo = mid
            t = (lo + hi) / 2
            return j, t, point(seg, t)
        left -= L
        j = (j - 1) % len(segments)
    raise ValueError("回退距离超过轮廓")


def args_prefix(seg, t):
    if seg["op"] == "lineTo":
        return (point(seg, t),)
    if seg["op"] == "qCurveTo":
        a, c, b = seg["start"], seg["args"][0], seg["end"]
        p01 = lerp(a, c, t)
        p12 = lerp(c, b, t)
        return (p01, point(seg, t))
    a, c1, c2, b = seg["start"], *seg["args"]
    p01, p12, p23 = lerp(a, c1, t), lerp(c1, c2, t), lerp(c2, b, t)
    p012 = lerp(p01, p12, t)
    return (p01, p012, point(seg, t))


def cut_tip(contour, tip, cut=30.0):
    segs = split_segments(contour)
    k = next(i for i, s in enumerate(segs)
             if math.dist(s["end"], tip) < 0.01)
    # k 是进入尖端的段，j 是离开尖端的段。
    # 两侧都从各自段的起点（即尖端）向后退，不能跨过尖端。
    j = (k + 1) % len(segs)
    # 进入侧：tip = k.end，切点在本段末端前 cut。
    # 离开侧：tip = j.start，切点在本段起点后 cut；绝不能跨过 tip。
    def at_length(seg, target):
        total = length(seg)
        target = max(0.0, min(total, target))
        lo, hi = 0.0, 1.0
        for _ in range(28):
            mid = (lo + hi) / 2
            if length({**seg, "end": point(seg, mid), "args": args_prefix(seg, mid)}) > target:
                hi = mid
            else:
                lo = mid
        t = (lo + hi) / 2
        return t, point(seg, t)

    ak = k
    at, A = at_length(segs[k], length(segs[k]) - cut)
    bk = j
    bt, B = at_length(segs[j], cut)
    # 两侧可以落在不同曲线段，分别截断后补直线端面。
    left = split(segs[ak], at)[0]
    right = split(segs[bk], bt)[1]
    out = [("moveTo", (segs[0]["start"],))]
    for s in segs[:ak]:
        out.append((s["op"], s["args"]))
    out.append((left["op"], left["args"]))
    out.append(("lineTo", (B,)))
    # B 位于另一侧段内，先保留该段的后半，再追加后续原始段。
    out.append((right["op"], right["args"]))
    for s in segs[bk + 1:]:
        out.append((s["op"], s["args"]))
    out.append(("closePath", ()))
    return out, {"A": A, "B": B, "segments": (ak, bk)}


if __name__ == "__main__":
    cs = V.read_glyph("ref/shs/shs-400.otf", "永")
    for cut in (20, 35):
        changed, info = cut_tip(cs[2], (965.0, 50.0), cut)
        new = [cs[0], cs[1], changed]
        path = f"/tmp/na_cut{cut}.svg"
        with open(path, "w") as f:
            f.write(V.svg(new, (700.0, 160.0, 1000.0, -100.0), 600))
        subprocess.run(["rsvg-convert", "-o", path + ".png", path], check=True)
        print(cut, info)
