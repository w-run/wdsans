"""墨量剖面：字形骨架的投影指纹。

一个字形在 em 框里怎么分布墨，决定了它的"骨架"与"布白"。
这里把墨量沿 x / y 各投成 16 段，归一化后得到剖面曲线 ——
两家剖面差在哪一段，骨架差异就落在哪一段。

派生指标：
  左右平衡   left / right         左右结构是否偏重
  上下平衡   top / bottom
  中宫松紧   中央 4×4 格墨量 / 全字墨量
  重心       墨重心 (cx, cy)

用法：
    python3 profile.py --fonts "shs=...,hos=...,ops=..." --charset structure \\
        --json /tmp/p.json
"""
import argparse
import json
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen   # noqa: E402

X0, X1 = -20.0, 1020.0      # 与 glyph_view 同画框
Y_TOP, Y_BOT = 900.0, -140.0
N = 16                       # 16×16，与格位编号一致
CW = (X1 - X0) / N
CH = (Y_TOP - Y_BOT) / N

# 结构分类样本：每类 4–6 字，覆盖骨架差异最敏感的形状
STRUCTURE = {
    "独体": "永木水火大小人心力女",
    "上下": "京雪思花字泉",
    "左右": "明林特到江部",
    "包围": "国回田同门图",
    "半包围": "这建延局原",
    "复杂": "赢藏攀囊",
    "极简": "一二十丁厂",
    "钩折": "事丁手寸也己",
}


def scan_runs(cs, coord, axis="h"):
    ev = []
    for pts in cs:
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if axis == "h":
                a, b, u0, u1 = y0, y1, x0, x1
            else:
                a, b, u0, u1 = x0, x1, y0, y1
            if a == b:
                continue
            lo, hi = (a, b) if a < b else (b, a)
            if not (lo <= coord < hi):
                continue
            t = (coord - a) / (b - a)
            ev.append((u0 + t * (u1 - u0), 1 if b > a else -1))
    if not ev:
        return []
    ev.sort()
    out = []
    w = 0
    start = None
    for u, d in ev:
        prev = w
        w += d
        if prev == 0 and w != 0:
            start = u
        elif prev != 0 and w == 0 and start is not None:
            out.append((start, u))
            start = None
    return out


def ink_grid(cs, step=2.0):
    """把墨量铺到 16×16 网格上（按面积精确积分，不是采样像素）。"""
    g = [[0.0] * N for _ in range(N)]
    y = Y_BOT + step / 2
    while y < Y_TOP:
        for (a, b) in scan_runs(cs, y, "h"):
            aa, bb = max(a, X0), min(b, X1)
            if bb <= aa:
                continue
            ri = int((Y_TOP - y) / CH)
            if not (0 <= ri < N):
                continue
            ci0 = int((aa - X0) / CW)
            ci1 = int((bb - X0) / CW)
            for ci in range(max(0, ci0), min(N - 1, ci1) + 1):
                lo = X0 + ci * CW
                hi = lo + CW
                w = min(bb, hi) - max(aa, lo)
                if w > 0:
                    g[ri][ci] += w * step
        y += step
    return g


def summarise(g):
    tot = sum(sum(r) for r in g)
    if tot <= 0:
        return None
    px = [sum(g[r][c] for r in range(N)) / tot for c in range(N)]
    py = [sum(g[r]) / tot for r in range(N)]
    # 重心：网格中心取 0..1
    cx = sum((c + 0.5) / N * px[c] for c in range(N))
    cy = sum((r + 0.5) / N * py[r] for r in range(N))
    left = sum(px[:N // 2])
    right = sum(px[N // 2:])
    top = sum(py[:N // 2])
    bot = sum(py[N // 2:])
    # 中宫：中央 4×4
    k0 = N // 2 - 2
    core = sum(sum(g[r][c] for c in range(k0, k0 + 4)) for r in range(k0, k0 + 4)) / tot
    return {
        "px": [round(v, 4) for v in px],
        "py": [round(v, 4) for v in py],
        "cx": round(cx, 4), "cy": round(cy, 4),
        "lr": round(left / right, 3) if right > 0 else 0,
        "tb": round(top / bot, 3) if bot > 0 else 0,
        "core": round(core, 4),
        "ink": round(tot / ((X1 - X0) * (Y_TOP - Y_BOT)), 4),
    }


def measure(path, chars):
    font = TTFont(path)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    out = {}
    for ch in chars:
        gn = cmap.get(ord(ch))
        if not gn:
            out[ch] = None
            continue
        pen = FlatPen(gs)
        gs[gn].draw(pen)
        pen._end()
        if not pen.contours:
            out[ch] = None
            continue
        out[ch] = summarise(ink_grid(pen.contours))
    font.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--charset", default="structure")
    ap.add_argument("--chars", default=None)
    ap.add_argument("--json", required=True)
    a = ap.parse_args()

    if a.chars:
        groups = {"自定义": a.chars}
    else:
        groups = STRUCTURE

    fonts = [(s.split("=", 1)[0].strip(), s.split("=", 1)[1].strip())
             for s in a.fonts.split(",")]

    out = {"groups": {}, "per_glyph": {}}
    for key, path in fonts:
        out["per_glyph"][key] = {}
    for gname, chars in groups.items():
        chars = "".join(dict.fromkeys(chars))
        out["groups"][gname] = {}
        for key, path in fonts:
            res = measure(path, chars)
            out["per_glyph"][key].update({f"{gname}/{c}": v for c, v in res.items()})
            ok = [v for v in res.values() if v]
            if not ok:
                continue
            n = len(ok)

            def m(f):
                return sum(f(v) for v in ok) / n
            out["groups"][gname][key] = {
                "n": n,
                "px": [round(sum(v["px"][i] for v in ok) / n, 4) for i in range(N)],
                "py": [round(sum(v["py"][i] for v in ok) / n, 4) for i in range(N)],
                "cx": round(m(lambda v: v["cx"]), 4),
                "cy": round(m(lambda v: v["cy"]), 4),
                "lr": round(m(lambda v: v["lr"]), 3),
                "tb": round(m(lambda v: v["tb"]), 3),
                "core": round(m(lambda v: v["core"]), 4),
                "ink": round(m(lambda v: v["ink"]), 4),
            }
            print(f"{gname:4} {key}: lr={out['groups'][gname][key]['lr']:.3f} "
                  f"tb={out['groups'][gname][key]['tb']:.3f} "
                  f"core={out['groups'][gname][key]['core']:.3f}", file=sys.stderr)
    json.dump(out, open(a.json, "w"), ensure_ascii=False, indent=1)
    print("saved", a.json)


if __name__ == "__main__":
    main()
