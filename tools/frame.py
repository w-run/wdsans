"""画框与格位 —— **唯一来源**。

任何工具需要"画框多大、格位怎么编号"，都必须从这里取，不要自己再定义一份。
曾经 glyph_view 和 glyph_svg 各写一套，改网格时只改了一边，
结果同一张图里出现 a–p 和 0–f 两套编号。

画框（em 坐标，1000 upm）：
    x ∈ [-20, 1020]     宽 1040
    y ∈ [900, -140]     高 1040
    基线 y = 0，距顶部 900

格位：
    16×16，每格 65
    列 0–f（左→右），行 0–f（上→下）
    格位 = 两位十六进制，列在前行在后：`3a` = 第 3 列第 a 行
    矩形 = 起点格-终点格：`3a-9d`
"""
X0, X1 = -20.0, 1020.0
Y_TOP, Y_BOT = 900.0, -140.0

GRID = 16
CELL = (X1 - X0) / GRID          # 65.0
WIDTH = X1 - X0                  # 1040
HEIGHT = Y_TOP - Y_BOT           # 1040

HEX = "0123456789abcdef"


def cell_name(col, row):
    """(列, 行) → '3a'。"""
    return f"{HEX[col]}{HEX[row]}"


def cell_box(name):
    """'3a' → 该格左上角的 em 坐标 (x, y_top)。"""
    name = name.strip().lower()
    if len(name) != 2 or name[0] not in HEX or name[1] not in HEX:
        raise SystemExit(f"格位写法应为两位十六进制（如 3a / 0f），收到: {name}")
    return X0 + HEX.index(name[0]) * CELL, Y_TOP - HEX.index(name[1]) * CELL


def region_from_crop(spec):
    """'3a-9d' → 起点格到终点格围成的矩形 (x0, ytop, x1, ybot)。

    单格写法 '3a' 等价于 '3a-3a'。
    """
    spec = spec.strip().lower()
    if "-" in spec:
        a, b = spec.split("-", 1)
    else:
        a = b = spec
    ax, ay = cell_box(a)
    bx, by = cell_box(b)
    x0 = min(ax, bx)
    x1 = max(ax, bx) + CELL
    ytop = max(ay, by)
    ybot = min(ay, by) - CELL
    return x0, ytop, x1, ybot


def region_from_box(spec):
    """'x0,y0,x1,y1'（em 坐标）→ 规范化矩形。"""
    vals = [float(v) for v in spec.split(",")]
    if len(vals) != 4:
        raise SystemExit("--box 需要 4 个数：x0,y0,x1,y1")
    bx0, by0, bx1, by1 = vals
    return (min(bx0, bx1), max(by0, by1), max(bx0, bx1), min(by0, by1))
