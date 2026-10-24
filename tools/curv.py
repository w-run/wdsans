"""弯钩曲率剖面：转折处是否有折点。

沿轮廓走，逐点算切线角，再用固定弧长窗口求"转角 / 弧长"（曲率）。
平滑的弧，曲率连续变化；有折点的地方，曲率会出现尖峰。

注意：端面和直角本来就转得急，所以先剔除单点大转角（>25°）的位置，
只看"弧段内"的曲率平滑度。

输出：
    kappa_max   最大曲率（1/em），等价最小半径
    kappa_p90   90 分位
    spike       最大曲率 / 中位曲率 —— 越大说明越"不均"，越可能有折点
    at          峰值位置

用法：
    python3 curv.py --fonts "shs=...,ops=..." --glyphs 乙尤九也心 --json /tmp/c.json
"""
import argparse
import json
import math
import statistics as st
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen   # noqa: E402

WIN = 40.0        # 弧长窗口
CORNER = 25.0     # 单点转角超过它算硬角，不参与曲率


def profile(pts):
    n = len(pts) - 1 if pts[0] == pts[-1] else len(pts)
    if n < 20:
        return None
    turn = []
    seg = []
    for i in range(n):
        a, b, c = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        if l1 < 1e-6 or l2 < 1e-6:
            turn.append(0.0)
            seg.append(0.0)
            continue
        cosv = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
        turn.append(math.degrees(math.acos(cosv)))
        seg.append(l2)
    ks = []
    pos = []
    for i in range(n):
        acc_t = 0.0
        acc_l = 0.0
        j = i
        cnt = 0
        while acc_l < WIN and cnt < n // 2:
            if turn[j] <= CORNER:
                acc_t += turn[j]
            acc_l += seg[j]
            j = (j + 1) % n
            cnt += 1
        if acc_l < WIN * 0.7:
            continue
        ks.append(math.radians(acc_t) / acc_l)
        pos.append(pts[i])
    if len(ks) < 10:
        return None
    ks_sorted = sorted(ks)
    kmed = ks_sorted[len(ks) // 2]
    kmax = ks_sorted[-1]
    kp90 = ks_sorted[int(len(ks_sorted) * 0.9)]
    imax = ks.index(kmax)
    return {
        "kappa_max": round(kmax, 5),
        "r_min": round(1 / kmax, 0) if kmax > 1e-9 else 0,
        "kappa_med": round(kmed, 5),
        "kappa_p90": round(kp90, 5),
        "spike": round(kmax / kmed, 2) if kmed > 1e-9 else 0,
        "at": [round(v) for v in pos[imax]],
    }


def measure(path, chars):
    font = TTFont(path)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    out = {}
    for ch in chars:
        gn = cmap.get(ord(ch))
        if not gn:
            continue
        pen = FlatPen(gs)
        gs[gn].draw(pen)
        pen._end()
        best = None
        for c in pen.contours:
            r = profile(c)
            if r and (best is None or r["kappa_max"] > best["kappa_max"]):
                best = r
        if best:
            out[ch] = best
    font.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--glyphs", default="乙尤九也心飞气几凡")
    ap.add_argument("--json", required=True)
    a = ap.parse_args()
    fonts = [(s.split("=", 1)[0].strip(), s.split("=", 1)[1].strip())
             for s in a.fonts.split(",")]
    out = {k: measure(p, a.glyphs) for k, p in fonts}
    json.dump(out, open(a.json, "w"), ensure_ascii=False, indent=1)
    print("saved", a.json)


if __name__ == "__main__":
    main()
