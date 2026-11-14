#!/usr/bin/env python3
"""run_zerocont.py - zerocont 三档应用 (400档索引驱动)"""
import sys, os, json
import numpy as np
sys.path.insert(0,'/workspace/wdsans2/probe')
sys.path.insert(0,'/workspace/wdsans2/modules')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_zerocont as M

BASE = os.environ.get('WDS_BASE','/workspace/wdsans2/build/masters_MOD6')
OUTD = os.environ.get('WDS_OUT','/workspace/wdsans2/build/masters_MOD7')
IDX  = os.environ.get('WDS_INDEX','/workspace/wdsans2/build/idx_tinyarea.json')
FN = {'250':'master-ExtraLight-250.otf','400':'master-Regular-400.otf','900':'master-Heavy-900.otf'}
os.makedirs(OUTD, exist_ok=True)

# 索引格式: {'tiny': [[cp, ci, area], ...]} -> 按 cp 分组
raw = json.load(open(IDX))['tiny']
bycp = {}
for cp, ci, A in raw:
    bycp.setdefault(cp, []).append(ci)
print('索引 %d 字 %d 处'%(len(bycp), len(raw)), flush=True)

for tag in ['250','400','900']:
    f=TTFont(BASE+'/'+FN[tag]); cm=f.getBestCmap(); gs=f.getGlyphSet()
    cff2=f['CFF2'].cff; td=cff2[cff2.fontNames[0]]; csT=td.CharStrings
    nch=0; skip=0
    for cp, cis in bycp.items():
        if cp not in cm: continue
        gn=cm[cp]
        rp=RecordingPen(); gs[gn].draw(rp)
        if not rp.value: continue
        C=contours_from_pen(rp.value)
        if len(C) <= len(cis):
            skip+=1; continue
        NEW=M.apply(C, cis)
        if len(NEW) != len(C)-len(cis):
            skip+=1; continue
        old=csT[gn]; csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
        nch+=1
    f['post'].formatType=3.0; f['post'].glyphOrder=None
    out=OUTD+'/'+FN[tag]
    f.save(out); f.close()
    print('zerocont %s: 应用 %d 字 (跳过 %d) -> %s'%(tag,nch,skip,out), flush=True)
