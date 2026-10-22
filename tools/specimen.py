"""样张渲染 CLI（铁律：必须出图并实际看）。

用法：
    python3 specimen.py out.png "永国回圖田" --font a.otf --weights 250,400,900
    python3 specimen.py cmp.png --left a.otf --right b.otf --text "永国回" --weights 400
"""
import argparse
import sys

import numpy as np
from PIL import Image

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import RecordingPen

sys.path.insert(0, "/var/minis/shared/projects/wdsans/tools")
from raster import flatten, rasterize, compose


def load_contours(font_path, wght, text):
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


def grid(items, size):
    return compose([[r] for r in items], size)


def row(items, size):
    return [items]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--text", default="永国回圖田日目自且甲申由")
    ap.add_argument("--font", default="/tmp/p0/sub.otf")
    ap.add_argument("--left", default=None)
    ap.add_argument("--right", default=None)
    ap.add_argument("--weights", default="250,400,900")
    ap.add_argument("--size", type=int, default=130)
    args = ap.parse_args()

    weights = [float(w) for w in args.weights.split(",")]
    rows = []

    if args.left and args.right:
        for w in weights:
            L = load_contours(args.left, w, args.text)
            R = load_contours(args.right, w, args.text)
            merged = []
            for (lc, lok), (rc, rok) in zip(L, R):
                merged.append((rasterize(lc, args.size) if lok else None, lok))
                merged.append((rasterize(rc, args.size) if rok else None, rok))
            rows.append(merged)
    else:
        for w in weights:
            items = load_contours(args.font, w, args.text)
            rows.append([(rasterize(c, args.size) if ok else None, ok)
                         for c, ok in items])

    img = compose(rows, args.size)
    img.save(args.out)
    print("saved", args.out, img.size)


if __name__ == "__main__":
    main()
