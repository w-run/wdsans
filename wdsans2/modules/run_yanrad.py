#!/usr/bin/env python3
"""run_yanrad.py - yanrad 三档应用 (400档索引驱动)"""
import sys, os, json
sys.path.insert(0,'/workspace/wdsans2/probe')
sys.path.insert(0,'/workspace/wdsans2/modules')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_yanrad as M

BASE = os.environ.get('WDS_BASE','/workspace/wdsans2/build/masters_MOD4')
OUTD = os.environ.get('WDS_OUT','/workspace/wdsans2/build/masters_MOD5')
IDX  = os.environ.get('WDS_INDEX','/workspace/wdsans2/build/idx_yanrad.json')
FN = {'250':'master-ExtraLight-250.otf','400':'master-Regular-400.otf','900':'master-Heavy-900.otf'}
os.makedirs(OUTD, exist_ok=True)

def endp(s):
    if s[0]=='QM': return np.array(s[1][-1],float)
    return np.array(s[-1],float)

def zero_count(C):
    n=0
    for c in C:
        q=[np.array(c['start'],float)]+[endp(s) for s in c['segs']]
        for i in range(len(q)-1):
            if float(np.linalg.norm(q[i+1]-q[i]))<0.01: n+=1
    return n

import numpy as np

hits_all = json.load(open(IDX))['hits']
print('索引 %d 字'%len(hits_all), flush=True)

for tag in ['250','400','900']:
    f=TTFont(BASE+'/'+FN[tag]); cm=f.getBestCmap(); gs=f.getGlyphSet()
    cff2=f['CFF2'].cff; td=cff2[cff2.fontNames[0]]; csT=td.CharStrings
    nch=0; skip=0
    for k,v in hits_all.items():
        cp=int(k)
        if cp not in cm: continue
        gn=cm[cp]
        rp=RecordingPen(); gs[gn].draw(rp)
        if not rp.value: continue
        C=contours_from_pen(rp.value)
        NEW=M.apply(C, v)
        z0,z1=zero_count(C),zero_count(NEW)
        if z1>z0:
            skip+=1; continue
        old=csT[gn]; csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
        nch+=1
    f['post'].formatType=3.0; f['post'].glyphOrder=None
    out=OUTD+'/'+FN[tag]
    f.save(out); f.close()
    print('yanrad %s: 应用 %d 字 (跳过 %d) -> %s'%(tag,nch,skip,out), flush=True)
