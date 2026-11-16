#!/usr/bin/env python3
"""frag_early - 查 T6 之前，拆分是在哪一步发生的"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen


def cnt(path, ch, lbl):
    if not os.path.exists(path):
        print("  %-28s 不存在" % lbl)
        return
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        print("  %-28s 无此字" % lbl); f.close(); return
    rp = RecordingPen()
    gs[cm[ord(ch)]].draw(rp)
    f.close()
    n = sum(1 for op, a in rp.value if op == "moveTo")
    print("  %-28s %d 轮廓" % (lbl, n))


print("=== 嘴 轮廓数逐阶段 ===")
BASE = "/workspace/wdsans2/build/"
STAGES = [
  ('SHS 原版 400', '/workspace/wdsans/ref/shs/shs-400.otf'),
  ('T3', BASE + 'masters_T3/master-Regular-400.otf'),
  ('T4', BASE + 'masters_T4/master-Regular-400.otf'),
  ('T5', BASE + 'masters_T5/master-Regular-400.otf'),
  ('T6', BASE + 'masters_T6/master-Regular-400.otf'),
  ('MOD', BASE + 'masters_MOD/master-Regular-400.otf'),
  ('R25', BASE + 'masters_R25/master-Regular-400.otf'),
  ('当前 VF', '/workspace/static/wdsans/WDesignSans-VF.otf'),
]
for lbl, p in STAGES:
    cnt(p, "嘴", lbl)
print()
print("=== 眠 轮廓数逐阶段 ===")
for lbl, p in STAGES:
    cnt(p, "眠", lbl)
print()
print("=== 可用目录 ===")
import glob
for d in sorted(glob.glob(BASE + "masters_T*")):
    print("  " + d)