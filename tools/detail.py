"""细节测量：笔画末端 / 转角 / 撇捺曲率 / 粗细变化。

不靠眼睛，也不靠像素 —— 全部在轮廓上做几何量算。

四个探针：
  terminal  笔画末端的**切口角度**（斜切还是平切）
  corner    包围结构四个角的**圆角半径**（欧化还是方肩）
  profile   斜笔的**中线轨迹与垂直笔宽**（撇捺的弧度与起收笔粗细）
  joint     笔画**交接处的加粗量**（搭接是否发黑）
"""
import argparse
import json
import math
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from metrics import FlatPen   # noqa: E402


_CACHE = {}


def _font(path):
    if path not in _CACHE:
        _CACHE[path] = TTFont(path)
    return _CACHE[path]


def contours_of(path, ch):
    font = _font(path)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    gn = cmap.get(ord(ch))
    if not gn:
        return None, None
    pen = FlatPen(gs)
    gs[gn].draw(pen)
    pen._end()
    return gn, pen.contours


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def scan_runs(cs, coord, axis="h"):
    """扫描线交点 → 若干条 (start, end) 墨段。"""
    ev = []
    for pts in cs:
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if axis == "h":
                a, b, u0, u1 = y0, y1, x0, x1
            else:
                a, b, u0, u1 = x0, x1, y0, y1
            if a == b:
                continue
            lo, hi = (a, b) if a < b else (b, a)
            if not (lo <= coord < hi):
                continue
            t = (coord - a) / (b - a)
            ev.append((u0 + t * (u1 - u0), 1 if b > a else -1))
    if not ev:
        return []
    ev.sort()
    out = []
    w = 0
    start = None
    for u, d in ev:
        prev = w
        w += d
        if prev == 0 and w != 0:
            start = u
        elif prev != 0 and w == 0 and start is not None:
            out.append((start, u))
            start = None
    return out


# ---------- 末端切口角度 ----------

def terminal_angle(cs, which):
    """笔画端面的方向：返回端面相对理想方向的偏差（度）。

    轮廓展平后端点常常只��� 2 个（直边），所以 2 点直接用连线，
    3 点以上用 PCA。0 = 正切（横画的端面竖直 / 竖画的端面水平）。
    """
    pts = [p for c in cs for p in c]
    x0, y0, x1, y1 = bbox(pts)
    if which in ("left", "right"):
        span = x1 - x0
        lim = 0.12 * span
        sel = [p for p in pts if ((p[0] - x0) < lim if which == "left"
                                 else (x1 - p[0]) < lim)]
        axis = "v"
    else:
        span = y1 - y0
        lim = 0.12 * span
        sel = [p for p in pts if ((y1 - p[1]) < lim if which == "top"
                                 else (p[1] - y0) < lim)]
        axis = "h"
    uniq = []
    for p in sel:
        if not uniq or math.dist(p, uniq[-1]) > 4:
            uniq.append(p)
    if len(uniq) < 2:
        return None
    if len(uniq) == 2:
        dx = uniq[1][0] - uniq[0][0]
        dy = uniq[1][1] - uniq[0][1]
        ang = math.degrees(math.atan2(abs(dy), abs(dx)))   # 0=水平, 90=竖直
    else:
        mx = sum(p[0] for p in uniq) / len(uniq)
        my = sum(p[1] for p in uniq) / len(uniq)
        sxx = sum((p[0] - mx) ** 2 for p in uniq)
        syy = sum((p[1] - my) ** 2 for p in uniq)
        sxy = sum((p[0] - mx) * (p[1] - my) for p in uniq)
        ang = abs(0.5 * math.degrees(math.atan2(2 * sxy, sxx - syy))) % 180
        if ang > 90:
            ang = 180 - ang
        ang = 90 - ang          # PCA 给的是主轴，转成端面法向角
    dev = (90 - ang) if axis == "v" else ang
    return {"n": len(uniq), "angle": ang, "dev_from_ideal": abs(dev)}


def edge_slant(cs, side):
    """端面斜切角：拟合字形一侧的边界线，返回偏离正交的度数。

    left/right → 逐 y 取最左/最右墨缘 x(y)，斜率 dx/dy 即切角；
    top/bottom → 逐 x 取最高/最低墨缘 y(x)。
    取中间 80% 范围拟合，避开两端转角。
    """
    pts = [p for c in cs for p in c]
    x0, y0, x1, y1 = bbox(pts)
    samples = []
    if side in ("left", "right"):
        n = 140
        for i in range(n):
            y = y0 + (y1 - y0) * (0.1 + 0.8 * i / (n - 1))
            runs = scan_runs(cs, y, "h")
            if not runs:
                continue
            v = runs[0][0] if side == "left" else runs[-1][1]
            samples.append((y, v))
        slope = "dx/dy"
    else:
        n = 140
        for i in range(n):
            x = x0 + (x1 - x0) * (0.1 + 0.8 * i / (n - 1))
            runs = scan_runs(cs, x, "v")
            if not runs:
                continue
            v = runs[-1][1] if side == "top" else runs[0][0]
            samples.append((x, v))
        slope = "dy/dx"
    # 只保留最长的连续带（三、二 这类多笔字，跨笔拟合毫无意义）
    bands = []
    cur = []
    for pt in samples:
        if cur and abs(pt[0] - cur[-1][0]) > 24:
            bands.append(cur)
            cur = []
        cur.append(pt)
    if cur:
        bands.append(cur)
    if not bands:
        return None
    samples = max(bands, key=len)
    if len(samples) < 6:
        return None
    # 最小二乘
    a = sum(p[0] for p in samples) / len(samples)
    b = sum(p[1] for p in samples) / len(samples)
    sxx = sum((p[0] - a) ** 2 for p in samples)
    sxy = sum((p[0] - a) * (p[1] - b) for p in samples)
    if sxx < 1e-9:
        return None
    k = sxy / sxx                     # 单位长度内的偏移
    ang = math.degrees(math.atan(abs(k)))   # 相对正交方向的倾角
    return {"n": len(samples), "slope": k, "angle": ang}


# ---------- 转角半径 ----------

def corner_radius(cs):
    """每条轮廓的四个包围盒角，圆弧半径 r = d / （√2−1）。

    d = 包围盒角到轮廓的最近距离。尖角 d≈0 → r≈0；圆角 d≈0.414r。
    不设点数门槛，否则会系统性漏掉尖角（只统计到圆角，结论会反）。
    """
    k = math.sqrt(2) - 1
    out = []
    for ci, pts in enumerate(cs):
        x0, y0, x1, y1 = bbox(pts)
        if x1 - x0 < 40 or y1 - y0 < 40:
            continue
        for name, cx, cy in (("TL", x0, y1), ("TR", x1, y1),
                             ("BL", x0, y0), ("BR", x1, y0)):
            d = min(math.dist(p, (cx, cy)) for p in pts)
            out.append({"contour": ci, "corner": name, "d": d, "r": d / k})
    return out


# ---------- 斜笔中线与笔宽 ----------

def stroke_profiles(cs, n=26):
    """沿 y 扫描，把墨段按 x 聚成若干条笔道，输出每条的中线与笔宽。"""
    pts = [p for c in cs for p in c]
    x0, y0, x1, y1 = bbox(pts)
    levels = [y0 + (y1 - y0) * (i + 0.5) / n for i in range(n)]
    strokes = {}          # id -> [(y, center, runw)]
    prev = []             # [(center, id)]
    for y in levels:
        runs = scan_runs(cs, y, "h")
        cur = []
        for (a, b) in runs:
            c = (a + b) / 2.0
            wid = b - a
            if wid < 4:
                continue
            # 与上一层的笔道配对（x 最近）
            best, bd = None, 1e9
            for (pc, pid) in prev:
                dd = abs(pc - c)
                if dd < bd and dd < 90:
                    bd, best = dd, pid
            if best is None:
                best = len(strokes)
                strokes[best] = []
            cur.append((c, best))
            strokes[best].append((y, c, wid))
        prev = cur
    out = []
    for sid, traj in strokes.items():
        if len(traj) < 6:
            continue
        out.append({"id": sid, "traj": traj})
    out.sort(key=lambda s: -len(s["traj"]))
    return out


def pair_profiles(cs, n=34):
    """逐层取最左侧与最右侧笔道 —— 撇、捺天然分居两端，不会串道。"""
    pts = [p for c in cs for p in c]
    x0, y0, x1, y1 = bbox(pts)
    left, right = [], []
    for i in range(n):
        y = y0 + (y1 - y0) * (i + 0.5) / n
        runs = [r for r in scan_runs(cs, y, "h") if r[1] - r[0] >= 4]
        if len(runs) < 2:
            continue
        a, b = runs[0]
        c_, d_ = runs[-1]
        left.append((y, (a + b) / 2, b - a))
        right.append((y, (c_ + d_) / 2, d_ - c_))
    return left, right


def analyse_stroke(traj):
    """由 (y, center, runwidth) 轨迹算：倾斜角、垂直笔宽、曲率。"""
    # 中线按 y 排序
    t = sorted(traj, key=lambda r: r[0])
    ys = [r[0] for r in t]
    xs = [r[1] for r in t]
    ws = [r[2] for r in t]
    # 局部斜率
    slopes = []
    for i in range(1, len(t)):
        dy = ys[i] - ys[i - 1]
        dx = xs[i] - xs[i - 1]
        if abs(dy) < 1e-6:
            slopes.append(float("inf"))
        else:
            slopes.append(dx / dy)
    # 每点的切线角（相对水平，0=水平 90=竖直）
    thetas = []
    for sl in slopes:
        if sl == float("inf"):
            thetas.append(90.0)
        else:
            thetas.append(math.degrees(math.atan2(1.0, abs(sl))))
    # 垂直笔宽 = 横向段宽 × sin(切线角)
    perp = [w * math.sin(math.radians(th)) for w, th in zip(ws[1:], thetas)]
    # 曲率：二阶差分 / 弧长
    turns = []                     # 相邻采样点的转角（度）
    for i in range(1, len(thetas)):
        turns.append(abs(thetas[i] - thetas[i - 1]))
    return {
        "n": len(t),
        "y0": ys[0], "y1": ys[-1],
        "x0": xs[0], "x1": xs[-1],
        "mean_angle": sum(thetas) / len(thetas) if thetas else 0,
        "w_head": sum(perp[:3]) / min(3, len(perp)) if perp else 0,
        "w_mid": perp[len(perp) // 2] if perp else 0,
        "w_tail": sum(perp[-3:]) / min(3, len(perp)) if perp else 0,
        "taper": (sum(perp[:3]) / min(3, len(perp))) / (sum(perp[-3:]) / min(3, len(perp)))
        if perp and sum(perp[-3:]) > 1 else 0,
        "turn_total": sum(turns),
        "turn_max": max(turns) if turns else 0,
        "turn_head": sum(turns[:3]) / min(3, len(turns)) if turns else 0,
        "turn_tail": sum(turns[-3:]) / min(3, len(turns)) if turns else 0,
    }


def bar_profile(cs, n=20):
    """单一横画的厚度剖面：起端 / 中段 / 末端厚度，及最厚位置。"""
    pts = [p for c in cs for p in c]
    x0, y0, x1, y1 = bbox(pts)
    prof = []
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        runs = scan_runs(cs, x, "v")
        if not runs:
            continue
        h = sum(b - a for a, b in runs)
        prof.append((x, h))
    if len(prof) < 8:
        return None
    hs = [p[1] for p in prof]
    mid = hs[len(hs) // 2]
    head = sum(hs[:3]) / 3
    tail = sum(hs[-3:]) / 3
    return {"head": head, "mid": mid, "tail": tail,
            "head_ratio": head / mid if mid else 0,
            "tail_ratio": tail / mid if mid else 0,
            "max_at": prof[hs.index(max(hs))][0]}


# ---------- 交接处加粗 ----------

def junction_fillet(cs):
    """横竖交接处的四个内角：理想尖角到轮廓的最近距离（0=纯直角）。

    十 / 中 这类 T 形交接，如果有一点点焊角或倒圆，d 会明显大于 0。
    """
    pts = [p for c in cs for p in c]
    x0, y0, x1, y1 = bbox(pts)
    # 横画上下缘：在左端附近取
    xl = x0 + 0.10 * (x1 - x0)
    bar = scan_runs(cs, 0, "v") if False else None
    vs = scan_runs(cs, xl, "v")
    if len(vs) != 1:
        return None
    bar_bot, bar_top = vs[0]
    # 竖笔左右缘：在横画上方取
    yv = bar_top + 0.55 * (y1 - bar_top)
    hs = scan_runs(cs, yv, "h")
    if not hs:
        return None
    smin = min(a for a, b in hs)
    smax = max(b for a, b in hs)
    corners = [(smin, bar_bot), (smax, bar_bot), (smin, bar_top), (smax, bar_top)]
    ds = []
    for cx, cy in corners:
        ds.append(min(math.dist(p, (cx, cy)) for p in pts))
    return {"d_mean": sum(ds) / len(ds), "d_max": max(ds), "n": len(ds)}


def stroke_overshoot(cs):
    """包围结构里，竖笔是否比底横多探出一截（出脚）。

    做法：在左/右竖笔中心取纵向墨段的最低点，与底横中点处的最低点比较。
    正值 = 竖笔更低（出脚）；0 = 齐平。
    """
    pts = [p for c in cs for p in c]
    x0, y0, x1, y1 = bbox(pts)
    ymid = 0.45 * (y0 + y1)
    hs = scan_runs(cs, ymid, "h")
    if len(hs) < 2:
        return None
    left = hs[0]
    right = hs[-1]
    lw = left[1] - left[0]
    rw = right[1] - right[0]
    xl = left[0] + lw / 2
    xr = right[1] - rw / 2
    xc = (x0 + x1) / 2

    def bottom(x):
        vs = scan_runs(cs, x, "v")
        return vs[0][0] if vs else None

    bl, br, bc = bottom(xl), bottom(xr), bottom(xc)
    if None in (bl, br, bc):
        return None
    return {"left": bl, "right": br, "bar": bc,
            "overshoot_l": bc - bl, "overshoot_r": bc - br,
            "stem_w": lw, "stem_rw": rw}


def folds(cs, thr=25.0):
    """硬折点：轮廓上转角超过 thr 度的顶点数量。

    曲线展平后，真正的弧线每点只转几度；只有"折"才会出现大转角。
    所以这个数就是"硬角数量" —— 越少越顺。
    """
    n = 0
    big = []
    for pts in cs:
        m = len(pts)
        if m < 5:
            continue
        for i in range(1, m - 1):
            ax, ay = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            bx, by = pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]
            la = math.hypot(ax, ay)
            lb = math.hypot(bx, by)
            if la < 1e-6 or lb < 1e-6:
                continue
            cosv = max(-1.0, min(1.0, (ax * bx + ay * by) / (la * lb)))
            ang = math.degrees(math.acos(cosv))
            if ang > thr:
                n += 1
                big.append(round(ang))
    return {"n": n, "angles": sorted(big, reverse=True)[:6]}


def joint_flare(cs):
    """交接加粗：竖笔在横画下缘处的宽度 / 远处宽度。>1 说明搭接鼓包。"""
    pts = [p for c in cs for p in c]
    x0, y0, x1, y1 = bbox(pts)
    xc = (x0 + x1) / 2
    # 横画边界要在**离开竖笔**的位置取，否则竖笔穿过横画只有一条连续段
    xs = x0 + 0.12 * (x1 - x0)
    vs = scan_runs(cs, xs, "v")
    if not vs:
        return None
    bands = sorted(vs)
    bar_bot, bar_top = bands[0] if len(bands) == 1 else bands[-1]
    def w_at(y):
        rs = scan_runs(cs, y, "h")
        if not rs:
            return None
        # 只取包含中心的墨段
        for a, b in rs:
            if a <= xc <= b:
                return b - a
        return None
    w_near = w_at(bar_bot - 25)
    w_far = w_at(bar_bot - 160)
    if not w_near or not w_far or w_far < 5:
        return None
    return {"near": w_near, "far": w_far, "flare": w_near / w_far}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True, help="key=path,key=path")
    ap.add_argument("--json", required=True)
    a = ap.parse_args()

    fonts = [(s.split("=", 1)[0].strip(), s.split("=", 1)[1].strip())
             for s in a.fonts.split(",")]

    # 末端：一字的两端、十字的横竖端
    terminals = [("一", "left"), ("一", "right"), ("十", "top"), ("十", "bottom"),
                 ("二", "left"), ("三", "right"), ("工", "top")]
    # 转角：包围结构
    corners = ["口", "田", "日", "目", "回", "国", "白", "田"]
    # 斜笔：撇捺
    diagonals = ["人", "大", "木", "水", "永", "又"]
    # 交接：横竖相接
    joints = ["十", "中", "王", "田", "里", "半"]

    out = {}
    for key, path in fonts:
        r = {"terminals": [], "corners": [], "diagonals": [], "joints": [],
             "slants": [], "bars": [], "overshoot": [],
             "folds": [], "flare": []}
        for ch, side in terminals:
            gn, cs = contours_of(path, ch)
            if not cs:
                continue
            t = terminal_angle(cs, side)
            if t:
                t["ch"] = ch
                t["side"] = side
                r["terminals"].append(t)
        for ch in dict.fromkeys(corners):
            gn, cs = contours_of(path, ch)
            if not cs:
                continue
            for c in corner_radius(cs):
                c["ch"] = ch
                r["corners"].append(c)
        for ch in diagonals:
            gn, cs = contours_of(path, ch)
            if not cs:
                continue
            left, right = pair_profiles(cs, 34)
            for tag, traj in (("撇", left), ("捺", right)):
                if len(traj) < 8:
                    continue
                st = analyse_stroke(traj)
                if st["n"] >= 8 and st["mean_angle"] < 80:
                    st["ch"] = ch
                    st["side"] = tag
                    r["diagonals"].append(st)
        r["slants"] = []
        for ch in ("一", "二", "口", "日"):
            gn, cs = contours_of(path, ch)
            if not cs:
                continue
            for side in ("left", "right", "top", "bottom"):
                sl = edge_slant(cs, side)
                if sl:
                    sl["ch"] = ch
                    sl["side"] = side
                    r["slants"].append(sl)
        r["bars"] = []
        for ch in ("一", "二", "三"):
            gn, cs = contours_of(path, ch)
            if not cs:
                continue
            for i, c in enumerate(cs):
                if len(c) < 4:
                    continue
                bp = bar_profile([c])
                if bp:
                    bp["ch"] = ch
                    bp["contour"] = i
                    r["bars"].append(bp)
        r["overshoot"] = []
        for ch in ("口", "日", "田", "目", "回", "国"):
            gn, cs = contours_of(path, ch)
            if not cs:
                continue
            o = stroke_overshoot(cs)
            if o:
                o["ch"] = ch
                r["overshoot"].append(o)
        r["folds"] = []
        for ch in ("永", "国", "回", "日", "田", "明", "京", "雪", "水", "人"):
            gn, cs = contours_of(path, ch)
            if not cs:
                continue
            f = folds(cs)
            f["ch"] = ch
            r["folds"].append(f)
        r["flare"] = []
        for ch in ("十", "中", "王", "里", "干"):
            gn, cs = contours_of(path, ch)
            if not cs:
                continue
            f = joint_flare(cs)
            if f:
                f["ch"] = ch
                r["flare"].append(f)
        for ch in joints:
            gn, cs = contours_of(path, ch)
            if not cs:
                continue
            j = junction_fillet(cs)
            if j:
                j["ch"] = ch
                r["joints"].append(j)
        out[key] = r
        print(f"[{key}] 末端{len(r['terminals'])} 角{len(r['corners'])} "
              f"斜笔{len(r['diagonals'])} 交接{len(r['joints'])}", file=sys.stderr)

    json.dump(out, open(a.json, "w"), ensure_ascii=False, indent=1)
    print("saved", a.json)


if __name__ == "__main__":
    main()
