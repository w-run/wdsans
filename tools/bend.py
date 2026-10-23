"""弯钩 / 折笔的转折测量。

分两件事量，不能混：
  · 硬点（折）：单个顶点转角 > 20°  —— 真正的"折"
  · 弯的半径：剔除硬点后，用滑窗曲率算最小半径与过渡长度

曲率用弧长窗口，避免展平带来的逐点噪声。

用法：
    python3 bend.py --fonts "shs=...,ops=..." --glyphs 乙尤九也心 --json /tmp/b.json
"""
import argparse
import json
import math
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen   # noqa: E402

WIN = 70.0      # 弧长窗口（em 单位），约等于一笔的宽度量级
CORNER = 20.0   # 单点转角超过它就算硬点


def trace(pts):
    """逐顶点：转角（度）、段长。"""
    n = len(pts) - 1 if pts[0] == pts[-1] else len(pts)
    out = []
    for i in range(n):
        a, b, c = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        l1 = math.hypot(*v1)
        l2 = math.hypot(*v2)
        if l1 < 1e-6 or l2 < 1e-6:
            continue
        cosv = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
        turn = math.degrees(math.acos(cosv))
        out.append({"p": b, "turn": turn, "len": l2})
    return out


def analyse(contours):
    best = {"kappa": 0.0, "r": 1e9, "at": None, "arc": 0.0}
    hard = 0
    for pts in contours:
        tr = trace(pts)
        if len(tr) < 10:
            continue
        hard += sum(1 for t in tr if t["turn"] > CORNER)
        m = len(tr)
        for i in range(m):
            # 以 i 为起点，累积到弧长 WIN
            acc_turn = 0.0
            acc_len = 0.0
            j = i
            cnt = 0
            while acc_len < WIN and cnt < m // 2:
                t = tr[j % m]
                if t["turn"] <= CORNER:        # 硬点不参与曲率
                    acc_turn += t["turn"]
                acc_len += t["len"]
                j += 1
                cnt += 1
            if acc_len < WIN * 0.6:
                continue
            kappa = math.radians(acc_turn) / acc_len     # 1/em
            if kappa > best["kappa"]:
                best = {"kappa": kappa,
                        "r": (1.0 / kappa) if kappa > 1e-9 else 1e9,
                        "at": tr[i]["p"], "arc": acc_len}
    return {"r_min": round(best["r"], 1), "kappa": round(best["kappa"], 5),
            "hard": hard,
            "at": [round(v) for v in best["at"]] if best["at"] else None}


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
        if pen.contours:
            out[ch] = analyse(pen.contours)
    font.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--glyphs", default="乙尤九也心飞气乞")
    ap.add_argument("--json", required=True)
    a = ap.parse_args()
    fonts = [(s.split("=", 1)[0].strip(), s.split("=", 1)[1].strip())
             for s in a.fonts.split(",")]
    out = {}
    for k, p in fonts:
        out[k] = measure(p, a.glyphs)
    json.dump(out, open(a.json, "w"), ensure_ascii=False, indent=1)
    print("saved", a.json)


if __name__ == "__main__":
    main()
