"""去出脚（feet removal）—— 第 5 版判据（最终）。

判据演进（每一版都被实测推翻）：
  v1: 出脚 = 字形低于基线
      → 四字体都下探，OPPO 在甲/申/明 上反而更深
  v2: 出脚 = 细长竖条顶端突出
      → 明 c5 顶 778.99 = c0 顶 778.99，同高
  v3: 底横 = 外壳内任一宽扁条
      → 冒/昌/晶 内部横被误移，糊成黑块
  v4: 加「同一外壳只取最低那条」
      → 仍错，因为问题不在选哪条，而在外壳形状

v5 正确判据（关键洞察）：
  **外壳底部必须是开口的（⊓ 形），才存在"脚"。**

  口 shell c0 (8 点): 底边是两段短线 81 和 78（两条腿），宽 750
                       → 没有横跨全宽的底边 → 开口 → 有脚
  日 shell c0 (8 点): 底边 80 和 78，宽 656  → 开口 → 有脚
  昌 上部 shell c2 (4 点): 底边横跨全宽 606 → 已闭合 → 无脚，跳过

  这就是为什么「昌」上部不该动：它已经是闭合矩形，
  把内部横移到底部会撞上已有底边，糊成黑块。

做法：把底横整体下移，与外壳两腿底端齐平（纯平移，面积/点数/yMin 不变）。
"""
from __future__ import annotations

from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

_CJK_RANGES = (
    (0x3005, 0x3005),
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),
    (0xF900, 0xFAFF),
    (0x2E80, 0x2FDF),
    (0x20000, 0x3FFFF),
)


def is_cjk_cp(cp):
    return any(a <= cp <= b for a, b in _CJK_RANGES)


def cjk_glyph_names(font):
    return {name for cp, name in font.getBestCmap().items() if is_cjk_cp(cp)}


def seg_bbox(seg):
    xs = [p[0] for p in seg]
    ys = [p[1] for p in seg]
    return min(xs), min(ys), max(xs), max(ys)


def _has_full_bottom_edge(seg, tol=3.0, span_ratio=0.5):
    """外壳底部是否有横跨全宽的水平边（= 已闭合，无脚）。"""
    n = len(seg)
    x0, y0, x1, y1 = seg_bbox(seg)
    width = x1 - x0
    if width <= 0:
        return True
    for i in range(n):
        ax, ay = seg[i]
        bx, by = seg[(i + 1) % n]
        if abs(by - ay) > tol:
            continue
        ey = (ay + by) / 2
        if ey > y0 + (y1 - y0) * 0.30:
            continue          # 只看底部 30%区域内的水平边
        if abs(bx - ax) > width * span_ratio:
            return True       # 底边横跨超一半 → 已闭合
    return False


def find_feet(segs, min_gap=18.0, max_gap=140.0):
    """返回 [(bar_idx, drop)]。"""
    boxes = [seg_bbox(s) if len(s) >= 3 else None for s in segs]
    out = []
    for i, b in enumerate(boxes):
        if b is None:
            continue
        x0, y0, x1, y1 = b
        w, h = x1 - x0, y1 - y0
        if w <= 0 or h <= 0 or w < h * 1.8:
            continue                      # 只处理宽扁条
        best = None
        for j, o in enumerate(boxes):
            if j == i or o is None:
                continue
            a0, b0, a1, b1 = o
            if not (a0 - 2 <= x0 and x1 <= a1 + 2):
                continue                  # bar 的 x 要被 shell 包含
            if (b1 - b0) < h * 2.5:
                continue                  # shell 要够高
            if y1 > b0 + (b1 - b0) * 0.62:
                continue                  # bar 要在 shell 下半部
            if _has_full_bottom_edge(segs[j]):
                continue                  # ★ 外壳已闭合 → 无脚
            gap = y0 - b0
            if min_gap <= gap <= max_gap:
                if best is None or gap > best:
                    best = gap
        if best is not None:
            out.append((i, best))
    return out


def shift_seg(seg, dy):
    return [(x, y + dy) for (x, y) in seg]


def _commit(g, pts):
    gc = GlyphCoordinates([(int(round(x)), int(round(y))) for x, y in pts])
    gc.toInt()
    g.coordinates = gc
    for a in ("xMin", "yMin", "xMax", "yMax"):
        if hasattr(g, a):
            delattr(g, a)


def remove_feet(font, dry_run=False, only_cjk=True):
    from .thinning import split_contours
    glyf = font["glyf"]
    allowed = cjk_glyph_names(font) if only_cjk else None
    n_glyph = n_bar = 0
    detail = []
    for name in font.getGlyphOrder():
        if allowed is not None and name not in allowed:
            continue
        g = glyf[name]
        if g.numberOfContours <= 0:
            continue
        segs = split_contours(g)
        feet = find_feet(segs)
        if not feet:
            continue
        n_glyph += 1
        n_bar += len(feet)
        if len(detail) < 25:
            detail.append((name, [(i, round(d, 1)) for i, d in feet]))
        if dry_run:
            continue
        new = list(segs)
        for i, drop in feet:
            new[i] = shift_seg(segs[i], -drop)
        flat = [p for sl in new for p in sl]
        assert len(flat) == sum(len(sl) for sl in segs), name
        _commit(g, flat)
    return n_glyph, n_bar, detail
