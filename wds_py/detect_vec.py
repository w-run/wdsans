#!/usr/bin/env python3
"""端点检测的 numpy 向量化实现。

原版（detect-feet.js / detect-ends.js）是逐点 Python 循环，60 点 × 7 次判定，
在 iSH 上既慢又不稳（26–161 秒波动）。这里改成一次性对所有点算。

与标量版语义完全一致，用 tests/cmp_detect.py 校验。
"""
import numpy as np


def _angle_deg(p1, p2, p3):
    """p2 为顶点，逆时针角度（度）。输入均为 (N,2) 数组。"""
    v1 = p1 - p2
    v2 = p3 - p2
    n1 = np.hypot(v1[:, 0], v1[:, 1])
    n2 = np.hypot(v2[:, 0], v2[:, 1])
    with np.errstate(invalid='ignore', divide='ignore'):
        c = np.clip((v1[:, 0] * v2[:, 0] + v1[:, 1] * v2[:, 1])
                    / (n1 * n2), -1.0, 1.0)
    convex = np.arccos(c)
    outer = v1[:, 0] * v2[:, 1] - v2[:, 0] * v1[:, 1]
    a = np.where(outer > 0, convex, 2 * np.pi - convex)
    a = np.where((n1 == 0) | (n2 == 0), 0.0, a)
    return np.degrees(a)


def _windows(xy, on, k):
    """返回 k 个错位视图（含环绕）。"""
    n = len(xy)
    idx = [(np.arange(n) + i) % n for i in range(k)]
    return [xy[i] for i in idx], [on[i] for i in idx]


def detect_feet_vec(contour, max_stroke=10, longest_foot=100, angle_tol=2):
    n = len(contour)
    if n < 7:
        return [], []
    xy = np.array([[p['x'], p['y']] for p in contour], dtype=np.float64)
    on = np.array([p['on'] for p in contour], dtype=bool)
    P, O = _windows(xy, on, 7)

    ok = O[0] & O[1] & O[2] & O[3] & O[4]
    ok &= P[0][:, 1] > P[1][:, 1]
    ok &= np.abs(P[0][:, 0] - P[1][:, 0]) <= 20

    a1 = _angle_deg(P[2], P[1], P[0])
    a2 = _angle_deg(P[3], P[2], P[1])
    a3 = _angle_deg(P[4], P[3], P[2])
    ok &= np.abs(a1 - 90) < angle_tol
    ok &= np.abs(a2 - 90) < angle_tol
    ok &= np.abs(a3 - 270) < angle_tol

    foot_len = np.hypot(*(P[3] - P[2]).T)
    foot_w = np.hypot(*(P[2] - P[1]).T)
    ok &= foot_len <= longest_foot
    ok &= foot_w <= max_stroke
    ok &= (P[0][:, 1] - P[3][:, 1]) >= 1.5 * max_stroke

    # 「月」：pt6 on 且 pt7 off，且 pt6 在两段之间，pt7.x <= pt5.x+10
    yue = (O[5] & ~O[6]
           & (P[5][:, 1] < P[4][:, 1])
           & (P[5][:, 1] > P[1][:, 1])
           & (P[6][:, 0] <= P[4][:, 0] + 10))
    # 「非」：pt7.y 在 pt4.y 之上但很近
    fei = (P[6][:, 1] > P[3][:, 1]) & ((P[6][:, 1] - P[3][:, 1]) < max_stroke)
    ok &= ~yue
    ok &= ~fei
    ok &= P[3][:, 1] <= 750

    left = [int((i + 1) % n) for i in np.nonzero(ok)[0]]

    # 右脚：左右镜像后复用同一判定
    mirrored = np.column_stack([1000 - xy[:, 0], xy[:, 1]])
    Pm, Om = _windows(mirrored[::-1].copy(), on[::-1].copy(), 7)
    ok2 = Om[0] & Om[1] & Om[2] & Om[3] & Om[4]
    ok2 &= Pm[0][:, 1] > Pm[1][:, 1]
    ok2 &= np.abs(Pm[0][:, 0] - Pm[1][:, 0]) <= 20
    b1 = _angle_deg(Pm[2], Pm[1], Pm[0])
    b2 = _angle_deg(Pm[3], Pm[2], Pm[1])
    b3 = _angle_deg(Pm[4], Pm[3], Pm[2])
    ok2 &= np.abs(b1 - 90) < angle_tol
    ok2 &= np.abs(b2 - 90) < angle_tol
    ok2 &= np.abs(b3 - 270) < angle_tol
    ok2 &= np.hypot(*(Pm[3] - Pm[2]).T) <= longest_foot
    ok2 &= np.hypot(*(Pm[2] - Pm[1]).T) <= max_stroke
    ok2 &= (Pm[0][:, 1] - Pm[3][:, 1]) >= 1.5 * max_stroke
    yue2 = (Om[5] & ~Om[6] & (Pm[5][:, 1] < Pm[4][:, 1])
            & (Pm[5][:, 1] > Pm[1][:, 1])
            & (Pm[6][:, 0] <= Pm[4][:, 0] + 10))
    fei2 = (Pm[6][:, 1] > Pm[3][:, 1]) & ((Pm[6][:, 1] - Pm[3][:, 1]) < max_stroke)
    ok2 &= ~yue2
    ok2 &= ~fei2
    ok2 &= Pm[3][:, 1] <= 750

    # 镜像索引 j 对应原索引 n-1-j，右脚位置 = mod(i+5, n)
    right = []
    for j in np.nonzero(ok2)[0]:
        i = (n - 1 - int(j)) % n
        right.append(int((i + 5) % n))
    # 去重（镜像可能重复命中）
    right = sorted(set(right))
    return left, right


def detect_ends_vec(contour, max_stroke=10, angle_tol=20):
    n = len(contour)
    if n < 6:
        return []
    xy = np.array([[p['x'], p['y']] for p in contour], dtype=np.float64)
    on = np.array([p['on'] for p in contour], dtype=bool)
    P, O = _windows(xy, on, 6)

    ok = (~O[0]) & O[1] & (~O[2]) & (~O[3]) & O[4] & (~O[5])
    ok &= np.hypot(*(P[4] - P[1]).T) <= max_stroke * 1.4
    a1 = _angle_deg(P[4], P[1], P[0])
    a2 = _angle_deg(P[5], P[4], P[1])
    ok &= np.abs(a1 + a2 - 160) < angle_tol

    return [int((i + 1) % n) for i in np.nonzero(ok)[0]]
