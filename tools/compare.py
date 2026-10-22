"""并排/上下对比样张。

用法：
    python3 compare.py out.png --a 原版.otf --b 新版.otf --text "永国回圖" --weights 400 --cols 4
"""
import argparse
import sys

sys.path.insert(0, "/var/minis/shared/projects/wdsans/tools")

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import RecordingPen

from raster import flatten, rasterize, compose


def load(font_path, wght, text):
    font = TTFont(font_path)
    if "fvar" in font and wght is not None:
        font = instantiateVariableFont(font, {"wght": wght}, inplace=False)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    out = []
    for ch in text:
        gn = cmap.get(ord(ch))
        if not gn:
            out.append((None, False)); continue
        pen = RecordingPen()
        gs[gn].draw(pen)
        out.append((flatten(pen.value), True))
    font.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--a", required=True, help="参考字体")
    ap.add_argument("--b", required=True, help="试验字体")
    ap.add_argument("--text", default="永国回圖田")
    ap.add_argument("--weights", default="400")
    ap.add_argument("--size", type=int, default=150)
    ap.add_argument("--cols", type=int, default=4)
    args = ap.parse_args()

    weights = [float(w) for w in args.weights.split(",")]
    rows = []
    for w in weights:
        A = load(args.a, w, args.text)
        B = load(args.b, w, args.text)
        for start in range(0, len(args.text), args.cols):
            chunkA = A[start:start + args.cols]
            chunkB = B[start:start + args.cols]
            rows.append([(rasterize(c, args.size) if ok else None, ok) for c, ok in chunkA])
            rows.append([(rasterize(c, args.size) if ok else None, ok) for c, ok in chunkB])

    img = compose(rows, args.size)
    img.save(args.out)
    print("saved", args.out, img.size, "| 每个字对：上=参考 下=试验")


if __name__ == "__main__":
    main()
