#!/usr/bin/env python3
"""check_preview - 核查预览字体是否还有 ledge 残留"""
import io
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen

W = '/workspace/static/wdsans/wd-preview.woff2'
R29 = '/workspace/wdsans2/build/masters_R29/master-Regular-400.otf'
R16 = '/workspace/wdsans2/build/masters_R16/master-Regular-400.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'


def load_w(path):
    f = TTFont(path)
    f.flavor = None
    b = io.BytesIO(); f.save(b); f.close()
    b.seek(0)
    return TTFont(b)


def topbar(path, ch, iswoff=False):
    """返回顶部横笔的右端 x 和字形右界"""
    f = load_w(path) if iswoff else TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    f.close()
    cs = []
    cur = None
    for op, args in rp.value:
        if op == "moveTo":
            if cur: cs.append(cur)
            cur = [tuple(args[0])]
        elif op in ("lineTo","curveTo","qCurveTo"):
            if cur:
                for a in args:
                    if hasattr(a, "__len__") and len(a) == 2 and not isinstance(a[0], (list,tuple)):
                        cur.append(tuple(a))
        elif op == "closePath":
            if cur: cs.append(cur)
            cur = None
    if cur: cs.append(cur)
    gx1 = max(p[0] for c in cs for p in c)
    gmax = max(p[1] for c in cs for p in c)
    best = None
    for c in cs:
        xs = [p[0] for p in c]; ys = [p[1] for p in c]
        w = max(xs)-min(xs); h = max(ys)-min(ys)
        if w < 300 or w/max(h,1) < 2.5:
            continue
        if max(ys) < gmax - 320:
            continue
        m = gx1 - max(xs)
        if best is None or m < best:
            best = m
    return (gx1, best)


print('%-5s %-16s %-16s %-16s %-16s' % ('字','预览woff2','R29 master','R16(有ledge)','SHS'))
for ch in "散形几各冬条备务":
  def f2(r):
    return "宽%.0f 余%s" % (r[0], ("%.0f" % r[1]) if r[1] is not None else "-") if r else "-"
  a = topbar(W, ch, True)
  b = topbar(R29, ch)
  c = topbar(R16, ch)
  d = topbar(SHS, ch)
  print("%-5s %-16s %-16s %-16s %-16s" % (ch, f2(a), f2(b), f2(c), f2(d)))