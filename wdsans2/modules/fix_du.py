#!/usr/bin/env python3
# fix_du - 对「都」应用 m_radfoot 并渲染
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_radfoot

SRC="/workspace/wdsans2/build/masters_R33/"; OUT="/workspace/wdsans2/build/rf_test"
os.makedirs(OUT, exist_ok=True)
FN={"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
for tag in ["250","400","900"]:
    f=TTFont(SRC+FN[tag])
    gs=f.getGlyphSet(); cm=f.getBestCmap()
    cff2=f["CFF2"].cff; td=cff2[cff2.fontNames[0]]; csT=td.CharStrings
    gn=cm[ord("都")]
    rp=RecordingPen(); gs[gn].draw(rp)
    C=contours_from_pen(rp.value)
    h=m_radfoot.find(C)
    print("%s: %s" % (tag, h))
    if not h: f.close(); continue
    NEW=m_radfoot.apply(C,h)
    old=csT[gn]
    csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType=3.0; f["post"].fontOrder=None if False else None
    f["post"].glyphOrder=None
    p=os.path.join(OUT,"D_%s.otf"%tag)
    f.save(p); f.close()
    print("   saved "+p)