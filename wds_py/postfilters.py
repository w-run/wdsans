#!/usr/bin/env python3
"""PostFilters 的 Python 移植：端点处理（去脚 / 钩张力 / 末端压平 / 点软化）。

来源：
  src/utils/point-math.js
  src/glyph-manipulate/detect-feet.js
  src/glyph-manipulate/detect-ends.js
  src/glyph-manipulate/PostFilters.js

这一层决定「出脚 / 喇叭口 / 凹陷」三项硬指标，几何判定必须与 JS 完全一致。
"""
import math


# ---------------- point math ----------------

def clone_glyph(g):
    """浅拷贝字形：点只有 x/y/on 三个标量，deepcopy 慢 30 倍"""
    return [[{'x': p['x'], 'y': p['y'], 'on': p['on']} for p in c] for c in g]


def clone_contour(c):
    return [{'x': p['x'], 'y': p['y'], 'on': p['on']} for p in c]


def mod(n, m):
    # Python 的 % 对负数同样返回非负值，与 JS 的 ((n%m)+m)%m 等价，省一次运算
    return n % m


def dot(v1, v2):
    return v1[0] * v2[0] + v1[1] * v2[1]


def outer(v1, v2):
    return v1[0] * v2[1] - v2[0] * v1[1]


def norm(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1])


def add(v1, v2):
    return (v1[0] + v2[0], v1[1] + v2[1])


def sub(v1, v2):
    return (v1[0] - v2[0], v1[1] - v2[1])


def mul(s, v):
    return (s * v[0], s * v[1])


def rad2deg(r):
    return r / math.pi * 180


def angle(pt1, pt2, pt3):
    """pt2 为顶点，返回逆时针夹角（弧度）。"""
    v1 = sub(pt1, pt2)
    v2 = sub(pt3, pt2)
    n1, n2 = norm(v1), norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    c = max(-1.0, min(1.0, dot(v1, v2) / (n1 * n2)))
    convex = math.acos(c)
    return convex if outer(v1, v2) > 0 else 2 * math.pi - convex


def dist(p1, p2):
    return norm(sub(p1, p2))


def projection(pt, l1, l2):
    p = sub(pt, l1)
    q = sub(l2, l1)
    if q[0] == 0 and q[1] == 0:
        return (l1[0], l1[1])
    return add(l1, mul(dot(p, q) / dot(q, q), q))


def tp(pt):
    return (pt['x'], pt['y'])


# ---------------- detect feet ----------------

def is_left_foot(pt, max_stroke=10, longest_foot=50, angle_tol=2):
    """pt 是 7 个连续点 [pt1..pt7]"""
    pt1, pt2, pt3, pt4, pt5, pt6, pt7 = pt[:7]

    def approx(a1, a2):
        return abs(a1 - a2) < angle_tol

    if not (pt1['on'] and pt2['on'] and pt3['on'] and pt4['on'] and pt5['on']):
        return False
    if not (pt1['y'] > pt2['y']):
        return False
    if abs(pt1['x'] - pt2['x']) > 20:
        return False
    if not approx(rad2deg(angle(tp(pt3), tp(pt2), tp(pt1))), 90):
        return False
    if not approx(rad2deg(angle(tp(pt4), tp(pt3), tp(pt2))), 90):
        return False
    if not approx(rad2deg(angle(tp(pt5), tp(pt4), tp(pt3))), 270):
        return False
    if dist(tp(pt3), tp(pt4)) > longest_foot:
        return False
    if dist(tp(pt2), tp(pt3)) > max_stroke:
        return False
    if pt1['y'] - pt4['y'] < 1.5 * max_stroke:
        return False
    # 「月」的情形
    if pt6['on'] and not pt7['on'] and pt6['y'] < pt5['y'] \
            and pt6['y'] > pt2['y'] and pt7['x'] <= pt5['x'] + 10:
        return False
    # 「非」的情形
    if pt7['y'] > pt4['y'] and pt7['y'] - pt4['y'] < max_stroke:
        return False
    if pt4['y'] > 750:
        return False
    return True


def detect_feet(contour, max_stroke=10, longest_foot=100, angle_tol=2):
    left, right = [], []
    n = len(contour)
    for i in range(n):
        pts = [contour[(i + k) % n] for k in range(7)]
        if is_left_foot(pts, max_stroke, longest_foot, angle_tol):
            left.append(mod(i + 1, n))
        mirrored = [{'x': 1000 - p['x'], 'y': p['y'], 'on': p['on']}
                    for p in reversed(pts)]
        if is_left_foot(mirrored, max_stroke, longest_foot, angle_tol):
            right.append(mod(i + 5, n))
    return left, right


# ---------------- detect ends ----------------

def is_end(pt, max_stroke=10, angle_tol=20):
    pt1, pt2, pt3, pt4, pt5, pt6 = pt[:6]

    def approx(a1, a2):
        return abs(a1 - a2) < angle_tol

    if pt1['on'] or not pt2['on'] or pt3['on'] or pt4['on'] \
            or not pt5['on'] or pt6['on']:
        return False
    if dist(tp(pt2), tp(pt5)) > max_stroke * 1.4:
        return False
    a1 = rad2deg(angle(tp(pt5), tp(pt2), tp(pt1)))
    a2 = rad2deg(angle(tp(pt6), tp(pt5), tp(pt2)))
    return approx(a1 + a2, 160)


def detect_ends(contour, max_stroke=10, angle_tol=20):
    n = len(contour)
    out = []
    for i in range(n):
        pts = [contour[mod(i + k, n)] for k in range(6)]
        if is_end(pts, max_stroke, angle_tol):
            out.append(mod(i + 1, n))
    return out


# ---------------- feet removal ----------------

def feet_lengths(contour, left, right):
    n = len(contour)
    ll = [contour[mod(i + 2, n)]['y'] - contour[i]['y'] for i in left]
    rl = [contour[mod(i - 2, n)]['y'] - contour[i]['y'] for i in right]
    return ll, rl


def remove_contour_feet(contour, left, right):
    n = len(contour)
    stage = []
    for i, pt in enumerate(contour):
        if i in left:
            stage.append({'x': pt['x'], 'y': contour[mod(i + 2, n)]['y'],
                          'on': pt['on']})
        elif i in right:
            stage.append({'x': pt['x'], 'y': contour[mod(i - 2, n)]['y'],
                          'on': pt['on']})
        else:
            stage.append(dict(pt))
    out = []
    for i, pt in enumerate(stage):
        if mod(i - 1, n) in left or mod(i - 2, n) in left:
            continue
        if mod(i + 1, n) in right or mod(i + 2, n) in right:
            continue
        out.append(pt)
    return out


def update_feet_indices(contour, left, right):
    n = len(contour)
    removed = []
    for i in left:
        removed += [mod(i + 1, n), mod(i + 2, n)]
    for i in right:
        removed += [mod(i - 1, n), mod(i - 2, n)]
    removed.sort()
    index_map = []
    k = 0
    for i in range(n):
        if i in removed:
            k += 1
        index_map.append(i - k)
    return [index_map[i] for i in left], [index_map[i] for i in right]


def search_in_glyph(glyph, xmin, xmax, ymin, ymax):
    res = []
    for cid, contour in enumerate(glyph):
        for pid, pt in enumerate(contour):
            if xmin <= pt['x'] <= xmax and ymin <= pt['y'] <= ymax:
                res.append((cid, pid))
    return res


def sink_feet(glyph, gleft, gright, glen, grlen, max_stroke=10, sink_ratio=0.25):
    to_sink, lengths = [], []
    for i, (cid, pid) in enumerate(gleft):
        lpt = glyph[cid][pid]
        rpt = glyph[cid][mod(pid + 1, len(glyph[cid]))]
        if abs(lpt['y'] - rpt['y']) <= 1:
            to_sink.append((cid, pid))
            lengths.append(glen[i])
    for i, (cid, pid) in enumerate(gright):
        lp = mod(pid - 1, len(glyph[cid]))
        lpt = glyph[cid][lp]
        rpt = glyph[cid][pid]
        if abs(lpt['y'] - rpt['y']) > 1:
            continue
        if (cid, lp) in to_sink:
            continue
        to_sink.append((cid, lp))
        lengths.append(grlen[i])

    result = clone_glyph(glyph)
    for i, (cid, pid) in enumerate(to_sink):
        lpt = result[cid][pid]
        rpt = result[cid][mod(pid + 1, len(result[cid]))]
        found = search_in_glyph(result, lpt['x'], rpt['x'],
                                lpt['y'] + 2, lpt['y'] + max_stroke)
        if not found:
            lpt['y'] -= lengths[i] * sink_ratio
            rpt['y'] -= lengths[i] * sink_ratio
            continue
        min_y = min(result[ci][pi]['y'] for ci, pi in found)
        found = [(ci, pi) for ci, pi in found
                 if abs(result[ci][pi]['y'] - min_y) <= 1]
        for ci, pi in found:
            result[ci][pi]['y'] -= lengths[i] * sink_ratio
        lpt['y'] -= lengths[i] * sink_ratio
        rpt['y'] -= lengths[i] * sink_ratio
    return result


def remove_feet(glyph, max_stroke=10, longest_foot=100, angle_tol=2):
    gleft, gright, glen, grlen = [], [], [], []
    stages = []
    for cid, contour in enumerate(glyph):
        left, right = detect_feet(contour, max_stroke, longest_foot, angle_tol)
        stages.append(remove_contour_feet(contour, left, right))
        ll, rl = feet_lengths(contour, left, right)
        left, right = update_feet_indices(contour, left, right)
        gleft += [(cid, p) for p in left]
        gright += [(cid, p) for p in right]
        glen += ll
        grlen += rl
    return sink_feet(stages, gleft, gright, glen, grlen, max_stroke)


# ---------------- stroke ends flatten ----------------

def target_points(contour, end):
    n = len(contour)
    pt1 = tp(contour[mod(end - 1, n)])
    pt2 = tp(contour[end])
    pt5 = tp(contour[mod(end + 3, n)])
    pt6 = tp(contour[mod(end + 4, n)])
    pt2_proj = projection(pt2, pt5, pt6)
    pt5_proj = projection(pt5, pt2, pt1)
    tp20 = add(mul(0.5, pt5_proj), mul(0.5, pt2))
    tp50 = add(mul(0.5, pt2_proj), mul(0.5, pt5))
    r = 0
    tp2n = add(mul(1 - r, tp20), mul(r, tp50))
    tp5n = add(mul(1 - r, tp50), mul(r, tp20))
    tp3 = add(mul(0.3, tp2n), mul(0.7, tp5n))
    tp4 = add(mul(0.7, tp2n), mul(0.3, tp5n))
    return tp2n, tp3, tp4, tp5n


def stroke_ends_flatten(glyph, ratio, remove_off_pts=False,
                        max_stroke=10, angle_tol=20):
    out = []
    for contour in glyph:
        ends = detect_ends(contour, max_stroke, angle_tol)
        targets = {}
        n = len(contour)
        for e in ends:
            t2, t3, t4, t5 = target_points(contour, e)
            targets[e] = t2
            targets[mod(e + 1, n)] = t3
            targets[mod(e + 2, n)] = t4
            targets[mod(e + 3, n)] = t5
        res = []
        for i, pt in enumerate(contour):
            if i not in targets:
                res.append(dict(pt))
                continue
            if remove_off_pts and not pt['on']:
                continue
            p = tp(pt)
            pr = add(mul(1 - ratio, p), mul(ratio, targets[i]))
            res.append({'x': pr[0], 'y': pr[1], 'on': pt['on']})
        out.append(res)
    return out


# ---------------- dots ----------------

def is_dot(contour, max_stroke):
    if len(contour) != 8:
        return False
    if contour[1]['on']:
        ok = (not contour[2]['on'] and not contour[3]['on'] and contour[4]['on']
              and contour[5]['on'] and not contour[6]['on']
              and not contour[7]['on'])
        nearest = contour[1]
    elif contour[7]['on']:
        ok = (not contour[1]['on'] and not contour[2]['on']
              and contour[3]['on'] and contour[4]['on']
              and not contour[5]['on'] and not contour[6]['on'])
        nearest = contour[7]
    else:
        return False
    if not ok:
        return False
    return (dist(tp(contour[0]), tp(nearest)) < max_stroke
            and rad2deg(angle(tp(contour[2]), tp(contour[1]),
                              tp(contour[0]))) < 180)


def dot_off_target(contour, off_index):
    n = len(contour)
    if contour[mod(off_index - 1, n)]['on']:
        prev = tp(contour[mod(off_index - 1, n)])
    else:
        prev = tp(contour[mod(off_index - 2, n)])
    if contour[mod(off_index + 1, n)]['on']:
        nxt = tp(contour[mod(off_index + 1, n)])
    else:
        nxt = tp(contour[mod(off_index + 2, n)])
    return projection(tp(contour[off_index]), prev, nxt)


def soften_dots(glyph, value, max_stroke=10):
    out = []
    for contour in glyph:
        if not is_dot(contour, max_stroke):
            out.append(contour)
            continue
        res = []
        for i, pt in enumerate(contour):
            if pt['on']:
                res.append(dict(pt))
                continue
            t = dot_off_target(contour, i)
            p = tp(pt)
            r = add(mul(value, p), mul(1 - value, t))
            res.append({'x': r[0], 'y': r[1], 'on': False})
        out.append(res)
    return out


# ---------------- hook tension ----------------

def is_hook(p1, p2, p3, p4, p5, p6):
    if p1['on'] or p2['on'] or not p3['on'] or not p4['on'] \
            or p5['on'] or p6['on']:
        return False
    if abs(p3['y'] - p2['y']) > 1 or abs(p4['y'] - p3['y']) > 1 \
            or abs(p5['y'] - p4['y']) > 1:
        return False
    return p1['y'] > p2['y'] and p6['y'] > p5['y']


def hook_tension(glyph, ratio):
    out = []
    for contour in glyph:
        res = clone_contour(contour)
        n = len(res)
        for i in range(n):
            pts = [res[mod(i + k, n)] for k in range(6)]
            if is_hook(*pts):
                cx = (pts[2]['x'] + pts[3]['x']) / 2
                pts[2]['x'] = pts[2]['x'] * (1 - ratio) + cx * ratio
                pts[3]['x'] = pts[3]['x'] * (1 - ratio) + cx * ratio
        out.append(res)
    return out


# ---------------- basics ----------------

def translation(glyph, dx, dy):
    return [[{'x': p['x'] + dx, 'y': p['y'] + dy, 'on': p['on']}
             for p in c] for c in glyph]


def scaling(glyph, xr, yr=None):
    yr = xr if yr is None else yr
    return [[{'x': p['x'] * xr, 'y': p['y'] * yr, 'on': p['on']}
             for p in c] for c in glyph]


def round_glyph(glyph):
    return [[{'x': round(p['x']), 'y': round(p['y']), 'on': p['on']}
             for p in c] for c in glyph]


def merge(*filters):
    def _f(g):
        for f in filters:
            g = f(g)
        return g
    return _f


def han_post_filter(param, apply_feet=True):
    """与 JS 的 hanPostFilter 保持一致的处理顺序"""
    v = param['vstroke']
    h = param['hstroke']
    chain = []
    if param.get('feetremoval') and apply_feet:
        chain.append(lambda g: remove_feet(g, max_stroke=v * 1.5,
                                           longest_foot=110))
    chain.append(lambda g: hook_tension(g, param['hooktension']))
    chain.append(lambda g: stroke_ends_flatten(
        g, param['flattenends'], bool(param.get('endsremoval')),
        max_stroke=h * 1.5))
    chain.append(lambda g: soften_dots(g, param['dotsoftness'],
                                       max_stroke=h * 1.5))
    return merge(*chain)
