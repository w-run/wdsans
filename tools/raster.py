"""渲染工具：把字形画成 PNG（图片级判定，铁律要求）。

关键实现：**用非零环绕规则（nonzero winding）光栅化**。
思源黑的轮廓是互相重叠的独立笔画，用奇偶规则（XOR）会把重叠处挖空 —— 那是错的。
"""
import numpy as np
from PIL import Image


def flatten(value, steps=10):
    """把 (op, args) 记录展平成闭合折线列表。

    支持三次曲线（curveTo，CFF）与二次曲线（qCurveTo，TrueType，含隐含 on 点）。
    """
    contours = []
    cur = []

    def flush():
        nonlocal cur
        if len(cur) > 2:
            contours.append(np.array(cur, dtype=float))
        cur = []

    def quad(p0, p1, p2):
        p0 = np.array(p0, float); p1 = np.array(p1, float); p2 = np.array(p2, float)
        for i in range(1, steps + 1):
            t = i / steps; mt = 1 - t
            cur.append(tuple(mt * mt * p0 + 2 * mt * t * p1 + t * t * p2))

    for op, args in value:
        if op == "moveTo":
            flush()
            cur = [args[0]]
        elif op == "lineTo":
            cur.append(args[0])
        elif op == "curveTo":
            p0 = np.array(cur[-1], dtype=float) if cur else np.zeros(2)
            p1, p2, p3 = (np.array(p, dtype=float) for p in args)
            for i in range(1, steps + 1):
                t = i / steps
                mt = 1 - t
                pt = (mt**3 * p0 + 3 * mt**2 * t * p1
                      + 3 * mt * t**2 * p2 + t**3 * p3)
                cur.append(tuple(pt))
        elif op == "qCurveTo":
            # TrueType：最后一点是 on，中间是控制点（可能有多个 → 隐含 on 点）
            pts = [np.array(p, float) for p in args]
            if pts[-1] is None:  # 全 off 的闭合二次曲线
                pts = pts[:-1]
                start = np.array(cur[-1], float)
                mids = []
                for i in range(len(pts)):
                    nxt = pts[(i + 1) % len(pts)]
                    mids.append((pts[i] + nxt) / 2)
                for i, ctrl in enumerate(pts):
                    p0 = start if i == 0 else mids[i - 1]
                    p2 = mids[i]
                    quad(p0, ctrl, p2)
                continue
            start = np.array(cur[-1], float) if cur else pts[0]
            prev = start
            for i in range(len(pts) - 1):
                ctrl = pts[i]
                if i < len(pts) - 2:
                    nxt = (ctrl + pts[i + 1]) / 2
                else:
                    nxt = pts[-1]
                quad(prev, ctrl, nxt)
                prev = nxt
        elif op in ("closePath", "endPath"):
            flush()
    flush()
    return contours


def rasterize(contours, size, ss=2, y_offset=60.0, em=1000.0):
    """非零环绕规则光栅化，返回 0..1 浮点蒙版（size×size，ss 倍超采样）。"""
    n = size * ss
    scale = n / em
    # 每个像素中心对应的字形 y 坐标（第 0 行在最上面）
    ys = ((n - (np.arange(n) + 0.5)) / scale) - y_offset
    xs = (np.arange(n) + 0.5) / scale
    mask = np.zeros((n, n), dtype=np.float32)

    edges = []
    for ct in contours:
        if len(ct) < 3:
            continue
        q = np.roll(ct, -1, axis=0)
        for (x1, y1), (x2, y2) in zip(ct, q):
            if y1 != y2:
                edges.append((x1, y1, x2, y2))
    if not edges:
        return mask

    for row in range(n):
        y = ys[row]
        crossings = []
        for x1, y1, x2, y2 in edges:
            if (y1 <= y < y2) or (y2 <= y < y1):
                t = (y - y1) / (y2 - y1)
                x = x1 + t * (x2 - x1)
                crossings.append((x, 1 if y2 > y1 else -1))
        if not crossings:
            continue
        crossings.sort()
        wind = 0
        for i, (x, d) in enumerate(crossings):
            wind += d
            if wind != 0:
                col0 = max(0, int(np.ceil((x - 0) * scale - 0.5)))
                nxt = crossings[i + 1][0] if i + 1 < len(crossings) else em
                col1 = min(n, int(np.floor(nxt * scale - 0.5)))
                if col1 > col0:
                    mask[row, col0:col1] = 1.0

    mask = mask.reshape(size, ss, size, ss).mean(axis=(1, 3))
    return mask


def compose(text_boxes, size, pad=10, ss=2):
    """把多个 (mask, char) 拼成网格图。"""
    cols = max(len(r) for r in text_boxes)
    rows = len(text_boxes)
    W = cols * (size + pad) + pad
    H = rows * (size + pad) + pad
    canvas = np.ones((H, W), dtype=np.float32)
    for r, row in enumerate(text_boxes):
        for c, (mask, ok) in enumerate(row):
            oy = pad + r * (size + pad)
            ox = pad + c * (size + pad)
            if mask is None:
                canvas[oy:oy + size, ox:ox + size] = 0.5 if not ok else 1.0
                continue
            region = canvas[oy:oy + size, ox:ox + size]
            canvas[oy:oy + size, ox:ox + size] = region * (1 - mask)
    return Image.fromarray((canvas * 255).astype(np.uint8))
