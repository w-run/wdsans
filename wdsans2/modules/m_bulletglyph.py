#!/usr/bin/env python3
"""m_bulletglyph - U+2022 • 使用独立字形（R36）

问题: 四个码位共用 periodcentered。间隔号 118x126 合理，
      但项目符号 • 应明显更大（参考 HOS 231x230 / OPPO 230x229）。
      实测我们 118x126，面积比仅 0.28。

方案: 从 Mona Sans（OFL 1.1）取 bullet，二次曲线转三次，新建 glyph 给 U+2022。
      不动 periodcentered（间隔号保持不动）。

关键约束:
  1. 我们的字体一律三次曲线（C），Mona 的 bullet 是 4 段 QM
     -> 必须转三次，否则 CFF2 表达不一致
  2. 三档转后签名必须一致: MCCCCCCCCZ（已验证）
  3. 墨迹尺寸转前后不变: 215x218 / 227x232 / 259x270
"""
import os
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.basePen import BasePen
from canonpen3 import make_charstring

MONA = "/workspace/wdsans/ref/mona/MonaSansVF.ttf"
SRC = os.environ.get("WDS_SRC", "/workspace/wdsans2/build/masters_R35")
OUT = os.environ.get("WDS_OUT", "/workspace/wdsans2/build/masters_R36")
TARGET_CP = 0x2022
NEW_GN = "bullet.2022"

MASTERS = [
    ("master-ExtraLight-250.otf", 250),
    ("master-Regular-400.otf", 400),
    ("master-Heavy-900.otf", 900),
]


class QuadToCubicPen(BasePen):
    def __init__(self):
        super().__init__(None)
        self.ops = []
    def _moveTo(self, p):
        self.ops.append(("M", p))
    def _lineTo(self, p):
        self.ops.append(("L", p))
    def _curveToOne(self, p1, p2, p3):
        self.ops.append(("C", p1, p2, p3))
    def _qCurveToOne(self, p1, p2):
        p0 = self._getCurrentPoint()
        c1 = (p0[0] + 2.0/3.0*(p1[0]-p0[0]), p0[1] + 2.0/3.0*(p1[1]-p0[1]))
        c2 = (p2[0] + 2.0/3.0*(p1[0]-p2[0]), p2[1] + 2.0/3.0*(p1[1]-p2[1]))
        self.ops.append(("C", c1, c2, p2))
    def _closePath(self):
        self.ops.append(("Z",))
    def _endPath(self):
        self.ops.append(("E",))


def to_contours(ops):
    """把 pen ops 转成 canonpen3 的 contour 结构"""
    C = []
    cur = None
    for o in ops:
        if o[0] == "M":
            if cur: C.append(cur)
            cur = {"start": o[1], "segs": []}
        elif o[0] == "L":
            if cur: cur["segs"].append(["L", o[1]])
        elif o[0] == "C":
            if cur: cur["segs"].append(["C", o[1], o[2], o[3]])
        elif o[0] == "Z":
            pass
    if cur: C.append(cur)
    return C


def get_bullet(weight):
    f = TTFont(MONA)
    instantiateVariableFont(f, {"wght": weight}, inplace=True)
    cm = f.getBestCmap(); gs = f.getGlyphSet(); h = f["hmtx"]
    if TARGET_CP not in cm:
        f.close(); return None
    gn = cm[TARGET_CP]
    pen = QuadToCubicPen()
    gs[gn].draw(pen)
    adv = h[gn][0]
    f.close()
    return to_contours(pen.ops), adv


def main(dry=False):
    print("=== 取 Mona bullet 并转三次 ===")
    data = {}
    for fn, w in MASTERS:
        r = get_bullet(w)
        if r is None:
            print("  w%d 无 bullet" % w); return 1
        C, adv = r
        sig = "/".join("".join(s[0] for s in c["segs"]) for c in C)
        data[w] = (C, adv, sig)
        print("  w%-4d adv=%-4d 轮廓=%d sig=%s" % (w, adv, len(C), sig))

    sigs = set(v[2] for v in data.values())
    if len(sigs) > 1:
        print("  !! 三档签名不一致: %s" % sigs); return 2
    print("  签名一致，可注入")

    if dry:
        print("(dry)"); return 0

    os.makedirs(OUT, exist_ok=True)
    for fn, w in MASTERS:
        mf = TTFont(os.path.join(SRC, fn))
        csT = mf["CFF2"].cff.topDictIndex[0].CharStrings
        # 🔴 顺序关键: 先强制解析 hmtx，再改 numGlyphs，否则解析错位
        hmtx = mf["hmtx"]
        _ = hmtx.metrics  # 触发解析
        C, adv, sig = data[w]
        old_cs = csT["periodcentered"]
        cs_new = make_charstring(C, old_cs.private, old_cs.globalSubrs)
        # CFF2: charStrings 存名字->索引，charStringsIndex 存实际数据
        if csT.charStringsAreIndexed:
            csT.charStringsIndex.append(cs_new)
            csT.charStrings[NEW_GN] = len(csT.charStringsIndex) - 1
        else:
            csT.charStrings[NEW_GN] = cs_new
        # 加 hmtx 条目
        hmtx.metrics[NEW_GN] = (adv, 0)
        # 最后改 glyphOrder + numGlyphs
        order = mf.getGlyphOrder()
        if NEW_GN not in order:
            order.append(NEW_GN)
            mf.setGlyphOrder(order)
            mf["maxp"].numGlyphs = len(order)
        for t in mf["cmap"].tables:
            if t.isUnicode() and TARGET_CP in t.cmap:
                t.cmap[TARGET_CP] = NEW_GN
        mf["post"].formatType = 3.0
        mf["post"].glyphOrder = None
        dst = os.path.join(OUT, fn)
        mf.save(dst)
        mf.close()
        print("  [%d] -> %s" % (w, dst))
    return 0


if __name__ == "__main__":
    sys.exit(main("--dry" in sys.argv))