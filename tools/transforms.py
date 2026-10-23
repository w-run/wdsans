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


def stroke_offset(value, delta=0.0):
    """笔画加粗/减细：沿每个节点的法线方向整体位移。

    delta > 0 加粗，< 0 减细（单位：设计单位 / 1000 em）。

    ⚠️ 实现要点：
    - 按**段**处理，一段上的控制点共享同一法线基准，避免重复输出算子
    - 按轮廓绕向统一法线方向，保证 delta 的正负语义一致
    - 只移动已有节点，节点数不变 → VF 安全
    """
    if abs(delta) < 1e-9:
        return value

    contours = _split_contours(value)
    out = []
    for kind, start, segs in contours:
        n = len(segs)
        if n < 2:
            out.extend(_rebuild(kind, start, segs))
            continue

        P = [start] + [args[-1] for _, args in segs]
        m = len(P)
        if m > 1 and math.hypot(P[0][0] - P[-1][0], P[0][1] - P[-1][1]) < 1e-6:
            P = P[:-1]
            m = len(P)
        if m < 3:
            out.extend(_rebuild(kind, start, segs))
            continue

        # 绕向：有向面积
        area = 0.0
        for i in range(m):
            x1, y1 = P[i]; x2, y2 = P[(i + 1) % m]
            area += x1 * y2 - x2 * y1
        sign = 1.0 if area < 0 else -1.0      # 顺时针轮廓：外法线取 +90°

        # 每个顶点的法线 = 相邻两边法线的平均
        normals = []
        for i in range(m):
            a = P[(i - 1) % m]; b = P[i]; c = P[(i + 1) % m]
            nx1, ny1 = _norm(-(b[1] - a[1]), b[0] - a[0])
            nx2, ny2 = _norm(-(c[1] - b[1]), c[0] - b[0])
            nx, ny = nx1 + nx2, ny1 + ny2
            ln = math.hypot(nx, ny)
            if ln < 1e-6:
                nx, ny = nx1, ny1
            else:
                nx, ny = nx / ln, ny / ln
            # 转角处沿角平分线位移，需按 1/cos(半角) 放大，才能保证面位移等于 delta
            dot = max(-1.0, min(1.0, nx1 * nx2 + ny1 * ny2))
            cos_half = math.sqrt(max(1e-6, (1 + dot) / 2))
            scale = 1.0 / max(0.30, cos_half)
            normals.append((nx * sign * scale, ny * sign * scale))

        newP = [(P[i][0] + normals[i][0] * delta,
                 P[i][1] + normals[i][1] * delta) for i in range(m)]

        new_segs = []
        for k, (op, args) in enumerate(segs):
            idx = k + 1
            if op == "lineTo":
                new_segs.append((op, (newP[idx % m],)))
            else:
                # 曲线：控制点按自身邻近法线位移（用段起点与终点的法线插值）
                if len(args) == 3:
                    p0 = newP[k % m]; p3 = newP[idx % m]
                    n0 = normals[k % m]; n3 = normals[idx % m]
                    p1 = (args[0][0] + (n0[0] * 0.67 + n3[0] * 0.33) * delta,
                          args[0][1] + (n0[1] * 0.67 + n3[1] * 0.33) * delta)
                    p2 = (args[1][0] + (n0[0] * 0.33 + n3[0] * 0.67) * delta,
                          args[1][1] + (n0[1] * 0.33 + n3[1] * 0.67) * delta)
                    new_segs.append((op, (p1, p2, p3)))
                else:
                    new_segs.append((op, args))
        out.extend(_rebuild(kind, newP[0], new_segs))
    return out


def terminal_fix(value, angle_hv=0.0, angle_diag=4.0, stroke_width=82.0,
                 width_norm=1.0, probe_frac=0.35, max_face_ratio=1.8,
                 min_edge_ratio=1.5, max_move_ratio=1.5):
    """端面修整：一次解决三件事。

      1) 平直化 —— 端面可能是微凹的弧，压成一条直线
      2) 等宽   —— 端面比笔画主体宽（越往末端越粗）时，收回到主体宽度
      3) 斜度   —— 横竖 0°、斜笔 angle_diag

    与 cap_angle 的区别：支持**曲线端面**，并且做宽度归一。
    只移动端面上的点（数量不变）→ VF 安全。
    """
    contours = _split_contours(value)
    out = []
    for kind, start, segs in contours:
        n = len(segs)
        if n < 3:
            out.extend(_rebuild(kind, start, segs))
            continue

        P = [start] + [args[-1] for _, args in segs]
        m = n + 1
        eop = [segs[k][0] if k < n else "lineTo" for k in range(m)]
        elen = [math.hypot(P[(k + 1) % m][0] - P[k][0], P[(k + 1) % m][1] - P[k][1])
                for k in range(m)]

        moved = {}
        done = set()
        for k in range(m):
            if k in done:
                continue
            is_line = eop[k] == "lineTo"
            if not (1e-6 < elen[k] <= stroke_width * max_face_ratio):
                continue
            # 端面的前后两段必须是长段（可曲线）
            before = (k - 1) % m
            after = (k + 1) % m
            if before == k or after == k:
                continue
            if elen[before] < max(elen[k], stroke_width) * min_edge_ratio:
                continue
            if elen[after] < max(elen[k], stroke_width) * min_edge_ratio:
                continue

            A1 = P[k]; B0 = P[(k + 1) % m]
            A0 = P[before]; B1 = P[(k + 2) % m]

            # 笔画方向 = 两条长边方向的平均（取反向一致的那个）
            d1 = _norm(A1[0] - A0[0], A1[1] - A0[1])
            d2 = _norm(B1[0] - B0[0], B1[1] - B0[1])
            if d1[0] * d2[0] + d1[1] * d2[1] > -0.7:
                continue                      # 不是端面（可能是转角）
            sd = _norm(d1[0] - d2[0], d1[1] - d2[1])
            if sd[1] < 0 or (abs(sd[1]) < 1e-9 and sd[0] < 0):
                sd = (-sd[0], -sd[1])

            # 主体宽度：沿两条长边各走 probe_frac，量两点距离
            t = probe_frac
            Pa = (A1[0] + (A0[0] - A1[0]) * t, A1[1] + (A0[1] - A1[1]) * t)
            Pb = (B0[0] + (B1[0] - B0[0]) * t, B0[1] + (B1[1] - B0[1]) * t)
            W = math.hypot(Pa[0] - Pb[0], Pa[1] - Pb[1])
            L = math.hypot(B0[0] - A1[0], B0[1] - A1[1])
            if W < 1e-6:
                continue

            # 目标宽度
            target_W = W + (min(L, W) - W) * width_norm
            if width_norm <= 0:
                target_W = L

            # 倾斜角
            if abs(sd[1]) >= 0.95:
                ang = angle_hv                 # 竖画
            elif abs(sd[0]) >= 0.95:
                ang = angle_hv                 # 横画
            else:
                ang = angle_diag               # 斜笔
            nx, ny = -sd[1], sd[0]
            if ang:
                th = math.radians(ang)
                nx, ny = nx * math.cos(th) - ny * math.sin(th), \
                         nx * math.sin(th) + ny * math.cos(th)

            mx, my = (A1[0] + B0[0]) / 2, (A1[1] + B0[1]) / 2
            # 端面上的所有点（含曲线控制点）投影到目标直线
            face_idx = [k]
            j = (k + 1) % m
            while j != (k + 1) % m or len(face_idx) == 1:
                face_idx.append(j)
                if j == (k + 1) % m:
                    break
                j = (j + 1) % m
                if j == k:
                    break
            ok = True
            tmp = {}
            for idx in face_idx:
                pt = P[idx]
                proj = (pt[0] - mx) * nx + (pt[1] - my) * ny
                proj = max(-target_W / 2, min(target_W / 2, proj))
                q = (mx + nx * proj, my + ny * proj)
                if math.hypot(q[0] - pt[0], q[1] - pt[1]) > stroke_width * max_move_ratio:
                    ok = False; break
                tmp[idx] = q
            if ok and tmp:
                moved.update(tmp)
                done.update([k, (k + 1) % m])

        if not moved:
            out.extend(_rebuild(kind, start, segs))
            continue
        newP = [moved.get(i, P[i]) for i in range(m)]
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


def flatten_flare(value, ratio=1.0, stroke_width=82.0,
                  max_cap_ratio=1.6, min_edge_ratio=1.5, probe=1.0,
                  flare_threshold=0.94):
    """去喇叭口：把笔画端部的「喇叭状张开」收成与笔画主体等宽。

    喇叭口 = 端面比后方主体**更宽**（传统木刻刀痕遗留）。
    做法：沿两条长边向内探测，量出主体宽度 W；
    若端面长度 L > W（判定为喇叭口），把端面的两个端点向中点收拢到 W。

    ratio = 1.0 收成完全等宽；0.5 只收一半；0 = 不处理。
    只移动端面两个端点，节点数不变 → VF 安全。
    """
    if ratio <= 0:
        return value
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
        eop = [ops[k] if k < n else "lineTo" for k in range(m)]
        elen = [math.hypot(P[(k + 1) % m][0] - P[k][0], P[(k + 1) % m][1] - P[k][1])
                for k in range(m)]

        moved = {}
        for k in range(m):
            if eop[k] != "lineTo" or not (1e-6 < elen[k] <= stroke_width * max_cap_ratio):
                continue
            before = (k - 1) % m
            after = (k + 1) % m
            if elen[before] < elen[k] * min_edge_ratio or elen[after] < elen[k] * min_edge_ratio:
                continue
            A1 = P[k]                    # 端面起点
            B0 = P[(k + 1) % m]          # 端面终点
            A0 = P[(k - 1) % m]          # 长边另一端
            B1 = P[(k + 2) % m]
            L = elen[k]
            d = max(1.0, L * probe)
            tA = min(1.0, d / elen[before])
            tB = min(1.0, d / elen[after])
            Pa = (A1[0] + (A0[0] - A1[0]) * tA, A1[1] + (A0[1] - A1[1]) * tA)
            Pb = (B0[0] + (B1[0] - B0[0]) * tB, B0[1] + (B1[1] - B0[1]) * tB)
            W = math.hypot(Pa[0] - Pb[0], Pa[1] - Pb[1])
            if W <= 1e-6 or L <= W * flare_threshold:
                continue                      # 不是喇叭口
            # 把端面收到 W（按 ratio 比例）
            target = L + (W - L) * ratio
            if target >= L:
                continue
            mx, my = (A1[0] + B0[0]) / 2, (A1[1] + B0[1]) / 2
            ux, uy = (B0[0] - A1[0]) / L, (B0[1] - A1[1]) / L
            moved[k] = (mx - ux * target / 2, my - uy * target / 2)
            moved[(k + 1) % m] = (mx + ux * target / 2, my + uy * target / 2)

        if not moved:
            out.extend(_rebuild(kind, start, segs))
            continue
        newP = [moved.get(k, P[k]) for k in range(m)]
        new_segs = []
        for k, (op, args) in enumerate(segs):
            idx = k + 1
            if idx in moved:
                new_segs.append((op, (newP[idx],)))
            else:
                new_segs.append((op, args))
        out.extend(_rebuild(kind, newP[0], new_segs))
    return out




def soften(value, tension=1.0):
    """笔画软硬：调整曲线控制点张力（控制点离 on 点的距离比例）。

    tension = 1.0 保持原样；< 1 曲线变直变硬；> 1 曲线变饱满变软。
    只移动已有控制点，不增删节点 → VF 安全。
    """
    if abs(tension - 1.0) < 1e-9:
        return value
    out = []
    last_on = None
    for op, args in value:
        if op in ("moveTo", "lineTo"):
            last_on = args[0]
            out.append((op, args))
        elif op == "curveTo":
            p1, p2, p3 = args
            p0 = last_on if last_on is not None else (0.0, 0.0)
            n1 = (p0[0] + (p1[0] - p0[0]) * tension,
                  p0[1] + (p1[1] - p0[1]) * tension)
            n2 = (p3[0] + (p2[0] - p3[0]) * tension,
                  p3[1] + (p2[1] - p3[1]) * tension)
            out.append((op, (n1, n2, p3)))
            last_on = p3
        else:
            out.append((op, args))
    return out


# ---------------------------------------------------------------- 内部工具

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
                out.append((cur[0], cur[1], cur[2]))
            cur = ["line", args[0], []]
        elif op in ("lineTo", "curveTo", "qCurveTo"):
            if cur is None:
                continue
            if op != "lineTo":
                cur[0] = "curve"
            cur[2].append((op, args))
        elif op in ("closePath", "endPath"):
            if cur:
                out.append((cur[0], cur[1], cur[2]))
                cur = None
    if cur:
        out.append((cur[0], cur[1], cur[2]))
    return out


def _rebuild(kind, start, segs):
    out = [("moveTo", (start,))]
    out.extend(segs)
    out.append(("closePath", ()))
    return out


def cap_angle(value, **kw):
    """兼容别名：端面处理统一走 terminal_fix。"""
    kw.pop("max_cap_ratio", None)
    kw.pop("min_edge_ratio", None)
    kw.pop("min_dot", None)
    kw.pop("collinear_dot", None)
    return terminal_fix(value, **kw)



def dot_normalize(value, stroke_width=82.0, max_dim_ratio=2.6, ratio=1.0,
                  flatten_faces=True):
    """点等宽：把楔形点改成等宽棒，并把弧形的端面压平。

    适用对象：小尺寸的四点闭合轮廓（点 / 短笔），端面可以是曲线。
    做法：
      1) 按弦长判断哪两条边是端面（短的）
      2) 把两个端面的弦长改成相等（取中值）→ 两条长边自然平行 → 等宽
      3) 端面若是曲线，把控制点投影到弦上 → 端面变平直（消除内凹）

    只移动已有节点，点数不变 → VF 安全。
    """
    if ratio <= 0:
        return value
    contours = _split_contours(value)
    out = []
    for kind, start, segs in contours:
        if len(segs) != 4:
            out.extend(_rebuild(kind, start, segs))
            continue
        P = [start] + [args[-1] for _, args in segs]
        if len(P) > 1 and math.hypot(P[0][0] - P[-1][0], P[0][1] - P[-1][1]) < 1.0:
            P = P[:-1]
        if len(P) != 4:
            out.extend(_rebuild(kind, start, segs))
            continue

        xs = [q[0] for q in P]; ys = [q[1] for q in P]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        # 点/短笔的判据：**短边**不超过笔宽的 max_dim_ratio 倍，长边不超过 6 倍
        if min(w, h) > stroke_width * max_dim_ratio or max(w, h) > stroke_width * 6.0:
            out.extend(_rebuild(kind, start, segs))
            continue

        def dist(a, b):
            return math.hypot(a[0] - b[0], a[1] - b[1])
        e = [dist(P[i], P[(i + 1) % 4]) for i in range(4)]

        # 端面 = 弦长之和较小的那一对
        if e[0] + e[2] <= e[1] + e[3]:
            faces = [(1, 2), (3, 0)]
        else:
            faces = [(0, 1), (2, 3)]

        l0 = dist(P[faces[0][0]], P[faces[0][1]])
        l1 = dist(P[faces[1][0]], P[faces[1][1]])
        if min(l0, l1) < 1e-6:
            out.extend(_rebuild(kind, start, segs))
            continue
        target = l0 + (((l0 + l1) / 2) - l0) * ratio

        newP = list(P)
        new_segs = [(op, args) for op, args in segs]
        for (i, j), cur in zip(faces, (l0, l1)):
            a, b = P[i], P[j]
            if cur < 1e-6:
                continue
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            ux, uy = (b[0] - a[0]) / cur, (b[1] - a[1]) / cur
            na = (mx - ux * target / 2, my - uy * target / 2)
            nb = (mx + ux * target / 2, my + uy * target / 2)
            newP[i] = na; newP[j] = nb
            # 端面对应的那一段：若为曲线，把控制点投影到新弦上
            seg_idx = i  # 段 i 从 P[i] 到 P[j]
            op, args = new_segs[seg_idx]
            if op == "curveTo" and flatten_faces and len(args) == 3:
                p1, p2 = args[0], args[1]
                def proj(pt):
                    vx, vy = pt[0] - na[0], pt[1] - na[1]
                    t = vx * ux + vy * uy
                    t = max(0.0, min(target, t))
                    return (na[0] + ux * t, na[1] + uy * t)
                new_segs[seg_idx] = (op, (proj(p1), proj(p2), nb))
            else:
                new_segs[seg_idx] = (op, (nb,))

        # 其余段端点同步
        for k in range(4):
            ni = (k + 1) % 4
            op, args = new_segs[k]
            if op == "curveTo" and len(args) == 3:
                new_segs[k] = (op, (args[0], args[1], newP[ni]))
            else:
                new_segs[k] = (op, (newP[ni],))

        out.extend(_rebuild(kind, newP[0], new_segs))
    return out


# ---------------------------------------------------------------- 内部工具

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
                out.append((cur[0], cur[1], cur[2]))
            cur = ["line", args[0], []]
        elif op in ("lineTo", "curveTo", "qCurveTo"):
            if cur is None:
                continue
            if op != "lineTo":
                cur[0] = "curve"
            cur[2].append((op, args))
        elif op in ("closePath", "endPath"):
            if cur:
                out.append((cur[0], cur[1], cur[2]))
                cur = None
    if cur:
        out.append((cur[0], cur[1], cur[2]))
    return out


def _rebuild(kind, start, segs):
    out = [("moveTo", (start,))]
    out.extend(segs)
    out.append(("closePath", ()))
    return out


def cap_angle(value, **kw):
    """兼容别名：端面处理统一走 terminal_fix。"""
    kw.pop("max_cap_ratio", None)
    kw.pop("min_edge_ratio", None)
    kw.pop("min_dot", None)
    kw.pop("collinear_dot", None)
    return terminal_fix(value, **kw)



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
    if "dot" in params:
        v = dot_normalize(v, **params["dot"])
    if "terminal" in params:
        v = terminal_fix(v, **params["terminal"])
    if "flare" in params:
        v = flatten_flare(v, **params["flare"])
    if "soften" in params:
        v = soften(v, **params["soften"])
    if "stroke" in params:
        v = stroke_offset(v, **params["stroke"])
    return v
