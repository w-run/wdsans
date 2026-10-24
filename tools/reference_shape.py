"""参考曲线迁移：不修补旧轮廓，直接映射参考字形的真实曲线。

原则：
- 源参考与目标字形都从原始字体读取（CFF 三次 / TrueType 二次）
- 只对参考轮廓做统一的坐标映射，不逐点猜参数
- 未选中的轮廓原样保留
"""
import subprocess
import vector_ops as V


def reference_pie(path, ch="永"):
    cs = V.read_glyph(path, ch)
    candidates = []
    for i, c in enumerate(cs):
        pts = V.endpoints(c)
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        if min(xs) < 150 and max(xs) < 450 and max(ys) > 400:
            candidates.append(i)
    if not candidates:
        raise ValueError("参考撇未找到")
    return cs[candidates[0]]


def map_reference(contour, target_left=56.0, target_right=390.0,
                  target_top=440.0, target_bottom=368.0,
                  ref_left=67.0, ref_right=390.0,
                  ref_top=427.0, ref_bottom=369.0):
    """参考撇顶块映射到 SHS 顶块；曲线形状保持不变，仅作仿射变换。

    上方顶块按目标高度映射；顶块以下只平移，避免把笔道纵向拉伸。
    """
    kx = (target_right - target_left) / (ref_right - ref_left)
    ky = (target_top - target_bottom) / (ref_top - ref_bottom)

    def point(p):
        x, y = p
        xx = target_left + (x - ref_left) * kx
        if y >= ref_bottom:
            yy = target_bottom + (y - ref_bottom) * ky
        else:
            yy = y + (target_bottom - ref_bottom)
        return (xx, yy)

    return [(op, tuple(point(p) for p in args)) if op != "closePath" else (op, args)
            for op, args in contour]


def replace_pie(base, reference):
    """用参考撇替换目标撇，其他轮廓不动。"""
    candidates = []
    for i, c in enumerate(base):
        pts = V.endpoints(c)
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        if min(xs) < 150 and max(xs) < 450 and max(ys) > 400:
            candidates.append(i)
    if not candidates:
        raise ValueError("目标撇未找到")
    idx = candidates[0]
    out = list(base)
    out[idx] = map_reference(reference)
    return out, idx


if __name__ == "__main__":
    base = V.read_glyph("ref/shs/shs-400.otf", "永")
    ref = reference_pie("ref/ops/ops-400.ttf")
    changed, idx = replace_pie(base, ref)
    print("replace contour", idx)
    print("reference:", V.path_data([ref]))
    print("mapped:", V.path_data([changed[idx]]))
    for suffix, contours in (("orig", base), ("mapped", changed)):
        path = f"/tmp/refpie_{suffix}.svg"
        with open(path, "w") as f:
            f.write(V.svg(contours))
        subprocess.run(["rsvg-convert", "-o", path + ".png", path], check=True)
