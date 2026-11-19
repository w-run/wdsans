#!/usr/bin/env python3
"""正确判据: 端面段 = 短段 + 前后都是长曲线 + 位于笔画末端"""
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

def seg_len(s, prev):
    if s[0] == "L":
        e = np.array(s[1], dtype=float)
    elif s[0] == "C":
        e = np.array(s[3], dtype=float)
    elif s[0] == "Q":
        e = np.array(s[2], dtype=float)
    else:
        return 0.0, None
    return float(np.linalg.norm(e - np.array(prev, dtype=float))), e

STRICT_MAXLEN = 130   # 端面宽度上限
MIN_NEIGHBOR = 150    # 前后段至少这么长才算"长曲线"

n_glyph = 0
hit_glyphs = []
hit_segs = []

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
    found = []
    for ci, c in enumerate(C):
        segs = c["segs"]
        n = len(segs)
        if n < 3:
            continue
        # 逐段取起点
        starts = [c["start"]]
        for s in segs[:-1]:
            if s[0] == "L": starts.append(s[1])
            elif s[0] == "C": starts.append(s[3])
            elif s[0] == "Q": starts.append(s[2])
            elif s[0] == "QM": starts.append(s[1][-1])
        for j, s in enumerate(segs):
            if s[0] != "C":
                continue
            L, end = seg_len(s, starts[j])
            if L < 30 or L > STRICT_MAXLEN:
                continue
            # 前后段长度
            Lprev, _ = seg_len(segs[j-1], starts[j-1])
            Lnext, _ = seg_len(segs[(j+1) % n], starts[(j+1) % n])
            if Lprev < MIN_NEIGHBOR or Lnext < MIN_NEIGHBOR:
                continue
            # 弯曲度
            p0 = np.array(starts[j], dtype=float)
            c1 = np.array(s[1], dtype=float)
            c2 = np.array(s[2], dtype=float)
            chord = end - p0
            if L < 1e-6: continue
            u = chord / L
            nrm = np.array([-u[1], u[0]])
            dev1 = abs(float((c1 - p0).dot(nrm)))
            dev2 = abs(float((c2 - p0).dot(nrm)))
            bend = max(dev1, dev2) / L
            if bend > 0.12:
                continue
            found.append((ci, j, round(L, 0), round(bend, 3), round(float(chord[0]), 0), round(float(chord[1]), 0)))
    if found:
        hit_glyphs.append(chr(cp))
        hit_segs.append((chr(cp), found))

print("CJK 字形: %d" % n_glyph)
print("命中字: %d (%.1f%%)" % (len(hit_glyphs), 100.0*len(hit_glyphs)/max(1,n_glyph)))
print("命中段总数: %d" % sum(len(x[1]) for x in hit_segs))
print()
print("=== 样例（前 20 字）===")
for ch, segs in hit_segs[:20]:
    for s in segs:
        print("  %s  轮廓%d段%d  长=%.0f 弯曲=%.3f dx=%.0f dy=%.0f" % (ch, s[0], s[1], s[2], s[3], s[4], s[5]))
print()
lens = [s[2] for _, segs in hit_segs for s in segs]
if lens:
    print("段长分布: 中位=%.0f P10=%.0f P90=%.0f 最大=%.0f" % (
        np.median(lens), np.percentile(lens,10), np.percentile(lens,90), max(lens)))
f.close()
