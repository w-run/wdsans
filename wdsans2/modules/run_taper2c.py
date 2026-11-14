#!/usr/bin/env python3
"""run_taper2c.py - taper v2 三档索引驱动（保存完整 (ci,k,j) 三元组）

修复上一版错误:
  - 之前只存 [ci, k] 丢了 j, 导致 apply 无法执行
  - 之前用 T.find(C, 77.0) 在 250 档检测, 段长判据不匹配, 只命中 56 字

正确做法:
  1. 只在 400 档调用 T.find(C, 77.0) 得到完整 (ci,k,j) 三元组
  2. 三档直接用这份三元组调 T.apply(C, ops) —— apply 只按段号操作, 与 SW 无关
"""
import sys, os, json
import numpy as np
sys.path.insert(0,'/workspace/wdsans2/probe')
sys.path.insert(0,'/workspace/wdsans2/modules')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_taper as T

BASE = os.environ.get('WDS_BASE','/workspace/wdsans2/build/masters_MOD8')
OUTD = os.environ.get('WDS_OUT','/workspace/wdsans2/build/masters_MOD9c')
IDX  = os.environ.get('WDS_INDEX','/workspace/wdsans2/build/idx_taper2c.json')
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

if os.path.exists(IDX):
    idx=json.load(open(IDX))['hits']
    print('复用已有索引 %d 字'%len(idx), flush=True)
else:
    f400=TTFont(BASE+'/'+FN['400'])
    cm400=f400.getBestCmap(); gs400=f400.getGlyphSet()
    cps=[cp for cp in sorted(cm400.keys()) if 0x4E00<=cp<=0x9FFF]
    idx={}
    for cp in cps:
        try:
            rp=RecordingPen(); gs400[cm400[cp]].draw(rp)
            C=contours_from_pen(rp.value) if rp.value else []
        except Exception: continue
        if not C: continue
        try:
            ops=T.find(C, 77.0)
        except Exception: continue
        if ops:
            idx[str(cp)]=[[int(o[0]),int(o[1]),int(o[2])] for o in ops]
    f400.close()
    print('400档检测: %d 字, %d 处'%(len(idx), sum(len(v) for v in idx.values())), flush=True)
    json.dump({'hits':idx}, open(IDX,'w'))

for tag in ['250','400','900']:
    f=TTFont(BASE+'/'+FN[tag]); cm=f.getBestCmap(); gs=f.getGlyphSet()
    cff2=f['CFF2'].cff; td=cff2[cff2.fontNames[0]]; csT=td.CharStrings
    nch=0; skip=0
    for k,v in idx.items():
        cp=int(k)
        if cp not in cm: continue
        gn=cm[cp]
        rp=RecordingPen(); gs[gn].draw(rp)
        if not rp.value: continue
        C=contours_from_pen(rp.value)
        ops=[tuple(o) for o in v]
        # 校验段号在范围内
        ok=True
        for ci,segk,segnj in ops:
            if ci>=len(C) or segk>=len(C[ci]['segs']) or segnj>=len(C[ci]['segs']):
                ok=False; break
        if not ok:
            skip+=1; continue
        try:
            NEW=T.apply(C, ops)
        except Exception:
            skip+=1; continue
        if zero_count(NEW)>zero_count(C):
            skip+=1; continue
        old=csT[gn]; csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
        nch+=1
    f['post'].formatType=3.0; f['post'].glyphOrder=None
    out=OUTD+'/'+FN[tag]
    f.save(out); f.close()
    print('taper2c %s: 应用 %d 字 (跳过 %d)'%(tag,nch,skip), flush=True)
