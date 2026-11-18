#!/usr/bin/env python3
# test_c2lift - 验证 m_c2lift: 多 应命中, 对照组不应误伤
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_c2lift

R="/workspace/wdsans2/build/masters_R34/master-Regular-400.otf"
f=TTFont(R,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
print("应命中 (多及了予 这类横折+撇):")
for ch in "多及予了乃刀力":
    if ord(ch) not in cm: continue
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    C=contours_from_pen(rp.value)
    h=m_c2lift.find(C)
    print("  %s -> %s" % (ch, h if h else "无"))
print()
print("对照组 (无横折撇结构):")
for ch in "口日田一十中申甲木本水火":
    if ord(ch) not in cm: continue
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    C=contours_from_pen(rp.value)
    h=m_c2lift.find(C)
    print("  %s -> %s" % (ch, h if h else "无"))
f.close()