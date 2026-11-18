#!/usr/bin/env python3
# test_radfoot - 验证 m_radfoot: 都对, 对照组不动
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_radfoot

R="/workspace/wdsans2/build/masters_R33/master-Regular-400.otf"
f=TTFont(R,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
print("应命中 (都有日/口旁出脚):")
for ch in "都郵郭鄙部陪哲":
    if ord(ch) not in cm: continue
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    C=contours_from_pen(rp.value)
    h=m_radfoot.find(C)
    print("  %s -> %s" % (ch, h if h else "无"))
print()
print("不应命中 (亻/氵旁, 本来就到底):")
for ch in "仰似倒假做修代件住你他们":
    if ord(ch) not in cm: continue
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    C=contours_from_pen(rp.value)
    h=m_radfoot.find(C)
    print("  %s -> %s" % (ch, h if h else "无"))
f.close()