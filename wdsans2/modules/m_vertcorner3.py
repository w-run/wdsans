#!/usr/bin/env python3
"""m_vertcorner3 - 横折突出拐角 -> 垂直过渡（保留回折段，不改变斜边厚度）

用户明确: 400 字重的拐角就是目标形态。
  - 400 以上更重: 横画有点长
  - 400 以下更轻: 斜画漏在横画外面
  - 期望: 斜边终点像 400 那样平滑过渡到横画，收在横画轮廓内部

## 400 档实测（目标几何）
    c1: start(734,752) -> L(719,752) -> C... -> C(770,685) -> close
    c2 横笔: (770,752)(385,752)(385,685)(770,685)
    横笔右上角 = (770,752)，c1 起点 = (734,752)，dx=-36
    斜边右端终点 = (770,685) = 横笔右下角（精确重合）

## R51 为什么不合格
    删掉了 c1 的 s0（回折段），斜边上边缘起点从 x=719 变成 x=770
    => 斜边上端加宽 51 单位 => 斜边变粗

## 本模块做法
    1. 保留 s0（斜边上边缘起点不变）=> 斜边厚度不变
    2. c1.start.x 对齐到横笔右端 x   => close 线变垂直
    3. c1.start.y 与 s0 终点 y 都对齐到横笔上缘
       (原字在这两处有 1 单位错位，导致轻字重下出现细缝)

## 三档实测
    w250: start(743,736) s0(736,736) 横笔y[708,737]
    w400: start(734,752) s0(719,752) 横笔y[685,752]  <- 目标
    w900: start(719,776) s0(691,776) 横笔y[650,777]
    三档 start.y / s0.y 都比横笔上缘低 1 单位，需一并对齐
"""
import numpy as np

NAME = "vertcorner3"
DESC = "横折拐角垂直过渡（保斜边厚度）"

TOL = 10.0
MIN_W = 200
MAX_H = 140
MIN_DX = 5
MAX_DX = 120


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
    """返回 [(P_id, bar_right_x, bar_top_y)]"""
    out = []
    bars = []
    for i, c in enumerate(C):
        if is_rect_bar(c):
            bars.append((i, bbox_of(c)))
    for i, c in enumerate(C):
        if is_rect_bar(c):
            continue
        if len(c["segs"]) < 3:
            continue
        if c["segs"][0][0] != "L":
            continue
        st = np.array(c["start"], float)
        s0 = np.array(c["segs"][0][1], float)
        # 回折段: 短、水平、向左
        if abs(s0[1] - st[1]) > TOL:
            continue
        if s0[0] >= st[0]:
            continue
        Pd = allpts(c)
        p_e = Pd[-1]
        for bi, bb in bars:
            bx0, bx1, by0, by1 = bb
            if bi == i:
                continue
            # 斜边终点 x 须与横笔右端对齐（结构签名：斜边收在横笔右缘）
            if abs(p_e[0] - bx1) > TOL:
                continue
            # 终点 y 不必在底边 —— 这正是要修的偏差
            # 但偏离过大说明不是同一个角，动态上限 = 3 倍横笔厚度
            bt = by1 - by0
            if bt <= 0:
                continue
            if abs(p_e[1] - by0) > bt * 3.0:
                continue
            # start 须在横笔上缘附近
            if abs(st[1] - by1) > TOL:
                continue
            dx = bx1 - st[0]
            if not (MIN_DX <= dx <= MAX_DX):
                continue
            out.append((i, float(bx1), float(by0), float(by1)))
            break
    return out


def apply(C, hits):
    NEW = []
    for c in C:
        NEW.append({"start": c["start"], "segs": [list(s) for s in c["segs"]]})
    for hit in hits:
        pid, bx1, by0, by1 = hit[0], hit[1], hit[2], hit[3]
        c = NEW[pid]
        # ① 上落点: start 移到横笔右上角 => close 线垂直
        c["start"] = (bx1, by1)
        # ② s0 终点 y 对齐横笔上缘（修 1 单位缝隙，x 不动保斜边厚度）
        s = list(c["segs"][0])
        s[1] = (s[1][0], by1)
        c["segs"][0] = s
        # ③ 下落点: 斜边末点 y 对齐横笔底边（x 不动）
        last = c["segs"][-1]
        if last[0] == "C":
            nl = list(last)
            nl[3] = (nl[3][0], by0)
            c["segs"][-1] = nl
        elif last[0] == "L":
            nl = list(last)
            nl[1] = (nl[1][0], by0)
            c["segs"][-1] = nl
    return NEW
