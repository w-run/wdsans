#!/usr/bin/env python3
"""GlyphModel.restore 与 ModelFilters 的 Python 移植。

JS 原版：
  src/glyph-manipulate/GlyphModel.js
  src/glyph-manipulate/ModelFilters.js
  src/font-build/glyph-filters.js（hanModelFilter 的组合顺序）

模型表示：
  onRefs      每个 on 点的"参考点"坐标
  onOffsets   每个 on 点相对参考点的偏移
  offOffsets  每个 off 点相对"前一个 on 点"的偏移
  offOnIndices 每个 off 点归属的 on 点索引
  onContourIndices 每个 on 点所属轮廓号
  xAlign/yAlign  需要对齐（取平均）的点组，元素形如 "on12" / "off7"
"""


def expand_align(s):
    on = s.startswith('on')
    return (on, int(s[2:] if on else s[3:]))


def set_coord_avg(axis, on_pts, off_pts, group):
    """把一组点的某个坐标取平均后写回。axis: 0=x, 1=y"""
    vals = []
    for on, idx in group:
        vals.append((on_pts if on else off_pts)[idx][axis])
    if not vals:
        return
    avg = sum(vals) / len(vals)
    for on, idx in group:
        (on_pts if on else off_pts)[idx][axis] = avg


def to_glyph(on_pts, off_pts, off_on_indices, on_contour_indices):
    """把 on/off 点序列还原成轮廓数组（每个点是 {'x','y','on'}）。"""
    contours = []
    cur = []
    off_i = 0
    for on_i, pt in enumerate(on_pts):
        if on_contour_indices[on_i] != len(contours):
            contours.append(cur)
            cur = []
        cur.append({'x': pt[0], 'y': pt[1], 'on': True})
        if off_i <= len(off_pts) - 1 and off_on_indices[off_i] == on_i:
            p1 = off_pts[off_i]
            p2 = off_pts[off_i + 1] if off_i + 1 < len(off_pts) else p1
            cur.append({'x': p1[0], 'y': p1[1], 'on': False})
            cur.append({'x': p2[0], 'y': p2[1], 'on': False})
            off_i += 2
    if cur:
        contours.append(cur)
    return contours


# ---------------- ModelFilters ----------------

def horizontal_scale(f):
    def _f(on_refs, on_offs, off_offs):
        return ([[p[0] * f, p[1]] for p in on_refs],
                on_offs,
                [[p[0] * f, p[1]] for p in off_offs])
    return _f


def weight_adjustment(f):
    def _f(on_refs, on_offs, off_offs):
        return (on_refs,
                [[p[0] * f, p[1] * f] for p in on_offs],
                off_offs)
    return _f


def contrast_adjustment(f):
    def _f(on_refs, on_offs, off_offs):
        return (on_refs,
                [[p[0] * f, p[1] * (2 - f)] for p in on_offs],
                off_offs)
    return _f


def radial_scale(xf, yf=None):
    yf = xf if yf is None else yf

    def _f(on_refs, on_offs, off_offs):
        return ([[(p[0] - 500) * xf + 500, (p[1] - 500) * yf + 500]
                 for p in on_refs], on_offs, off_offs)
    return _f


def counter_scale(factor):
    def f(x):
        if abs(x) < 0.25:
            return x
        return (1 if x > 0 else -1) * (abs(x) ** (2 - factor))

    def _f(on_refs, on_offs, off_offs):
        return ([[(f(p[0] / 500 - 1) + 1) * 500, p[1]] for p in on_refs],
                on_offs, off_offs)
    return _f


def gravity_adjustment(factor):
    def f(x):
        return (1 - (1 - x) ** factor) ** (1 / factor) if 0 < x < 1 else x

    def _f(on_refs, on_offs, off_offs):
        return ([[p[0], f(p[1] / 1000) * 1000] for p in on_refs],
                on_offs, off_offs)
    return _f


def soften(factor):
    def _f(on_refs, on_offs, off_offs):
        return (on_refs, on_offs,
                [[p[0] * factor, p[1] * factor] for p in off_offs])
    return _f


def translation(dx, dy):
    def _f(on_refs, on_offs, off_offs):
        return ([[p[0] + dx, p[1] + dy] for p in on_refs], on_offs, off_offs)
    return _f


def merge(*filters):
    def _f(a, b, c):
        for f in filters:
            a, b, c = f(a, b, c)
        return (a, b, c)
    return _f


def han_model_filter(param):
    """顺序必须与 JS 的 hanModelFilter 完全一致（非线性变换，顺序影响结果）"""
    return merge(
        horizontal_scale(param['width']),
        radial_scale(param['xtracking'], param['ytracking']),
        counter_scale(param['counter']),
        gravity_adjustment(param['gravity']),
        weight_adjustment(param['weight']),
        contrast_adjustment(param['contrast']),
        soften(param['softness']),
    )


def kana_model_filter(param):
    return merge(
        horizontal_scale(param['width']),
        radial_scale(param['xtracking'], param['ytracking']),
        weight_adjustment(param['weight']),
        contrast_adjustment(param['contrast']),
    )


# ---------------- restore ----------------

def restore(model, transform=None):
    """返回轮廓数组。transform 与 JS 一致：接收三个数组返回三个数组。"""
    on_refs = [[float(p[0]), float(p[1])] for p in model['onRefs']]
    on_offs = [[float(p[0]), float(p[1])] for p in model['onOffsets']]
    off_offs = [[float(p[0]), float(p[1])] for p in model['offOffsets']]

    if transform is not None:
        on_refs, on_offs, off_offs = transform(on_refs, on_offs, off_offs)

    on_pts = [[r[0] + o[0], r[1] + o[1]] for r, o in zip(on_refs, on_offs)]

    off_on = model['offOnIndices']
    off_pts = []
    for i, off in enumerate(off_offs):
        base = on_pts[off_on[i]]
        off_pts.append([base[0] + off[0], base[1] + off[1]])

    for group in model.get('xAlign') or []:
        g = [expand_align(s) for s in group]
        set_coord_avg(0, on_pts, off_pts, g)
    for group in model.get('yAlign') or []:
        g = [expand_align(s) for s in group]
        set_coord_avg(1, on_pts, off_pts, g)

    return to_glyph(on_pts, off_pts, off_on, model['onContourIndices'])
