"""参照对照表：Noto / OPPO / HOS 同尺寸并排，带标尺。

用途：设计决策必须先看图。数值只能证明「没坏」，不能证明「好看」。
"""
from __future__ import annotations
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from tool_glyph_svg import glyph_svg  # noqa

FONTS = [
    ("Noto（基座）", "/workspace/wdsans/ref/NotoSansCJKsc-VF.ttf", True),
    ("OPPO（主参照）", "/workspace/wdsans/ref/ops/ops-400.ttf", False),
    ("HOS（次参照）", "/workspace/wdsans/ref/hos/hos-400.ttf", False),
]


def load(path, wght=400):
    f = TTFont(path)
    if "fvar" in f:
        f = instancer.instantiateVariableFont(
            f, {"wght": wght}, inplace=True, updateFontNames=False, optimize=False
        )
    return f


def render(open_fn):
    raise NotImplementedError


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("chars")
    ap.add_argument("--outdir", default="/tmp/glow/cmp")
    ap.add_argument("--wght", type=int, default=400)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    for label, path, is_var in FONTS:
        f = load(path, a.wght)
        for ch in a.chars:
            try:
                svg = glyph_svg(f, ch, show_index=False)
            except SystemExit:
                print(f"  {label} 缺 {ch}")
                continue
            base = f"{a.outdir}/{ch}-{label.split(chr(65288))[0]}"
            open(base + ".svg", "w", encoding="utf-8").write(svg)
            subprocess.run(["rsvg-convert", "-o", base + ".png", "--zoom", "1.0", base + ".svg"],
                           check=False)
            print("wrote", base + ".png")