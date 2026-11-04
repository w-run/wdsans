"""去出脚（feet removal）。

判据来源（口 uni2F1D，400 字重，逐点实测）：
  Noto c0(8pts): ⊓ 外壳，两竖腿伸到 y=-55/-51
       c1(4pts): 独立底横 y 30..107
       → 竖腿比底横下沿低约 85 = 出脚
  OPPO c0(4pts): 完整外框，底边 y=-37（底横就在最底，平底）
  HOS  c0(8pts): 腿到 -58，底横下沿 35 → 出脚 93

做法：把独立底横整体下移，使其下沿与外壳竖腿底端齐平。
纯平移 → 面积不变、点数不变、VF 安全、字形 yMin 不变。

⚠️ 适用范围限制（实测教训）：
  该判据只对**汉字部件**成立。
  实测 U+1107（谚文字母）的 8点外壳+4点内条 会被误判，下移 67；
  结果谚文/假名/拉丁出现 12~25% 像素改动、位移达 97px。
  所以必须限制在 CJK 统一表意文字区（URO + Ext-A + 兼容区）。
"""
from __future__ import annotations

from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

# CJK 统一表意文字（含扩展 A、兼容表意、康熙部首）
_CJK_RANGES = (
    (0x3005, 0x3005),   # 々
    (0x3400, 0x4DBF),   # Ext-A
    (0x4E00, 0x9FFF),   # URO
    (0xF900, 0xFAFF),   # 兼容表意
    (0x2E80, 0x2FDF),   # 康熙部首 / 部首补充
    (0x20000, 0x3FFFF), # Ext-B 及以后
)


def is_cjk_cp(cp):
    return any(a <= cp <= b for a, b in _CJK_RANGES)


def cjk_glyph_names(font):
    """返回属于 CJK 表意文字的字形名集合。"""
    out = set()
    for cp, name in font.getBestCmap().items():
        if is_cjk_cp(cp):
            out.add(name)
    return out


def seg_bbox(seg):
    xs = [p[0] for p in seg]
    ys = [p[1] for p in seg]
    return min(xs), min(ys), max(xs), max(ys)


def find_feet(segs, min_gap=18.0, max_gap=140.0):
    """返回 [(bar_idx, drop)] —— 需要下移的底横轮廓。"""
    boxes = [seg_bbox(s) if len(s) >= 3 else None for s in segs]
    out = []
    for i, b in enumerate(boxes):
        if b is None:
            continue
        x0, y0, x1, y1 = b
        w, h = x1 - x0, y1 - y0
        if w <= 0 or h <= 0 or w < h * 1.8:
            continue
        best = None
        for j, o in enumerate(boxes):
            if j == i or o is None:
                continue
            a0, b0, a1, b1 = o
            if not (a0 - 2 <= x0 and x1 <= a1 + 2):
                continue
            if (b1 - b0) < h * 2.5:
                continue
            if y1 > b0 + (b1 - b0) * 0.62:
                continue
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
    """去出脚。only_cjk=True 时只处理汉字区，避免误伤谚文/假名/拉丁。"""
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
