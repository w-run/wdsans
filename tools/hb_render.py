"""字形渲染：调用 HarfBuzz 官方 hb-view（Cairo 光栅化）。

为什么不用浏览器：@font-face 一旦加载失败（子集缺字、路径错误），
浏览器会**静默回退到系统字体**，四列字全变成 PingFang 而且看不出来。
hb-view 直接读字体文件，不存在回退。

关键：用 --font-extents=880,-120 把所有字体强制到同一套 ascent/descent，
基线与 em 框完全对齐，可以逐像素比较。

用法：
    python3 hb_render.py --out out.png --glyph 永 --size 700 \
        --fonts "key=标签=路径,key=标签=路径"
"""
import argparse
import os
import subprocess

from PIL import Image, ImageDraw


def render(font_path, glyph, size, out):
    cmd = ["hb-view", font_path, glyph,
           f"--font-size={size}",
           "--font-extents=880,-120",
           "--margin=0",
           "--background=FFFFFF",
           "--foreground=000000",
           f"--output-file={out}"]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return Image.open(out).convert("L")


def ink_stats(im):
    import numpy as np
    a = np.array(im)
    ys, xs = (a < 128).nonzero()
    if len(xs) == 0:
        return None
    return dict(ratio=round(float((a < 128).mean()), 4),
                bbox=(int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--glyph", required=True)
    ap.add_argument("--size", type=int, default=700)
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--tmpdir", default="/tmp/p0/hb")
    a = ap.parse_args()

    os.makedirs(a.tmpdir, exist_ok=True)
    fonts = [tuple(x.split("=", 2)) for x in a.fonts.split(",")]
    imgs = []
    for key, label, path in fonts:
        im = render(path, a.glyph, a.size, os.path.join(a.tmpdir, f"{key}.png"))
        imgs.append((label, im))
        print(f"  {label:10} {im.size} {ink_stats(im)}", flush=True)

    W = max(i.width for _, i in imgs)
    H = max(i.height for _, i in imgs)
    pad, lab = 8, 24
    canvas = Image.new("L", ((W + pad) * len(imgs) + pad, H + pad * 2 + lab), 255)
    d = ImageDraw.Draw(canvas)
    for idx, (label, im) in enumerate(imgs):
        x = pad + idx * (W + pad)
        canvas.paste(im, (x, pad + lab))
        d.text((x, pad), label, fill=80)
    canvas.save(a.out)
    print("saved", a.out, canvas.size)


if __name__ == "__main__":
    main()
