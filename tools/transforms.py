"""WDesign Sans · 形变算子

全部算子的共同约束：**只移动节点，不增删节点**。
输入输出都是 RecordingPen 的值（(op, args) 列表），拓扑保证不变。

坐标系：基线 y=0，字身 1000×1000，字形中心 (500, 500)。
"""
import math

# ---------------------------------------------------------------- 基础工具

def _xy(pt):
    return float(pt[0]), float(pt[1])


def map_points(value, fn):
    """对所有坐标点应用同一个函数 fn(x, y) -> (x, y)。"""
    out = []
    for op, args in value:
        if op == "closePath":
            out.append((op, args))
        else:
            out.append((op, tuple(fn(*_xy(p)) for p in args)))
    return out


def bbox(value):
    xs, ys = [], []
    for op, args in value:
        for p in args:
            xs.append(p[0]); ys.append(p[1])
    if not xs:
        return (0, 0, 0, 0)
    return (min(xs), min(ys), max(xs), max(ys))


# ---------------------------------------------------------------- 算子

def face_scale(value, target_w=880, target_h=880, min_scale=0.80, max_scale=1.20):
    """字面率归一：把字形 bbox 缩放到目标宽高，中心对齐字形中心。

    这是「字面」控制，不是「中宫」控制。它会同时缩放笔画粗细，
    所以真实管线里必须与 stroke_compensate 配对使用。
    """
    x0, y0, x1, y1 = bbox(value)
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return value
    sx = target_w / w
    sy = target_h / h
    sx = max(min_scale, min(max_scale, sx))
    sy = max(min_scale, min(max_scale, sy))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    def fn(x, y):
        return ((x - cx) * sx + 500, (y - cy) * sy + 500)

    return map_points(value, fn)


def gravity_warp(value, strength=0.0):
    """重心调整：在字形自身 y 范围内做单调重映射，上下端点保持不动。

    t' = t^(1-strength)，t 为归一化的纵向位置。
    strength > 0 抬高重心（上半拉伸、下半压缩），< 0 反之。
    """
    if abs(strength) < 1e-6:
        return value
    _, y0, _, y1 = bbox(value)
    h = y1 - y0
    if h <= 0:
        return value
    gamma = 1.0 - strength

    def fn(x, y):
        t = (y - y0) / h
        t = max(0.0, min(1.0, t))
        return (x, y0 + (t ** gamma) * h)

    return map_points(value, fn)


def center_spread(value, factor=1.0, cx=500.0, cy=460.0):
    """中宫松散：径向外推，**字面（外框）保持不变**。

    归一化半径 r ∈ [0,1]，映射 r' = r * (1 + k*(1-r))，k = factor-1。
    中心区域位移最大，外缘位移为零 —— 所以 bbox 不变，只有内部留白变大。
    这是「中宫」和「字面」的关键区别：松 ≠ 大。
    """
    k = factor - 1.0
    if abs(k) < 1e-6:
        return value
    x0, y0, x1, y1 = bbox(value)
    R = max(abs(x1 - cx), abs(cx - x0), abs(y1 - cy), abs(cy - y0)) or 1.0

    def fn(x, y):
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy) / R
        if r < 1e-9:
            return (x, y)
        scale = 1.0 + k * max(0.0, 1.0 - r)
        return (cx + dx * scale, cy + dy * scale)

    return map_points(value, fn)


def stroke_offset(value, delta=0.0, deadzone=0.12):
    """笔画加粗/减细：沿节点法线方向位移。

    delta 单位为设计单位（1000 em）。deadzone 用于抑制转折点的过度外扩。
    """
    if abs(delta) < 1e-6:
        return value

    out = []
    contour = []

    def flush():
        if len(contour) >= 3:
            n = len(contour)
            for i, (op, args, idx) in enumerate(contour):
                px, py = args[idx]
                # 用相邻点的差分方向估算外法线
                prev = contour[(i - 1) % n][1][contour[(i - 1) % n][2]]
                nxt = contour[(i + 1) % n][1][contour[(i + 1) % n][2]]
                tx, ty = nxt[0] - prev[0], nxt[1] - prev[1]
                ln = math.hypot(tx, ty) or 1.0
                nx, ny = ty / ln, -tx / ln
                new = (px + nx * delta, py + ny * delta)
                contour[i] = (op, tuple(new if j == idx else p for j, p in enumerate(args)), idx)

    for op, args in value:
        if op == "closePath":
            flush()
            out.extend([(o, a) for o, a, _ in contour])
            contour = []
            out.append((op, args))
            continue
        if not args:
            out.append((op, args)); continue
        for idx in range(len(args)):
            contour.append((op, args, idx))
    if contour:
        flush()
        out.extend([(o, a) for o, a, _ in contour])
    return out


# ---------------------------------------------------------------- 组合

PIPELINE = {
    # 名字: (函数, 参数)
    "face": face_scale,
    "gravity": gravity_warp,
    "spread": center_spread,
    "stroke": stroke_offset,
}


def soften(value, tension=1.0):
    """笔画软硬：调整曲线控制点的「张力」（= 控制点离 on 点的距离比例）。

    tension = 1.0 保持原样；< 1 曲线变直变硬；> 1 曲线变饱满变软。
    只移动已有控制点，不增删节点 —— VF 安全。

    这是与旧版 `softness: 0.85` 对应的算子，但语义是**乘数**而不是收缩量：
    旧版 0.85 ≈ 本算子的 tension=0.85。
    """
    if abs(tension - 1.0) < 1e-9:
        return value

    out = []
    last_on = None  # 上一个闭合轮廓的当前 on 点
    i = 0
    n = len(value)
    while i < n:
        op, args = value[i]
        if op in ("moveTo", "lineTo"):
            last_on = args[0]
            out.append((op, args))
            i += 1
        elif op == "curveTo":
            p1, p2, p3 = args
            p0 = last_on if last_on is not None else (0.0, 0.0)
            n1 = (p0[0] + (p1[0] - p0[0]) * tension,
                  p0[1] + (p1[1] - p0[1]) * tension)
            n2 = (p3[0] + (p2[0] - p3[0]) * tension,
                  p3[1] + (p2[1] - p3[1]) * tension)
            out.append((op, (n1, n2, p3)))
            last_on = p3
            i += 1
        else:
            out.append((op, args))
            i += 1
    return out


def cap_angle(value, angle_hv=0.0, angle_diag=4.0, stroke_width=82.0,
              max_cap_ratio=1.6, min_edge_ratio=1.6, collinear_dot=0.985,
              max_move_ratio=1.2):
    """端面处理：把笔画端面收成一条直线，并按笔画方向给不同倾斜角。

    angle_hv   : 横画 / 竖画端面的倾斜角（度），**默认 0 = 严格垂直**
    angle_diag : 斜笔画（撇捺点）端面的倾斜角（度）

    检测方式：端面 = 一段**连续短边**（可能由多段拼成），两端连着两条
    **近似反向平行的长边**。转角处前后边互相垂直，不会被误判。

    关键：整段端面上的**所有节点**一起投影到目标直线，
    否则端面中间的点不动，会形成「凹陷」。
    """
    contours = _split_contours(value)
    out = []
    for kind, start, segs in contours:
        ops = [op for op, _ in segs]
        n = len(segs)
        if n < 3 or all(o != "lineTo" for o in ops):
            out.extend(_rebuild(kind, start, segs))
            continue

        P = [start] + [args[-1] for _, args in segs]
        m = n + 1
        eop = [ops[k] if k < n else "lineTo" for k in range(m)]   # 闭合边视为直线
        elen = [math.hypot(P[(k + 1) % m][0] - P[k][0], P[(k + 1) % m][1] - P[k][1])
                for k in range(m)]
        edir = [_norm(P[(k + 1) % m][0] - P[k][0], P[(k + 1) % m][1] - P[k][1])
                for k in range(m)]

        def is_short(k):
            return eop[k] == "lineTo" and 1e-6 < elen[k] <= stroke_width * max_cap_ratio

        moved = {}
        visited = set()
        for k0 in range(m):
            if k0 in visited or not is_short(k0):
                continue
            # 向后扩展：连续短边且共线
            run = [k0]
            k = k0
            while True:
                nk = (k + 1) % m
                if nk == k0 or nk in run or not is_short(nk):
                    break
                cross = abs(edir[k][0] * edir[nk][1] - edir[k][1] * edir[nk][0])
                if cross > (1 - collinear_dot) ** 0.5 * 3:
                    break
                run.append(nk); k = nk
            if len(run) < 1:
                continue
            # 首尾两条相邻长边
            before = (run[0] - 1) % m
            after = (run[-1] + 1) % m
            if before in run or after in run:
                continue
            # 相邻长边允许是曲线段：用弦长与弦方向近似
            L = sum(elen[i] for i in run)
            if L > stroke_width * max_cap_ratio:
                continue
            if min(elen[before], elen[after]) < L * min_edge_ratio:
                continue
            db, da = edir[before], edir[after]
            if db[0] * da[0] + db[1] * da[1] > -0.85:      # 需近似反向
                continue

            # 笔画方向（规范化：统一指向上方/右方，保证端面倾斜方向一致）
            sdx, sdy = db
            if sdy < 0 or (abs(sdy) < 1e-9 and sdx < 0):
                sdx, sdy = -sdx, -sdy
            if abs(sdy) <= 0.30 * abs(sdx):
                ang = angle_hv
            elif abs(sdx) <= 0.30 * abs(sdy):
                ang = angle_hv
            else:
                ang = angle_diag

            a = P[run[0]]
            b = P[(run[-1] + 1) % m]
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            nx, ny = -sdy, sdx
            if ang:
                th = math.radians(ang)
                nx, ny = nx * math.cos(th) - ny * math.sin(th), \
                         nx * math.sin(th) + ny * math.cos(th)

            # 收集端面上所有点（含 run 内部的顶点）
            idxs = [run[0]] + [(i + 1) % m for i in run]
            ok = True
            for j in idxs:
                pt = P[j]
                t = (pt[0] - mx) * nx + (pt[1] - my) * ny
                q = (mx + nx * t, my + ny * t)
                if math.hypot(q[0] - pt[0], q[1] - pt[1]) > stroke_width * max_move_ratio:
                    ok = False; break
                moved[j] = q
            if not ok:
                for j in idxs:
                    moved.pop(j, None)
                continue
            visited.update(run)

        if not moved:
            out.extend(_rebuild(kind, start, segs))
            continue

        newP = [moved.get(k, P[k]) for k in range(m)]
        new_segs = []
        for k, (op, args) in enumerate(segs):
            idx = k + 1
            if idx in moved:
                if op == "lineTo":
                    new_segs.append((op, (newP[idx],)))
                else:
                    new_segs.append((op, tuple(args[:-1]) + (newP[idx],)))
            else:
                new_segs.append((op, args))
        out.extend(_rebuild(kind, newP[0], new_segs))
    return out


def _norm(x, y):
    ln = math.hypot(x, y) or 1.0
    return x / ln, y / ln


def _split_contours(value):
    """拆成 [(kind, start, segs)]，kind = 'line'（全直线）或 'curve'。"""
    out = []
    cur = None
    for op, args in value:
        if op == "moveTo":
            if cur:
                out.append(cur)
            cur = ["line", args[0], []]
        elif op == "lineTo":
            cur[2].append((op, args))
        elif op in ("curveTo", "qCurveTo"):
            cur[0] = "curve"
            cur[2].append((op, args))
        elif op == "closePath":
            if cur:
                out.append(cur)
                cur = None
    if cur:
        out.append(cur)
    return out


def _rebuild(kind, start, segs):
    out = [("moveTo", (start,))]
    out.extend(segs)
    out.append(("closePath", ()))
    return out


def apply_all(value, params):
    """按固定顺序应用算子。顺序有讲究：先结构、后重心、最后笔画。

    只应用 params 中显式出现的算子 —— 缺省即不变形。
    """
    v = value
    if "face" in params:
        v = face_scale(v, **params["face"])
    if "spread" in params:
        v = center_spread(v, **params["spread"])
    if "gravity" in params:
        v = gravity_warp(v, **params["gravity"])
    if "soften" in params:
        v = soften(v, **params["soften"])
    if "stroke" in params:
        v = stroke_offset(v, **params["stroke"])
    return v
