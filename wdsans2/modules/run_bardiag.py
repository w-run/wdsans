#!/usr/bin/env python3
"""run_bardiag.py - bardiag 三档应用 (400档索引驱动)

索引格式: {cp: [(bi,di,by0,by1,xo0,xo1), ...]}
三档按同一索引应用, 保证结构一致。
"""
import sys, os, json
sys.path.insert(0,'/workspace/wdsans2/probe')
sys.path.insert(0,'/workspace/wdsans2/modules')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_bardiag as M

BASE = os.environ.get('WDS_BASE','/workspace/wdsans2/build/masters_MOD2')
OUTD = os.environ.get('WDS_OUT','/workspace/wdsans2/build/masters_MOD3')
IDX  = os.environ.get('WDS_INDEX','/workspace/wdsans2/build/idx_bardiag.json')
FN = {'250':'master-ExtraLight-250.otf','400':'master-Regular-400.otf','900':'master-Heavy-900.otf'}
os.makedirs(OUTD, exist_ok=True)

def do_apply(tag, hits_all):
    f=TTFont(BASE+'/'+FN[tag]); cm=f.getBestCmap(); gs=f.getGlyphSet()
    cff2=f['CFF2'].cff; td=cff2[cff2.fontNames[0]]; csT=td.CharStrings
    nch=0
    for k,v in hits_all.items():
        cp=int(k)
        if cp not in cm: continue
        gn=cm[cp]
        rp=RecordingPen(); gs[gn].draw(rp)
        if not rp.value: continue
        C=contours_from_pen(rp.value)
        NEW=M.apply(C, v)
        old=csT[gn]; csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
        nch+=1
    f['post'].formatType=3.0; f['post'].glyphOrder=None
    out=OUTD+'/'+FN[tag]
    f.save(out); f.close()
    print('bardiag %s: 应用 %d 字 -> %s'%(tag,nch,out), flush=True)

hits=json.load(open(IDX))['hits']
print('索引 %d 字'%len(hits), flush=True)
for tag in ['250','400','900']:
    do_apply(tag, hits)
