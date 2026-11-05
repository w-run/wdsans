"""笔画验收工具集：把 P16~P22 用到的验证脚本固化入库。

用法:
  python tools/stroke_audit.py density    # 减细均匀性（相关分析）
  python tools/stroke_audit.py geo        # 几何保真度（包围盒缩放）
  python tools/stroke_audit.py feet       # 去出脚检测
  python tools/stroke_audit.py stats      # 单字墨量/包围盒

所有测量都用矢量轮廓（AreaPen/BoundsPen），不依赖渲染，结果可复现。
"""
from __future__ import annotations
import sys, math, argparse

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen

OURS = "/data/build-cache/wdsans-p1/wdsans-FINAL.ttf"
NOTO = "/workspace/wdsans/ref/NotoSansCJKsc-VF.ttf"
OPPO = "/workspace/wdsans/ref/ops/ops-400.ttf"


def load(path, wght=None):
    f = TTFont(path)
    if wght is not None and "fvar" in f:
        f = instancer.instantiateVariableFont(
            f, {"wght": wght}, inplace=True, updateFontNames=False, optimize=False)
    return f


def glyph_metrics(f, ch):
    """返回 (墨面积, 包围盒w, 包围盒h) 或 None"""
    cm = f.getBestCmap()
    name = cm.get(ord(ch))
    if not name:
        return None
    gs = f.getGlyphSet()
    try:
        ap = AreaPen(gs); gs[name].draw(ap); area = abs(ap.value)
        bp = BoundsPen(gs); gs[name].draw(bp); b = bp.bounds
    except Exception:
        return None
    if not b or area <= 0:
        return None
    w = b[2] - b[0]; h = b[3] - b[1]
    if w <= 0 or h <= 0:
        return None
    return area, w, h


def _cjk_range(f, other):
    ours = set(f.getBestCmap()); oth = set(other.getBestCmap())
    return [cp for cp in sorted(ours) if 0x4E00 <= cp <= 0x9FFF and cp in oth]


def cmd_geo(step_div=1500):
    """几何保真度：包围盒缩放比，检测局部破坏"""
    o = load(OURS, 400); n = load(NOTO, 400)
    cps = _cjk_range(o, n)
    step = max(1, len(cps) // step_div)
    rows = []
    for cp in cps[::step]:
        a = glyph_metrics(o, chr(cp)); b = glyph_metrics(n, chr(cp))
        if not a or not b:
            continue
        rows.append((chr(cp), a[1]/b[1], a[2]/b[2]))
    o.close(); n.close()
    if not rows:
        print("无有效样本"); return
    ws = sorted(r[1] for r in rows); hs = sorted(r[2] for r in rows)
    def p(arr, q): return arr[min(len(arr)-1, int(len(arr)*q))]
    medw = p(ws, .5)
    over = sum(1 for r in rows if abs(r[1]-medw) > 0.01)
    print("样本: %d" % len(rows))
    print("宽度比 p5=%.4f p50=%.4f p95=%.4f" % (p(ws,.05), medw, p(ws,.95)))
    print("高度比 p5=%.4f p50=%.4f p95=%.4f" % (p(hs,.05), p(hs,.5), p(hs,.95)))
    print("宽度比偏离中位 >1%% 的字数: %d / %d (%.2f%%)" % (
        over, len(rows), 100.0*over/len(rows)))
    print("判定:", "均匀变换，无局部破坏" if over == 0 else "存在离群，需排查")


def cmd_density(step_div=2000):
    """减细均匀性：减细比 vs 笔画密度"""
    o = load(OURS, 400); n = load(NOTO, 400)
    cps = _cjk_range(o, n)
    step = max(1, len(cps) // step_div)
    pts = []
    for cp in cps[::step]:
        a = glyph_metrics(o, chr(cp)); b = glyph_metrics(n, chr(cp))
        if not a or not b:
            continue
        dens = b[0] / float(b[1]*b[2])
        ratio = a[0] / float(b[0])
        if dens > 0 and ratio > 0:
            pts.append((dens, ratio))
    o.close(); n.close()
    if len(pts) < 10:
        print("样本不足"); return
    pts.sort()
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    nn = len(pts); mx = sum(xs)/nn; my = sum(ys)/nn
    cov = sum((x-mx)*(y-my) for x, y in pts)
    sx = math.sqrt(sum((x-mx)**2 for x in xs))
    sy = math.sqrt(sum((y-my)**2 for y in ys))
    r = cov/(sx*sy) if sx*sy else 0
    print("样本: %d" % nn)
    print("相关系数 r = %.4f" % r)
    q = nn//5
    print("按密度五等分:")
    for k in range(5):
        seg = pts[k*q:(k+1)*q] if k < 4 else pts[4*q:]
        if seg:
            print("  %.3f-%.3f  mean=%.3f  n=%d" % (
                seg[0][0], seg[-1][0], sum(s[1] for s in seg)/len(seg), len(seg)))
    print("判定:", "均匀减细，无密度偏置" if abs(r) < 0.3 else "存在密度相关，需排查")


def cmd_stats(chars):
    fonts = [("我们", load(OURS, 400)), ("Noto", load(NOTO, 400)), ("OPPO", load(OPPO))]
    print("%-4s %-12s %-12s %-12s %-10s" % ("字", "我们墨", "Noto墨", "OPPO墨", "我们/OPPO"))
    for ch in chars:
        vals = []
        for _, f in fonts:
            m = glyph_metrics(f, ch)
            vals.append(m[0] if m else None)
        a, b, c = vals
        ratio = ("%.3f" % (a/c)) if (a and c) else "-"
        print("%-4s %-12s %-12s %-12s %-10s" % (
            ch, a or "-", b or "-", c or "-", ratio))
    for _, f in fonts:
        f.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["geo", "density", "stats"])
    ap.add_argument("chars", nargs="*", default=["国", "永", "漆", "口", "十"])
    a = ap.parse_args()
    if a.cmd == "geo":
        cmd_geo()
    elif a.cmd == "density":
        cmd_density()
    else:
        cmd_stats(a.chars)


if __name__ == "__main__":
    main()
