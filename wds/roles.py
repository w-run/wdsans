"""笔画角色识别 v2 —— 基于实测几何，不用 glow 的固定阈值。

P0 版本的错误（已实测确认）：
  1. 笔画宽度用 bbox 短边估 → 「口」量出 375（真实约 80）
  2. 折角判据没区分「笔画端面」与「转折」→ 「口」量出 12 个折角（真实 4 个）

v2 的判据来源：「一」「丨」「口」「十」的实测结构（Noto/OPPO 双字体对照）：
  - 「一」= 单轮廓矩形 4 点，横厚 = |y1-y2|
  - 「丨」= 单轮廓矩形 4 点，竖宽 = |x1-x2|
  - 「口」= 外轮廓 8 点，端面落在侧壁，四个内角是转折
  - 端面（stroke end）= 两条几乎平行的短边之间夹一段「宽度约等于笔画厚」的短边
"""
from __future__ import annotations
import math


def _d(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def _turn_deg(prev, cur, nxt):
    """在 cur 处的转向角（0 = 直行，90 = 直角）。"""
    v1x, v1y = cur.x - prev.x, cur.y - prev.y
    v2x, v2y = nxt.x - cur.x, nxt.y - cur.y
    n1 = math.hypot(v1x, v1y)
    n2 = math.hypot(v2x, v2y)
    if n1 < 1e-9 or n2 < 1e-9:
        return 0.0
    c = max(-1.0, min(1.0, (v1x * v2x + v1y * v2y) / (n1 * n2)))
    return math.degrees(math.acos(c))


def contour_bbox(c):
    xs = [p.x for p in c]
    ys = [p.y for p in c]
    return min(xs), min(ys), max(xs), max(ys)


def is_rect(c, tol=1.0):
    """单轮廓是否轴对齐矩形（4 点，「一」「丨」这种）。"""
    if len(c) != 4 or not all(p.on for p in c):
        return False
    for i in range(4):
        p, q = c[i], c[(i + 1) % 4]
        # 只允许水平或垂直边
        if abs(p.x - q.x) > tol and abs(p.y - q.y) > tol:
            return False
    return True


def rect_thickness(c):
    """矩形轮廓的笔画厚度：短边长度。"""
    x0, y0, x1, y1 = contour_bbox(c)
    return min(x1 - x0, y1 - y0)


def find_corners(c, min_turn=60.0):
    """真转折点：跳过共线点后，转向角 >= min_turn。

    「口」的 8 点轮廓里，4 个角是 90 度转向，其余点是端面/共线点。
    """
    n = len(c)
    out = []
    for i in range(n):
        prev, cur, nxt = c[(i - 1) % n], c[i], c[(i + 1) % n]
        # 共线点跳过（短边或几乎不转向）
        if _d(prev, cur) < 1e-6 or _d(cur, nxt) < 1e-6:
            continue
        t = _turn_deg(prev, cur, nxt)
        if t >= min_turn:
            out.append((i, round(t, 1)))
    return out


def find_ends(c, stroke_w, ratio=1.6):
    """笔画端面：转向角约 90 度、且一侧边长 ≈ 笔画厚度。

    与 glow 的 detect-ends 区别：不用「on/off 交替」这种依赖曲线表达的判据，
    改用「长度 ≈ 笔画厚」这个几何不变量 —— 对直线和曲线一视同仁。
    """
    n = len(c)
    out = []
    for i in range(n):
        prev, cur, nxt = c[(i - 1) % n], c[i], c[(i + 1) % n]
        e1, e2 = _d(prev, cur), _d(cur, nxt)
        if e1 < 1e-6 or e2 < 1e-6:
            continue
        t = _turn_deg(prev, cur, nxt)
        if abs(t - 90.0) > 20.0:
            continue
        # 至少一侧边 ≈ 笔画厚度 → 这是端面的两个角
        if min(e1, e2) <= stroke_w * ratio:
            out.append((i, round(min(e1, e2), 1)))
    return out


def stroke_width_from_skeleton(contours):
    """从矩形轮廓直接量笔画厚度（最可靠的方式）。

    对「一」「丨」这种单矩形：短边即厚度。
    对含矩形的多轮廓字：取所有矩形短边的中位数。
    兜底：用全字 bbox 的 1/12（经验值，仅当没有任何矩形轮廓）。
    """
    widths = []
    for c in contours:
        if is_rect(c):
            w = rect_thickness(c)
            if 5 < w < 250:
                widths.append(w)
    if widths:
        widths.sort()
        return widths[len(widths) // 2]
    # 兜底
    xs = [p.x for c in contours for p in c]
    ys = [p.y for c in contours for p in c]
    if not xs:
        return 50.0
    return max(10.0, min(max(xs) - min(xs), max(ys) - min(ys)) / 12.0)


def analyze(contours):
    sw = stroke_width_from_skeleton(contours)
    out = {"stroke_width": round(sw, 1), "contours": []}
    for ci, c in enumerate(contours):
        info = {
            "index": ci,
            "n_points": len(c),
            "rect": is_rect(c),
            "corners": find_corners(c),
            "ends": find_ends(c, sw),
        }
        if info["rect"]:
            info["thickness"] = round(rect_thickness(c), 1)
            info["bbox"] = [round(v, 1) for v in contour_bbox(c)]
        out["contours"].append(info)
    return out
