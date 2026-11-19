#!/usr/bin/env python3
"""m_landfix - 斜边落点对齐横线底边

## 用户标记的问题（250档）
两个红圈处：上部斜撇落点、下部斜边落点，都多出面积。
「下面的点，y 应该与横线底边平齐」

## 实测（多）
    档   c5.twl.y  c6底边y  差
    250    332       373    -41  <- 落点低 41，多出三角面积
    400    332       332      0  <- 正确
    900    (需测)

## 原因
    250 档横笔厚度只有 29，而 400 档是 68。
    SHS 原始设计里斜边端点固定在 y=332，但横笔底边随厚度变化:
      250: 402-29=373   400: 400-68=332
    所以 250 档的斜边端点落在横笔下方 41 单位。

## 修法
    把斜边末段终点 y 对齐到本档横笔底边 y。
    只改 1 个点的 y -> VF 安全（三档各自按本档横笔底边计算）
"""
import numpy as np

NAME = "landfix"
DESC = "斜边落点对齐横线底边"

TOL = 15.0
MIN_W = 200
MAX_H = 160


def allpts(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]:
                P.append(np.array(q, float))
        elif s[0] == "C":
            P.extend([np.array(s[1], float), np.array(s[2], float), np.array(s[3], float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1], float), np.array(s[2], float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)


def bbox_of(c):
    P = allpts(c)
    return P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max()


def is_rect_bar(c):
    if len(c["segs"]) != 3:
        return False
    if any(s[0] != "L" for s in c["segs"]):
        return False
    x0, x1, y0, y1 = bbox_of(c)
    return (x1 - x0) >= MIN_W and 20 <= (y1 - y0) <= MAX_H


def find(C):
    """返回 [(slant_id, target_y)]：斜边末点 y 对齐横笔底边"""
    out = []
    bars = [(i, bbox_of(c)) for i, c in enumerate(C) if is_rect_bar(c)]
    if not bars:
        return out
    for i, c in enumerate(C):
        if is_rect_bar(c):
            continue
        if len(c["segs"]) < 3:
            continue
        P = allpts(c)
        p_end = P[-1]
        for bi, bb in bars:
            bx0, bx1, by0, by1 = bb
            if bi == i:
                continue
            # 斜边终点 x 须贴近横笔右端
            if abs(p_end[0] - bx1) > TOL:
                continue
            # 终点 y 低于横笔底边 -> 有溢出
            dy = by0 - p_end[1]
            if dy < 8 or dy > 80:
                continue
            P2 = allpts(c)
            if (P2[:,0].max()-P2[:,0].min()) < 300 or (P2[:,1].max()-P2[:,1].min()) < 200:
                continue
            if (bx1 - bx0) < 250:
                continue
            out.append((i, float(by0)))
            break
    return out


def apply(C, hits):
    NEW = []
    for c in C:
        NEW.append({"start": c["start"], "segs": [list(s) for s in c["segs"]]})
    for pid, ty in hits:
        c = NEW[pid]
        last = list(c["segs"][-1])
        if last[0] == "C":
            last[3] = (last[3][0], ty)
        elif last[0] == "L":
            last[1] = (last[1][0], ty)
        else:
            continue
        c["segs"][-1] = last
    return NEW
