#!/usr/bin/env python3
"""run_latinmat.py - 拉丁横向缩放三档应用

每档独立应用（缩放在各档作用相同，不涉及阈值判断）
"""
import sys, os
import numpy as np
sys.path.insert(0,'/workspace/wdsans2/probe')
sys.path.insert(0,'/workspace/wdsans2/modules')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_latinmat as LM

BASE = os.environ.get('WDS_BASE','/workspace/wdsans2/build/masters_MOD10')
OUTD = os.environ.get('WDS_OUT','/workspace/wdsans2/build/masters_MOD12')
FN = {'250':'master-ExtraLight-250.otf','400':'master-Regular-400.otf','900':'master-Heavy-900.otf'}
os.makedirs(OUTD, exist_ok=True)

for tag in ['250','400','900']:
    f=TTFont(BASE+'/'+FN[tag]); cm=f.getBestCmap(); gs=f.getGlyphSet()
    cff2=f['CFF2'].cff; td=cff2[cff2.fontNames[0]]; csT=td.CharStrings
    n=0
    for cp,gn in cm.items():
        if not LM.is_latin(cp): continue
        rp=RecordingPen(); gs[gn].draw(rp)
        if not rp.value: continue
        C=contours_from_pen(rp.value)
        if not C: continue
        NEW=LM.scale_contours(C, LM.SCALE)
        old=csT[gn]; csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
        n+=1
    f['post'].formatType=3.0; f['post'].glyphOrder=None
    out=OUTD+'/'+FN[tag]
    f.save(out); f.close()
    print('latinmat %s: 改 %d 字形'%(tag,n), flush=True)
