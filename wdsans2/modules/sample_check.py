#!/usr/bin/env python3
# sample_check - 从 1040 改动词中随机抽样, 检查高度是否都拉到接近 SHS
import sys, json, random
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_boxrad

idx=json.load(open("/workspace/wdsans2/build/masters_R33/boxrad_index.json"))
cps=[int(k) for k in idx]
random.seed(7)
samp=random.sample(cps, 12)

def leftbox(path, cp, lid):
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    if cp not in cm: f.close(); return None
    rp=RecordingPen(); gs[cm[cp]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    ps=[m_boxrad.allpts(c) for c in C]
    if lid is None or max(lid)>=len(ps): return None
    y0=min(ps[i][:,1].min() for i in lid); y1=max(ps[i][:,1].max() for i in lid)
    return y1-y0

R32="/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
R34="/workspace/wdsans2/build/masters_R34/master-Regular-400.otf"
print("%-4s %-10s %-10s %-8s" % ("字","R32高","R34高","增加"))
ok=0
for cp in samp:
    lid=idx[str(cp)]
    a=leftbox(R32, cp, lid); b=leftbox(R34, cp, lid)
    if a is None or b is None: continue
    d=b-a
    mark = "OK" if 60 < d < 110 else "!!"
    if mark=="OK": ok+=1
    print("%-4s %-10.0f %-10.0f %+.0f  %s" % (chr(cp), a, b, d, mark))
print()
print("-> %d/12 增量在 60~110 区间（预期 ~80）" % ok)