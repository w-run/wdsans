"""笔端与点形研究。

两个探针：
  extreme_angle  轮廓最外侧一点处的夹角（180° = 平端面，<100° = 出锋尖角）
  dots           小面��块（点）的数量、长宽比、面积占比

用法：
    python3 ends.py --fonts "shs=...,ops=..." --json /tmp/ends.json
"""
import argparse
import json
import math
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen, signed_area   # noqa: E402

EM = 1e6  # 1000×1000


def _angle_at(pts, idx, reach=10.0):
    """在 idx 点，沿轮廓两侧各走 reach 弧长，求两方向的夹角（度）。"""
    n = len(pts) - 1 if pts[0] == pts[-1] else len(pts)
    if n < 8:
        return None
    i = idx % n

    def walk(step):
        acc = 0.0
        j = i
        while acc < reach:
            k = (j + step) % n
            acc += math.dist(pts[j % n], pts[k])
            j = k
        return pts[j % n]

    a = walk(-1)
    b = walk(+1)
    v1 = (pts[i][0] - a[0], pts[i][1] - a[1])
    v2 = (b[0] - pts[i][0], b[1] - pts[i][1])
    l1, l2 = math.hypot(*v1), math.hypot(*v2)
    if l1 < 1e-6 or l2 < 1e-6:
        return None
    cosv = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
    return math.degrees(math.acos(cosv))


def extreme_angle(cs, side):
    """side: left/right/top/bottom → 该侧最外点处的夹角。"""
    best = None
    for c in cs:
        n = len(c) - 1 if c[0] == c[-1] else len(c)
        for i in range(n):
            p = c[i]
            key = {"left": -p[0], "right": p[0],
                   "top": p[1], "bottom": -p[1]}[side]
            if best is None or key > best[0]:
                best = (key, c, i)
    if not best:
        return None
    _, c, i = best
    return _angle_at(c, i)


def dots(cs, lo=0.0015, hi=0.045):
    """小面积轮廓 = 点。返回数量与几何特征。"""
    out = []
    for c in cs:
        a = abs(signed_area(c))
        f = a / EM
        if not (lo <= f <= hi):
            continue
        xs = [p[0] for p in c]
        ys = [p[1] for p in c]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        if w < 12 or h < 12:
            continue
        # 填充率：面积 / 外接矩形
        fill = a / (w * h) if w * h else 0
        out.append({"w": round(w), "h": round(h), "area": round(f, 4),
                    "aspect": round(w / h, 2) if h else 0,
                    "fill": round(fill, 2)})
    return out


# 侧重点：斜笔末端（右上/右下）、横画端、撇端
CASES = {
    "斜笔末端": [("乙", "right"), ("九", "right"), ("飞", "right"),
                 ("凡", "right"), ("刀", "right"), ("力", "right"),
                 ("乃", "right"), ("万", "right"), ("方", "right"),
                 ("了", "right"), ("子", "bottom"), ("刁", "right")],
    "横端": [("一", "right"), ("二", "right"), ("三", "right"),
             ("工", "right"), ("王", "right"), ("十", "right")],
    "撇端": [("人", "left"), ("八", "left"), ("木", "left"),
             ("大", "left"), ("少", "left")],
}

DOT_GLYPHS = ["心", "火", "六", "主", "江", "燕", "杰", "冬"]


def measure(path):
    font = TTFont(path)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    res = {"ends": {}, "dots": {}}
    for grp, items in CASES.items():
        res["ends"][grp] = {}
        for ch, side in items:
            gn = cmap.get(ord(ch))
            if not gn:
                continue
            pen = FlatPen(gs)
            gs[gn].draw(pen)
            pen._end()
            a = extreme_angle(pen.contours, side)
            if a is not None:
                res["ends"][grp][ch] = round(a, 0)
    for ch in DOT_GLYPHS:
        gn = cmap.get(ord(ch))
        if not gn:
            continue
        pen = FlatPen(gs)
        gs[gn].draw(pen)
        pen._end()
        res["dots"][ch] = dots(pen.contours)
    font.close()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--json", required=True)
    a = ap.parse_args()
    fonts = [(s.split("=", 1)[0].strip(), s.split("=", 1)[1].strip())
             for s in a.fonts.split(",")]
    out = {k: measure(p) for k, p in fonts}
    json.dump(out, open(a.json, "w"), ensure_ascii=False, indent=1)
    print("saved", a.json)


if __name__ == "__main__":
    main()
