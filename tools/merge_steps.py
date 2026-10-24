"""永：按原始曲线逐项修改并输出对照。只用于验证，不覆盖字体。"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import vector_ops as V

TIP_PIE = (94.0, -17.0)
TIP_NA = (965.0, 50.0)


def dot_index(contours):
    candidates = []
    for i, c in enumerate(contours):
        pts = V.endpoints(c)
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if min(ys) > 600 and 150 < w < 500 and h < 300:
            candidates.append((max(w, h), i))
    if not candidates:
        raise ValueError("点未找到")
    return min(candidates)[1]


def use_reference_dot(base, reference):
    out = [list(c) for c in base]
    out[dot_index(base)] = reference[dot_index(reference)]
    return out


def shoulder(contour):
    out = []
    for op, args in contour:
        if op == "curveTo" and tuple(args[-1]) == (390.0, 421.0):
            # 原曲线仍到肩部下沿，随后补竖直边到顶边。
            c1, c2, _ = args
            out.append(("curveTo", (c1, c2, (390.0, 368.0))))
            out.append(("lineTo", ((390.0, 440.0),)))
        elif op == "lineTo" and tuple(args[0]) == (341.0, 443.0):
            # 顶边共线冗余点，删掉，避免留下小台阶。
            continue
        else:
            out.append((op, args))
    return out


def flatten_only_face(contour, tip):
    return [("lineTo", (tip,)) if op == "curveTo" and tuple(args[-1]) == tip
            else (op, args) for op, args in contour]


def variants(base, reference):
    a = use_reference_dot(base, reference)
    b = [shoulder(c) if i == 1 else list(c) for i, c in enumerate(a)]
    c = [flatten_only_face(c, TIP_PIE if i == 1 else TIP_NA)
         if i in (1, 2) else list(c) for i, c in enumerate(b)]
    return {"SHS": base, "NEW-dot": a, "NEW-dot+shoulder": b,
            "NEW-all-three": c, "OPPO": reference}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/merge_steps.png")
    args = ap.parse_args()
    base = V.read_glyph("ref/shs/shs-400.otf", "永")
    ref = V.read_glyph("ref/ops/ops-400.ttf", "永")
    vs = variants(base, ref)
    from PIL import Image, ImageDraw, ImageFont
    files = []
    for label, contours in vs.items():
        path = f"/tmp/step_{label.replace('+','_')}.svg"
        with open(path, "w") as f:
            f.write(V.svg(contours, V.FRAME, 560))
        subprocess.run(["rsvg-convert", "-o", path + ".png", path], check=True)
        files.append((label, path + ".png"))
    ims = [(lab, Image.open(p).convert("RGB")) for lab, p in files]
    bar = 34
    gap = 8
    W = sum(im.width for _, im in ims) + gap * (len(ims) - 1)
    H = ims[0][1].height + bar
    canvas = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(canvas)
    font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 17)
    x = 0
    for label, im in ims:
        d.text((x + 5, 8), label, fill="#333", font=font)
        canvas.paste(im, (x, bar))
        d.rectangle((x, bar, x + im.width - 1, bar + im.height - 1), outline="#9db3cc")
        x += im.width + gap
    canvas.save(args.out)
    print(args.out)


if __name__ == "__main__":
    main()
