#!/usr/bin/env python3
# scope_radfoot - 全库扫描 m_radfoot 命中范围
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_radfoot

R="/workspace/wdsans2/build/masters_R33/master-Regular-400.otf"
f=TTFont(R,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
hits=[]
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
    rp=RecordingPen()
    try: gs[cm[cp]].draw(rp)
    except Exception: continue
    C=contours_from_pen(rp.value)
    h=m_radfoot.find(C)
    if h: hits.append(chr(cp))
f.close()
print("m_radfoot 命中: %d 字" % len(hits))
print("  " + "".join(hits[:120]))