#!/usr/bin/env python3
"""eval_bullet - 评估 U+2022 • 拆分方案的可行性

方案: 从 Mona Sans 取 bullet 字形，新建一个 glyph 给 U+2022 专用。
      许可: Mona 是 OFL 1.1，可用。

检查项:
  1. Mona 的 bullet 墨迹尺寸是否合适（应接近参考 229）
  2. 是否有空闲 glyph 槽位
  3. 三档是否都能取到
  4. GSUB/GPOS 是否需要同步
"""
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen

MONA = "/workspace/wdsans/ref/mona/MonaSansVF.ttf"
VF = "/workspace/static/wdsans/WDesignSans-VF.otf"

print("=== 1. Mona 的 bullet / periodcentered 尺寸 ===")
for w in (250, 400, 900):
    f = TTFont(MONA)
    instantiateVariableFont(f, {"wght": w}, inplace=True)
    cm = f.getBestCmap(); gs = f.getGlyphSet(); h = f["hmtx"]
    out = []
    for cp, nm in ((0x2022, "bullet"), (0x00B7, "periodcentered")):
        if cp not in cm:
            out.append("%s:无" % nm);
            continue
        gn = cm[cp]
        bp = BoundsPen(gs)
        try:
            gs[gn].draw(bp)
        except Exception:
            pass
        b = bp.bounds
        if b:
            out.append("%s %dx%d adv=%d" % (nm, b[2]-b[0], b[3]-b[1], h[gn][0]))
        else:
            out.append("%s 无墨" % nm)
    f.close()
    print("  w%-4d %s" % (w, " | ".join(out)))

print()
print("=== 2. 我们的空闲 glyph 槽位 ===")
f = TTFont(VF, lazy=True)
cm = f.getBestCmap()
ng = f["maxp"].numGlyphs
print("  numGlyphs = %d (上限 65535)" % ng)
# 找未映射的 glyph
order = f.getGlyphOrder()
mapped = set(cm.values())
free = [g for g in order if g not in mapped]
print("  未映射 glyph 数 = %d" % len(free))
print("  前 5 个: %s" % free[:5])
f.close()