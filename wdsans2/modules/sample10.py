#!/usr/bin/env python3
# sample10 - 用 m_barple2 生成 10 个代表字, 三档
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_barple2

B = "/workspace/wdsans2/build/masters_T6/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
OUT = "/workspace/wdsans2/build/s10"
os.makedirs(OUT, exist_ok=True)

CHARS = "多及力刀乃予了争互五亨享永夕"

for tag in ["250","400","900"]:
    f = TTFont(B + FN[tag])
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
    n = 0; hitlist = []
    for ch in CHARS:
        if ord(ch) not in cm: continue
        gn = cm[ord(ch)]
        rp = RecordingPen(); gs[gn].draw(rp)
        C = contours_from_pen(rp.value)
        hits = m_barple2.find(C)
        if not hits:
            continue
        hitlist.append(ch)
        NEW = m_barple2.apply(C, hits)
        old = csT[gn]
        csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
        n += 1
    f["post"].formatType = 3.0; f["post"].glyphOrder = None
    p = os.path.join(OUT, "S_%s.otf" % tag)
    f.save(p); f.close()
    print("  %s: 改动 %d 字 -> %s" % (tag, n, "".join(hitlist)))