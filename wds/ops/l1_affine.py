"""L1 全局仿射 + L2 字面/中宫算子。

设计依据（实测，DESIGN §4.2 / PARAMS §3.3）：
  目标：字面 884×880（比 Noto 略收一圈），墨密度 0.430（Noto 0.440 → 略降）
  手法：**收字面 + 减细笔画**两条腿走路，不能只靠缩字面

关键：所有算子只改 delta，不改点数。
"""
from __future__ import annotations
import math

CX, CY = 500.0, 500.0


def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def face_scale(sx, sy, cx=CX, cy=CY):
    """字面整体缩放（相对字面中心）。

    这是「字身收窄」的实现：字占的地方变小，字与字之间留白变多，
    但每个字本身不变形。
    """
    def fn(deltas):
        return [((dx) * sx, (dy) * sy) for dx, dy in deltas]
    return fn


def radial_scale(s, cx=CX, cy=CY):
    """径向缩放（相对字面中心的等比放大/缩小）。"""
    return face_scale(s, s, cx, cy)


def translate(dx, dy):
    """整体平移（delta 不变，用于调整字面上下位置）。"""
    def fn(deltas):
        return deltas
    return fn


def vertical_bias(k):
    """重心微调：y 方向的线性偏置，保持基线与字顶不动。

    用于「视觉重心 y=512」这类目标。作用在 delta 上是乘法，
    因为 delta 本身刻画了字重间的变化方向。
    """
    def fn(deltas):
        return [(dx, dy * k) for dx, dy in deltas]
    return fn


def lerp(a, b, t):
    return a + (b - a) * t


def weight_curve(wght, base=400, k=1.0):
    """按字重给一个温和的笔画粗细系数。

    只作用于 delta 的放大缩小，因此不会破坏拓扑。
    曲线：以 base 为 1.0，向两端平滑变化。
    """
    return 1.0 + k * math.tanh((wght - base) / 260.0)
