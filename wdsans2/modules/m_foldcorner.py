#!/usr/bin/env python3
"""m_foldcorner - 横折拐角一体化处理（上落点 + 下落点）

## 用户需求
  1. 横折突出拐角 -> 垂直过渡（400 档是目标形态）
  2. 斜边落点 y 与横线底边平齐
  3. 边改边微调

## 三档实测（多）
    档   c1(上斜)末点  c2上横y范围     关系
    250  (770,708)    [708,737]      末点=底边 OK
    400  (770,685)    [685,752]      末点=底边 OK
    900  (770,650)    [650,777]      末点=底边 OK
    => 上部落点三档都正确，只需处理 start.x

    档   c5(下斜)末点  c6下横y范围     关系
    250  (924,332)    [373,402]      末点低 41  <-- 外露
    400  (924,332)    [332,400]      末点=底边 OK
    900  (924,332)    [268,396]      末点高 64  <-- 藏进
    => 下部落点三档不一致，需按本档横笔底边对齐

## 判据（全动态，不用硬编码数值）
  横笔 = 3 段纯 L 的矩形轮廓
  斜边 = 其余轮廓中，末点 x 与横笔右端 x 对齐（容差=横笔厚度*0.12）的那个
  ① 上落点: 斜边起点 y 在横笔上缘、起点 x 在横笔右端左侧 -> 
             start.x 对齐到横笔右端（形成垂直过渡）
  ② 下落点: 斜边末点 y 与横笔底边不等 -> 对齐到横笔底边

## 安全
  只移动单个点的坐标，段数与操作符不变 -> VF 安全
  三档各自按本档几何计算，不跨档套用绝对值
"""
import numpy as np

NAME = "foldcorner"
DESC = "横折拐角：垂直过渡 + 落点对齐"


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
    return all(s[0] == "L" for s in c["segs"])


def find(C):
    """返回 [(kind, pid, seg_idx, new_x, new_y)]
    kind: "top"=上落点垂直过渡, "bot"=下落点对齐底边
    seg_idx: -1 表示 start，否则为 segs 索引"""
    out = []
    bars = []
    for i, c in enumerate(C):
        if is_rect_bar(c):
            bb = bbox_of(c)
            bars.append((i, bb))
    if not bars:
        return out

    for i, c in enumerate(C):
        if is_rect_bar(c):
            continue
        if len(c["segs"]) < 3:
            continue
        P = allpts(c)
        p_s = P[0]
        p_e = P[-1]
        for bi, (bx0, bx1, by0, by1) in bars:
            bt = by1 - by0
            bw = bx1 - bx0
            if bt <= 0 or bw <= 0:
                continue
            tol = bt * 0.12

            # ---- ① 上落点: 终点精确等于横笔右下角，起点在横笔上缘 ----
            # 动态容差: 只允许横笔厚度 5% 的偏差（原 20% 在粗档过宽）
            if (abs(p_e[0] - bx1) <= bt * 0.05 and
                    abs(p_e[1] - by0) <= bt * 0.05 and
                    abs(p_s[1] - by1) <= bt * 0.05):
                # start 须在横笔右端左侧，但差距不超过一个横笔厚度
                dx = bx1 - p_s[0]
                if bt * 0.10 < dx < bt * 1.2:
                    # 起点 x 对齐横笔右端，y 对齐横笔上缘
                    out.append(("top", i, -1, float(bx1), float(by1)))
                    # 同时把第一个 seg 终点 y 对齐（修 1 单位缝隙）
                    if c["segs"][0][0] == "L":
                        sv = c["segs"][0][1]
                        if abs(sv[1] - by1) <= bt * 0.20:
                            out.append(("s0y", i, 0, float(sv[0]), float(by1)))
                    continue

            # ---- ② 下落点: 终点 x 对齐横笔右端，y 不等于底边 ----
            if abs(p_e[0] - bx1) <= tol:
                dy = p_e[1] - by0
                if abs(dy) > bt * 0.15 and abs(dy) < bt * 3.0:
                    out.append(("bot", i, len(c["segs"]) - 1, float(p_e[0]), float(by0)))
                    break
    return out


def apply(C, hits):
    NEW = []
    for c in C:
        NEW.append({"start": c["start"],
                    "segs": [list(s) for s in c["segs"]]})
    for kind, pid, si, nx, ny in hits:
        c = NEW[pid]
        if si < 0:
            c["start"] = (nx, ny)
            continue
        if si >= len(c["segs"]):
            continue
        s = list(c["segs"][si])
        if s[0] == "C":
            s[3] = (nx, ny)
        elif s[0] == "Q":
            s[2] = (nx, ny)
        elif s[0] == "L":
            s[1] = (nx, ny)
        else:
            continue
        c["segs"][si] = s
    return NEW
