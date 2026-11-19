#!/usr/bin/env python3
"""分析全库撇/捺末端段的分布，确定 C->L 判据范围"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

MASTER = "/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"
f = TTFont(MASTER, lazy=True)
cm = f.getBestCmap()
gs = f.getGlyphSet()

# 统计：多少字形有「右下方向的 C 段末端」
n_glyph = 0
n_tip = 0
samples = []

for cp in cm:
    if not (0x4E00 <= cp <= 0x9FFF):
        continue
    gn = cm[cp]
    rp = RecordingPen()
    try:
        gs[gn].draw(rp)
    except Exception:
        continue
    C = contours_from_pen(rp.value)
    n_glyph += 1
    hit = False
    for c in C:
        segs = c["segs"]
        if len(segs) < 2:
            continue
        for j, s in enumerate(segs):
            if s[0] != "C":
                continue
            end = np.array(s[3], dtype=float)
            c2 = np.array(s[2], dtype=float)
            prev = np.array(segs[j-1][-1] if j > 0 else c["start"], dtype=float)
            # 末端段特征: 段长较短、终点是笔画端
            seg_len = float(np.linalg.norm(end - prev))
            if seg_len < 30 or seg_len > 200:
                continue
            # 方向: 右下 (dx>0, dy<0)
            dx = end[0] - prev[0]
            dy = end[1] - prev[1]
            if dx <= 0 or dy >= 0:
                continue
            # 弯曲度: c2 偏离弦的距离
            chord = end - prev
            L = np.linalg.norm(chord)
            if L < 1e-6:
                continue
            u = chord / L
            nrm = np.array([-u[1], u[0]])
            dev = abs(float((c2 - prev).dot(nrm)))
            bend = dev / L
            if bend < 0.06:
                hit = True
                samples.append((chr(cp), round(seg_len, 0), round(bend, 3), round(float(dx), 0), round(float(dy), 0)))
                break
    if hit:
        n_tip += 1

print("CJK 字形总数: %d" % n_glyph)
print("含「右下 C 段末端 + 低弯曲」的字: %d" % n_tip)
print()
print("=== 样例（前 25 个）===")
for s in samples[:25]:
    print("  %s  段长=%.0f 弯曲=%.3f dx=%.0f dy=%.0f" % s)
print()
print("=== 弯曲度分布 ===")
if samples:
    bends = [s[2] for s in samples]
    lens = [s[1] for s in samples]
    print("  弯曲: 中位=%.3f  P90=%.3f  最大=%.3f" % (np.median(bends), np.percentile(bends, 90), max(bends)))
    print("  段长: 中位=%.0f  P10=%.0f  P90=%.0f" % (np.median(lens), np.percentile(lens, 10), np.percentile(lens, 90)))
f.close()
