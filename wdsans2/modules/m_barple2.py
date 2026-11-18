#!/usr/bin/env python3
"""m_barple2 - 横折去拐角（重写 m_barple）

## 目标
去掉 SHS 的「横笔冲出再回折」拐角，让横笔右缘垂直落到横笔下缘，
撇从横笔右下角起笔 —— 与 400 档的既有形态一致。

## m_barple 的两个错误
1. 把 400 档检测出的 (xR, by0) 硬套到三档：
   250 档的 xR 应为 758（本档交点），却用了 770 -> 右移 12；
   by0 应为 708（本档横笔下缘），却用了 685 -> 上移 23。
   结果：撇被撑粗 36%（实测 38 vs SHS 28）。
2. 只把 body 末点移到 (xR, by0)，横笔右端仍留在原位 ->
   两者相差 12~76 单位 -> 横笔右端悬空 -> 出现凹口（用户截图红框）。

## 本版做法
三档各自计算：
  xR  = body 轮廓在 y=本档 bar_bot 处的右缘交点
  横笔右端 -> xR      （补齐悬空，形成竖直右缘）
  body 末点 -> (xR, bar_bot)
  删除 seg4 回折段

实测（多）:
  档    bar右端  xR    末点        撇厚   SHS
  250     745    758   (758,708)    27     28
  400     733    770   (770,685)    70     71
  900     712    788   (788,650)   144    154
"""
import numpy as np

NAME = "barple2"
DESC = "横折去拐角（三档各自求交点，横笔补齐到交点）"


def endp(s):
    return np.array(s[1][-1], float) if s[0] == "QM" else np.array(s[-1], float)


def bbox(c):
    pts = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: pts.append(np.array(q, float))
        elif s[0] == "C":
            pts.extend([np.array(s[1], float), np.array(s[2], float), np.array(s[3], float)])
        elif s[0] == "Q":
            pts.extend([np.array(s[1], float), np.array(s[2], float)])
        else:
            pts.append(np.array(s[1], float))
    P = np.array(pts)
    return P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()


def poly(c, n=200):
    pts = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "C":
            p0 = pts[-1]
            c1 = np.array(s[1], float); c2 = np.array(s[2], float); p3 = np.array(s[3], float)
            for i in range(1, n + 1):
                t = i / n; mt = 1 - t
                pts.append(mt**3*p0 + 3*mt*mt*t*c1 + 3*mt*t*t*c2 + t**3*p3)
        elif s[0] == "QM":
            for q in s[1]: pts.append(np.array(q, float))
        else:
            pts.append(np.array(s[1], float))
    return np.array(pts)


def xcross(P, y):
    xs = []
    for i in range(len(P) - 1):
        a = P[i]; b = P[i+1]
        if (a[1]-y)*(b[1]-y) <= 0 and abs(b[1]-a[1]) > 1e-9:
            t = (y - a[1]) / (b[1] - a[1])
            xs.append(a[0] + t*(b[0]-a[0]))
    return sorted(xs)


def find(C, sw=None):
    """返回 [(bar_idx, body_idx, xR, bar_bot), ...]  -- 依赖本档几何"""
    res = []
    for bi, bar in enumerate(C):
        if len(bar["segs"]) != 3 or "".join(s[0] for s in bar["segs"]) != "LLL":
            continue
        bb = bbox(bar)
        w = bb[1] - bb[0]; h = bb[3] - bb[2]
        if h <= 0 or w / h < 1.8 or w < 200:
            continue
        for ci, body in enumerate(C):
            if ci == bi:
                continue
            segs = body["segs"]
            if len(segs) < 5 or segs[-1][0] != "L" or segs[-2][0] != "C":
                continue
            apex = endp(segs[-2]); fold = endp(segs[-1])
            # 拐角: 冲出点比横笔右端靠右，回折点又比冲出点靠左
            if apex[0] <= bb[1] + 2:
                continue
            if fold[0] >= apex[0] - 2:
                continue
            if not (bb[2] - 6 <= apex[1] <= bb[3] + 6):
                continue
            xs = xcross(poly(body), bb[2])
            if len(xs) < 2:
                continue
            xR = xs[-1]
            if xR <= bb[1]:
                continue
            res.append((bi, ci, xR, bb[2]))
            break
    return res


def apply(C, hits):
    NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
    for bi, ci, xR, bar_bot in hits:
        bar = NEW[bi]
        bar["start"] = (xR, bar["start"][1])
        bar["segs"][2] = ["L", (xR, bar["segs"][2][-1][1])]
        segs = NEW[ci]["segs"]
        segs[-2] = ["C", segs[-2][1], segs[-2][2], (xR, bar_bot)]
        del segs[-1]
    return NEW