"""TrueType 轮廓规范化：展开隐式中点。

关键发现（本轮实测）：
  Noto 的「一」在 glyf 里是 **[3 点轮廓, 1 点轮廓]**，不是 4 点矩形！
  TrueType 允许两个连续 off-curve 点之间**隐含一个 on-curve 中点**，
  所以 3 个点可以表示 4 个角。我的边级算法直接按 3 点算，
  漏掉了 1 个真实角点 → 横厚改不动（实测 82.0 而不是 70.1）。

⚠️ 但注意：**展开中点会改变点数，破坏 VF 一致性**。
  所以这个模块只用于**分析/测量**，不能用于产出字形。
  要真正改形，必须用「在原始点序列上模拟边」的方案：
  把隐式中点也当作虚拟顶点参与位移计算，但只写回真实点。
"""
from __future__ import annotations
import math


def expand_implied_points(coords, flags):
    """展开 TrueType 隐式中点，返回 [(x, y, on)]。仅用于分析。"""
    n = len(coords)
    if n == 0:
        return []
    out = []
    for i in range(n):
        x, y = coords[i]
        on = bool(flags[i] & 1)
        out.append((float(x), float(y), on))
        nxt = (i + 1) % n
        nx, ny = coords[nxt]
        non = bool(flags[nxt] & 1)
        # 两个连续 off => 中间有隐含 on 中点
        if not on and not non:
            out.append(((x + nx) / 2.0, (y + ny) / 2.0, True))
    return out


def count_real_vs_expanded(coords, flags):
    exp = expand_implied_points(coords, flags)
    return len(coords), len(exp)
