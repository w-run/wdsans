"""字体几何测量：从轮廓算，不靠像素。

所有指标都是**精确几何量**（格林公式 + 一维扫描线交点），不经过光栅化，
所以不受渲染器差异影响。

指标：
  bbox        字形包围盒（em 单位）
  ink         墨面积占 em 框比例（"黑度"）
  stem        横/竖笔画粗细（扫描线实测，非估算）
  centroid    墨重心偏移（中宫位置）
  curve_ratio 曲线段占比（直的还是圆的）
  nodes       节点数 / 每千单位²墨面积的节点密度

用法：
    python3 metrics.py --fonts "shs=ref/shs/shs-400.otf,hos=ref/hos/hos-400.ttf" \
        --charset common --json out.json
"""
import argparse
import json
import math
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

UPM = 1000.0

# 结构覆盖齐全的样字：独体/上下/左右/包围/半包围/复杂/极简
COMMON = (
    "永国回口田日目月用周同门问间闻"
    "一二三十上下中正王玉主主义之"
    "人大天夫太犬木本末未朱来米水"
    "小少尖尚当光先见贝页顺须頃"
    "山川州州巛工土士干于平年午牛"
    "女子好安如妈妈字学孚子孔孙孝"
    "心必忒忠念思急息忽总忘志忙"
    "手才方方式武成或我找戈戊戌"
    "攵故教收改放政敌效敢散敬数"
    "辶过达迈远违运送进连这还进"
    "金全余余合令今介余俞食会仓"
    "氵江河湖海沈汪洲汉汗汁池汤"
    "艹花苦英茶草兰若茂茅茹莫落"
    "宀家室宇宇宙宋完宏宝定客宣"
    "犭犭犯狂狄狗狠狡狼狈猬猢"
    "饣饭饮饰饱饲饼饿馆馄馒馔"
    "纟红纸纪约纯纳纺线练组细织"
    "钅针钉钓钞钟钢钥钱铁铜银"
    "病痛疾疗症疲痕痴瘦瘢癌"
    "雨雪霜雾露需震霍霓霖霹"
    "火灯灰炎炉炭点烈烦烧烟煤"
    "石矿码砂砌砍砸破硬确碎碑"
    "禾私秃秀秋科秒种秤租积称"
    "衣表衫衬衷衰袁袋被裁裂装"
    "言计订认讨让训议讯记讲讳"
    "贝负贡财责贤败账货质贩贪"
    "马冯闯驰驱驳驴驶驻驼驾骂"
    "鸟鸡鸣鸥鸦鸭鸳鸯鸽鹅鹤鹰"
    "鱼鲁鲂鲍鲜鲨鲸鳄鳝鳞"
    "页顶项顺须顽顾顿预领颇颈"
    "力办加务劝功动助努劫劲劳势"
    "刂刊刑划则刚创删别扭别利"
    "寸对寻导寿封射尊尊"
    "卩卫叩卯印危即却卵卿卸"
    "匚区匠匣匪匿匹巨臣"
    "囗囗囚四回因团困围固国图圆"
    "冂冂内冈冉册同网周"
)

PROBES = "永国一口田日月人大小中木水土火"


class FlatPen(BasePen):
    """把轮廓展平成多边形，供面积/扫描线计算。"""

    def __init__(self, glyphSet, tol=2.0):
        super().__init__(glyphSet)
        self.tol = tol
        self.contours = []
        self.cur = []
        self.nseg = 0
        self.ncurve = 0
        self.nline = 0
        self.nnodes = 0

    def _moveTo(self, pt):
        self._end()
        self.cur = [pt]
        self._start = pt
        self.nnodes += 1

    def _lineTo(self, pt):
        self.cur.append(pt)
        self.nseg += 1
        self.nline += 1
        self.nnodes += 1

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        n = self._nsub(p0, p1, p2, p3)
        for i in range(1, n + 1):
            t = i / n
            self.cur.append(_bez(p0, p1, p2, p3, t))
        self.nseg += n
        self.ncurve += 1
        self.nnodes += 1

    def _closePath(self):
        self._end()

    def _endPath(self):
        self._end()

    def _end(self):
        if len(self.cur) > 2:
            if self.cur[0] != self.cur[-1]:
                self.cur.append(self.cur[0])
            self.contours.append(self.cur)
        self.cur = []
        self.cur = []

    def _nsub(self, p0, p1, p2, p3):
        # 用控制多边形长度粗估，控制点步长 ~ tol
        L = (math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3))
        return max(6, min(40, int(L / 12) + 6))


def _bez(p0, p1, p2, p3, t):
    mt = 1 - t
    a, b, c, d = mt ** 3, 3 * mt * mt * t, 3 * mt * t * t, t ** 3
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def signed_area(pts):
    s = 0.0
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        s += x0 * y1 - x1 * y0
    return s / 2.0


def moments(contours):
    """返回 (ink_area, cx, cy)。用有向面积，洞会自动相减。"""
    A = 0.0
    Cx = Cy = 0.0
    for pts in contours:
        a = signed_area(pts)
        A += a
        # 重心（闭合多边形）
        mx = my = 0.0
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            cr = x0 * y1 - x1 * y0
            mx += (x0 + x1) * cr
            my += (y0 + y1) * cr
        Cx += mx / 6.0
        Cy += my / 6.0
    if abs(A) < 1e-9:
        return 0.0, 0.0, 0.0
    return abs(A), Cx / A, Cy / A


def runs_at(contours, coord, axis):
    """一维扫描线：返回该处墨区的连续段长度列表。

    axis='h' → 在 y=coord 处量横向墨段（测竖笔粗细）
    axis='v' → 在 x=coord 处量纵向墨段（测横笔粗细）
    """
    xs = []
    for pts in contours:
        rng = range(len(pts) - 1)
        for i in rng:
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
            xs.append((u0 + t * (u1 - u0), 1 if b > a else -1))
    if not xs:
        return []
    xs.sort()
    out = []
    w = 0
    start = None
    for x, d in xs:
        prev = w
        w += d
        if prev == 0 and w != 0:
            start = x
        elif prev != 0 and w == 0 and start is not None:
            if x - start >= 3:          # 忽略渲染毛刺（hairline）
                out.append(x - start)
            start = None
    return out


def measure_glyph(font, gs, gname, cmap_rev):
    pen = FlatPen(gs)
    try:
        gs[gname].draw(pen)
    except Exception:
        return None
    pen._end()
    cs = pen.contours
    if not cs:
        return None
    area, cx, cy = moments(cs)
    pts = [p for c in cs for p in c]
    xMin = min(p[0] for p in pts); xMax = max(p[0] for p in pts)
    yMin = min(p[1] for p in pts); yMax = max(p[1] for p in pts)

    # 扫描线探针：取字形中部
    hw = []
    vw = []
    if yMax - yMin > 50:
        for f in (0.25, 0.5, 0.75):
            hw += runs_at(cs, yMin + (yMax - yMin) * f, "h")
    if xMax - xMin > 50:
        for f in (0.25, 0.5, 0.75):
            vw += runs_at(cs, xMin + (xMax - xMin) * f, "v")

    return {
        "g": gname, "ch": cmap_rev.get(gname, ""),
        "w": xMax - xMin, "h": yMax - yMin,
        "xMin": xMin, "xMax": xMax, "yMin": yMin, "yMax": yMax,
        "ink": area / (UPM * UPM),
        "cx": cx, "cy": cy,
        "nodes": pen.nnodes, "ncont": len(cs),
        "curve": pen.ncurve / max(1, pen.ncurve + pen.nline),
        "face": ((xMax - xMin) * (yMax - yMin)) / (UPM * UPM),
        "white": 1 - (area / max(1.0, (xMax - xMin) * (yMax - yMin))),
        "mL": xMin, "mR": UPM - xMax, "mB": yMin, "mT": UPM - yMax,
        "src_seg": pen.ncurve + pen.nline,
        "hw": hw, "vw": vw,
    }


def stat(vals):
    if not vals:
        return None
    s = sorted(vals)
    n = len(s)
    mean = sum(s) / n
    med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    var = sum((v - mean) ** 2 for v in s) / n
    return {"n": n, "mean": mean, "median": med, "sd": math.sqrt(var),
            "min": s[0], "max": s[-1]}


def measure_font(path, chars):
    font = TTFont(path)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    rev = {}
    for cp, gn in cmap.items():
        rev.setdefault(gn, chr(cp))
    hhea = font["hhea"]
    os2 = font["OS/2"]
    head = font["head"]
    meta = {
        "file": path,
        "upm": head.unitsPerEm,
        "name": font["name"].getDebugName(4),
        "ascender": hhea.ascender, "descender": hhea.descender,
        "typoAsc": getattr(os2, "sTypoAscender", None),
        "typoDesc": getattr(os2, "sTypoDescender", None),
        "winAsc": getattr(os2, "usWinAscent", None),
        "winDesc": getattr(os2, "usWinDescent", None),
        "capHeight": getattr(os2, "sCapHeight", None),
        "xHeight": getattr(os2, "sxHeight", None),
        "wclass": os2.usWeightClass,
        "numCJK": sum(1 for c in cmap if 0x4E00 <= c <= 0x9FFF),
        "numGlyphs": font["maxp"].numGlyphs,
    }
    rows = []
    miss = []
    for ch in chars:
        gn = cmap.get(ord(ch))
        if not gn:
            miss.append(ch)
            continue
        r = measure_glyph(font, gs, gn, rev)
        if r:
            r["ch"] = ch
            rows.append(r)
    font.close()
    return meta, rows, miss


def aggregate(meta, rows):
    ink = [r["ink"] for r in rows]
    hw = [v for r in rows for v in r["hw"]]
    vw = [v for r in rows for v in r["vw"]]
    nodes = [r["nodes"] for r in rows]
    curve = [r["curve"] for r in rows]
    wid = [r["w"] for r in rows]
    hei = [r["h"] for r in rows]
    # 重心偏离 em 中心（500,350 大致视觉中心）的距离
    off = [math.hypot(r["cx"] - 500, r["cy"] - 340) for r in rows]
    area = [r["ink"] * UPM * UPM for r in rows]
    dens = [r["nodes"] / (a / 1000.0) for r, a in zip(rows, area) if a > 1000]
    return {
        "family": meta,
        "glyphs": len(rows),
        "ink": stat(ink),
        "w": stat(wid),
        "h": stat(hei),
        "hw": stat(hw),        # 竖笔粗细
        "vw": stat(vw),        # 横笔粗细
        "nodes": stat(nodes),
        "node_density": stat([d * 10 for d in dens]),  # 每万单位²墨面积的节点数
        "curve": stat(curve),
        "face": stat([r["face"] for r in rows]),
        "white": stat([r["white"] for r in rows]),
        "mL": stat([r["mL"] for r in rows]),
        "mR": stat([r["mR"] for r in rows]),
        "mT": stat([r["mT"] for r in rows]),
        "mB": stat([r["mB"] for r in rows]),
        "src_seg": stat([r["src_seg"] for r in rows]),
        "centroid_off": stat(off),
        "cx": stat([r["cx"] for r in rows]),
        "cy": stat([r["cy"] for r in rows]),
        "xMin": stat([r["xMin"] for r in rows]),
        "yMin": stat([r["yMin"] for r in rows]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True, help="key=path,key=path")
    ap.add_argument("--charset", default="common")
    ap.add_argument("--chars", default=None, help="自定义字符或文件")
    ap.add_argument("--json", required=True)
    ap.add_argument("--detail", default=None, help="额外输出逐字 JSON")
    a = ap.parse_args()

    chars = PROBES if a.charset == "probe" else COMMON
    if a.chars:
        chars = a.chars if not a.chars.endswith(".txt") else open(a.chars).read()
    # 去重保序
    seen = set()
    chars = "".join(c for c in chars if not (c in seen or seen.add(c)))

    fonts = []
    for item in a.fonts.split(","):
        k, p = item.split("=", 1)
        fonts.append((k.strip(), p.strip()))

    out = {"charset_size": len(chars), "results": {}, "per_glyph": {}}
    for key, path in fonts:
        meta, rows, miss = measure_font(path, chars)
        agg = aggregate(meta, rows)
        agg["missing"] = "".join(miss)
        out["results"][key] = agg
        out["per_glyph"][key] = rows
        print(f"[{key}] {len(rows)}/{len(chars)} 字  缺:{len(miss)}  "
              f"ink={agg['ink']['mean']:.3f}  竖={agg['hw']['median']:.0f}  "
              f"横={agg['vw']['median']:.0f}  曲线={agg['curve']['mean']:.2f}",
              file=sys.stderr)

    with open(a.json, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    if a.detail:
        with open(a.detail, "w") as f:
            json.dump(out["per_glyph"], f, ensure_ascii=False)
    print("saved", a.json)


if __name__ == "__main__":
    main()
