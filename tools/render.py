"""渲染样张：把字形画成 PNG，用于视觉判断（铁律：必须看图）。

用法：
    python3 render.py out.png "永国回圖田" --weights 250,400,900 [--transform spread]
"""
import sys
import argparse
from PIL import Image, ImageDraw, ImageChops

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.basePen import BasePen


class FlattenPen(BasePen):
    """把字形路径展平成折线，便于用 PIL 画。"""

    def __init__(self, glyphSet, steps=12):
        super().__init__(glyphSet)
        self.contours = []
        self.current = []
        self.steps = steps

    def _moveTo(self, pt):
        self._flush()
        self.current = [pt]

    def _lineTo(self, pt):
        self.current.append(pt)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.current[-1] if self.current else (0, 0)
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            x = (mt**3 * p0[0] + 3 * mt**2 * t * p1[0]
                 + 3 * mt * t**2 * p2[0] + t**3 * p3[0])
            y = (mt**3 * p0[1] + 3 * mt**2 * t * p1[1]
                 + 3 * mt * t**2 * p2[1] + t**3 * p3[1])
            self.current.append((x, y))

    def _closePath(self):
        self._flush()

    def _endPath(self):
        self._flush()

    def _flush(self):
        if len(self.current) > 2:
            self.contours.append(self.current)
        self.current = []

    def finish(self):
        self._flush()
        return self.contours


def glyph_contours(font, glyph_name, steps=12):
    gs = font.getGlyphSet()
    pen = FlattenPen(gs, steps)
    gs[glyph_name].draw(pen)
    return pen.finish()


def render_grid(font, chars, size=160, cols=None, bg=(255, 255, 255),
                fg=(20, 20, 20), pad=10):
    """把一个字符串渲染成网格 PNG。"""
    cols = cols or len(chars)
    rows = (len(chars) + cols - 1) // cols
    W = cols * (size + pad) + pad
    H = rows * (size + pad) + pad
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    cmap = font.getBestCmap()

    for i, ch in enumerate(chars):
        r, c = divmod(i, cols)
        ox = pad + c * (size + pad)
        oy = pad + r * (size + pad)
        gn = cmap.get(ord(ch))
        if not gn:
            d.text((ox + size // 3, oy + size // 3), "?", fill=(255, 0, 0))
            continue
        try:
            contours = glyph_contours(font, gn)
        except Exception:
            d.text((ox + size // 3, oy + size // 3), "E", fill=(255, 0, 0))
            continue
        # 字形坐标：y 向上，0..1000；用 XOR 累加实现奇偶填充（正确处理中宫）
        s = size / 1000.0
        cell = Image.new("1", (size, size), 0)
        cd = ImageDraw.Draw(cell)
        for ct in contours:
            pts = [(x * s, size - (y + 60) * s) for x, y in ct]
            if len(pts) > 2:
                mask = Image.new("1", (size, size), 0)
                ImageDraw.Draw(mask).polygon(pts, fill=1)
                cell = ImageChops.logical_xor(cell, mask)
        img.paste(fg, (ox, oy), cell)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("text")
    ap.add_argument("--font", default="/tmp/p0/sub.otf")
    ap.add_argument("--weights", default="250,400,900")
    ap.add_argument("--size", type=int, default=160)
    args = ap.parse_args()

    weights = [float(w) for w in args.weights.split(",")]
    vf = TTFont(args.font)
    imgs = []
    for w in weights:
        f = instantiateVariableFont(TTFont(args.font), {"wght": w}, inplace=False)
        imgs.append(render_grid(f, args.text, size=args.size))

    W = max(i.width for i in imgs)
    H = sum(i.height for i in imgs)
    out = Image.new("RGB", (W, H), (255, 255, 255))
    y = 0
    for i in imgs:
        out.paste(i, (0, y)); y += i.height
    out.save(args.out)
    print("saved", args.out, out.size)


if __name__ == "__main__":
    main()
