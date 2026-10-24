"""修复 otfccdump 对 TrueType 的曲线退化：用 fontTools 的 Qu2CuPen 精确转三次曲线，
替换 otfcc JSON 里的 contours。

用法: python3 fix_mona_curves.py <Mona-N.ttf> <Mona-N.json> <out.json>
"""
import json
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.qu2cuPen import Qu2CuPen


class ContourPen(BasePen):
    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.contours = []

    def _moveTo(self, pt):
        self.contours.append([{'x': pt[0], 'y': pt[1], 'on': True}])

    def _lineTo(self, pt):
        self.contours[-1].append({'x': pt[0], 'y': pt[1], 'on': True})

    def _curveToOne(self, p1, p2, p3):
        c = self.contours[-1]
        c.append({'x': p1[0], 'y': p1[1], 'on': False})
        c.append({'x': p2[0], 'y': p2[1], 'on': False})
        c.append({'x': p3[0], 'y': p3[1], 'on': True})

    def _closePath(self):
        pass


def main():
    ttf_path, json_path, out_path = sys.argv[1:4]
    ttf = TTFont(ttf_path)
    gs = ttf.getGlyphSet()
    data = json.load(open(json_path))

    fixed = 0
    for name in ttf.getGlyphOrder():
        if name not in data['glyf']:
            continue
        cp = ContourPen(gs)
        pen = Qu2CuPen(cp, max_err=0.5, all_cubic=True)
        gs[name].draw(pen)
        data['glyf'][name]['contours'] = [
            [{'x': int(round(p['x'])), 'y': int(round(p['y'])), 'on': p['on']}
             for p in c] for c in cp.contours
        ]
        fixed += 1

    json.dump(data, open(out_path, 'w'))
    print(f'{ttf_path}: fixed {fixed} glyphs -> {out_path}')


main()
