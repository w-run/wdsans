"""永 · NEW 版定稿（三项修改，按字体原始曲线核对得出）。

三项：
1. 点     整体采用 OPPO 参考轮廓（原始曲线、原坐标，不缩放不平移）
2. 肩部   撇顶端补竖直右缘 (390,368→440)，并删掉顶边共线冗余点 (341,443)
3. 末端   撇、捺的"针尖段"改成直线端面

第 3 项的依据（读三家原始曲线的分段表得到，不是推测）：
    SHS  撇  (35,40)→(94,-17)   curve  ← 针尖
    HOS  撇  (94,-17)→(33,51)    line   ← 端面
    OPPO 撇  (84,-43)→(34,11)    line   ← 端面
    SHS  捺  (912,-15)→(965,50)  curve  ← 针尖
    OPPO 捺  (965,26)→(921,-36)   line   ← 端面

只改这两段曲线为直线，端点位置不变，其余原始曲线逐字保留。
"""
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import vector_ops as V
from deblunt import segments

PIE_FACE = ((35.0, 40.0), (94.0, -17.0))
NA_FACE = ((912.0, -15.0), (965.0, 50.0))


def dot_index(contours):
    cands = []
    for i, c in enumerate(contours):
        pts = V.endpoints(c)
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if min(ys) > 600 and 150 < w < 500 and h < 300:
            cands.append((max(w, h), i))
    if not cands:
        raise ValueError("点未找到")
    return min(cands)[1]


def straighten(contour, start, end):
    """把 (start→end) 这一段曲线改成直线，端点不变。"""
    segs = segments(contour)
    k = next((i for i, s in enumerate(segs)
              if tuple(s["start"]) == tuple(start) and tuple(s["end"]) == tuple(end)), None)
    if k is None:
        return list(contour), False
    out = [("moveTo", (segs[0]["start"],))]
    for i, s in enumerate(segs):
        if i == k:
            out.append(("lineTo", (end,)))
        else:
            out.append((s["op"], s["args"]))
    out.append(("closePath", ()))
    return out, True


def shoulder(contour):
    out = []
    for op, args in contour:
        if op == "curveTo" and tuple(args[-1]) == (390.0, 421.0):
            c1, c2, _ = args
            out.append(("curveTo", (c1, c2, (390.0, 368.0))))
            out.append(("lineTo", ((390.0, 440.0),)))
        elif op == "lineTo" and tuple(args[0]) == (341.0, 443.0):
            continue
        else:
            out.append((op, args))
    return out


def build(base, reference):
    out = [list(c) for c in base]
    out[dot_index(out)] = reference[dot_index(reference)]
    out[1] = shoulder(out[1])
    out[1], ok_pie = straighten(out[1], *PIE_FACE)
    out[2], ok_na = straighten(out[2], *NA_FACE)
    return out, {"pie_face_line": ok_pie, "na_face_line": ok_na}


def verify(base, new, reference):
    """数值验收：与参考对比关键量。"""
    def na_width(cs, x):
        from detail import scan_runs
        poly = []
        for c in cs:
            pts = []
            for op, args in c:
                if op == "moveTo":
                    pts = [tuple(args[0])]
                elif op in ("lineTo", "curveTo", "qCurveTo"):
                    pts.append(tuple(args[-1]))
                elif op == "closePath":
                    if pts:
                        poly.append(pts + [pts[0]])
                    pts = []
        runs = scan_runs(poly, x, "v")
        if not runs:
            return None
        a, b = max(runs, key=lambda r: r[0])
        return round(b - a)

    def face_len(contour, start, end):
        segs = segments(contour)
        for s in segs:
            if tuple(s["start"]) == tuple(start) and tuple(s["end"]) == tuple(end):
                return round(math.dist(start, end), 1), s["op"]
        return None, None

    info = {}
    for tag, cs in (("SHS", base), ("NEW", new), ("OPPO", reference)):
        L, op = face_len(cs[1], *PIE_FACE)
        info[tag] = {"pie_face": L, "pie_op": op,
                     "na_x900": na_width(cs, 900),
                     "na_x930": na_width(cs, 930)}
    return info


def main():
    base = V.read_glyph("ref/shs/shs-400.otf", "永")
    ref = V.read_glyph("ref/ops/ops-400.ttf", "永")
    new, flags = build(base, ref)
    print("改动：", flags)
    for k, v in verify(base, new, ref).items():
        print(" ", k, v)
    for name, contours in (("shs", base), ("new", new), ("oppo", ref)):
        for suffix, box, w in (("whole", V.FRAME, 620),
                               ("pie", (0.0, 470.0, 440.0, -130.0), 560),
                               ("na", (700.0, 160.0, 1000.0, -100.0), 620)):
            path = f"/tmp/newv_{name}_{suffix}.svg"
            with open(path, "w") as f:
                f.write(V.svg(contours, box, w))
            subprocess.run(["rsvg-convert", "-o", path + ".png", path], check=True)
    from PIL import Image, ImageDraw, ImageFont
    for suffix, w in (("whole", 420), ("pie", 360), ("na", 360)):
        ims = [(lab, Image.open(f"/tmp/newv_{key}_{suffix}.svg.png").convert("RGB").resize((w, w)))
               for key, lab in (("shs", "SHS"), ("new", "NEW"), ("oppo", "OPPO"))]
        W = sum(i.width for _, i in ims) + 8 * (len(ims) - 1)
        canvas = Image.new("RGB", (W, w + 30), "white")
        d = ImageDraw.Draw(canvas)
        f = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 16)
        x = 0
        for lab, im in ims:
            d.text((x + 4, 6), lab, fill="#333", font=f)
            canvas.paste(im, (x, 30))
            x += im.width + 8
        canvas.save(f"/tmp/newv_row_{suffix}.png")
    print("ok")


if __name__ == "__main__":
    main()
