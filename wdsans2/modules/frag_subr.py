#!/usr/bin/env python3
"""frag_subr - 确认 SHS 的 subr 拆分导致轮廓数差异（是否真缺陷）"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen


def area_and_bounds(path, ch, lbl):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        print("  %s 无此字" % lbl); f.close(); return
    gn = cm[ord(ch)]
    bp = BoundsPen(gs)
    rp = RecordingPen()
    gs[gn].draw(rp)
    gs[gn].draw(bp)
    adv = f["hmtx"][gn][0]
    f.close()
    # 计算总墨面积（对每个轮廓用鞋带公式）
    total = 0.0
    cur = []
    for op, args in rp.value:
        if op == "moveTo":
            cur = [np.array(args[0], float)]
        elif op == "lineTo":
            cur.append(np.array(args[0], float))
        elif op in ("curveTo", "qCurveTo"):
            cur.extend([np.array(a, float) for a in args])
        elif op == "closePath":
            if len(cur) >= 3:
                P = np.array(cur)
                ar = 0.5 * abs(np.dot(P[:, 0], np.roll(P[:, 1], 1)) -
                               np.dot(P[:, 1], np.roll(P[:, 0], 1)))
                total += ar
            cur = []
    b = bp.bounds
    print("  %-8s 墨面积 %8.0f  bbox %dx%d  adv=%d" %
          (lbl, total, b[2] - b[0], b[3] - b[1], adv))
    return total


print("=== 嘴 墨面积对比（若面积接近则只是拆分方式不同）===")
area_and_bounds('/workspace/static/wdsans/WDesignSans-VF.otf', '嘴', '我们 VF')
area_and_bounds('/workspace/wdsans2/build/masters_R25/master-Regular-400.otf', '嘴', 'R25')
area_and_bounds('/workspace/wdsans/ref/shs/shs-400.otf', '嘴', 'SHS')
area_and_bounds('/workspace/wdsans/ref/hos/hos-400.ttf', '嘴', 'HOS')
area_and_bounds('/workspace/wdsans/ref/ops4/OPPOSans4.ttf', '嘴', 'OPPO')
print()
print("=== 眠 墨面积对比 ===")
area_and_bounds('/workspace/static/wdsans/WDesignSans-VF.otf', '眠', '我们 VF')
area_and_bounds('/workspace/wdsans/ref/shs/shs-400.otf', '眠', 'SHS')
area_and_bounds('/workspace/wdsans/ref/hos/hos-400.ttf', '眠', 'HOS')