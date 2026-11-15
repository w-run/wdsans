#!/usr/bin/env python3
"""run_residue.py - 清理前面模块改动后新产生的 residue

三个模块依次在 MOD9c 上应用:
  1. m_barple   1 字   1 处
  2. m_stepalign 188 字 192 处
  3. m_bardiag   29 字  30 处

顺序: barple -> stepalign -> bardiag
  每步之后重新检测下一步, 因为前一步会改变几何
三档按 400 档索引应用
"""
import sys, os, json
import numpy as np
sys.path.insert(0,'/workspace/wdsans2/probe')
sys.path.insert(0,'/workspace/wdsans2/modules')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_barple as BP, m_stepalign as SA, m_bardiag as BD

BASE = os.environ.get('WDS_BASE','/workspace/wdsans2/build/masters_MOD9c')
OUTD = os.environ.get('WDS_OUT','/workspace/wdsans2/build/masters_MOD10')
FN = {'250':'master-ExtraLight-250.otf','400':'master-Regular-400.otf','900':'master-Heavy-900.otf'}
SW400 = 77.0
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

# 1) 400 档依次检测三个模块, 累积索引
f400=TTFont(BASE+'/'+FN['400'])
cm400=f400.getBestCmap(); gs400=f400.getGlyphSet()
cps=[cp for cp in sorted(cm400.keys()) if 0x4E00<=cp<=0x9FFF]
all_idx={}   # cp -> [(mod_name, hits)]
for cp in cps:
    try:
        rp=RecordingPen(); gs400[cm400[cp]].draw(rp)
        C=contours_from_pen(rp.value) if rp.value else []
    except Exception: continue
    if not C: continue
    steps=[]
    for name,mod in [('barple',BP),('stepalign',SA),('bardiag',BD)]:
        try: h=mod.find(C,SW400)
        except Exception: h=[]
        if h:
            steps.append([name, [[int(x) for x in (o if isinstance(o,(list,tuple)) else [o])] for o in h]])
            try: C=mod.apply(C,h)
            except Exception: pass
    if steps: all_idx[str(cp)]=steps
f400.close()
n1=sum(1 for v in all_idx.values() for _ in v)
print('400档 residue: %d 字 %d 步'%(len(all_idx),n1), flush=True)

# 2) 三档应用
MODS={'barple':BP,'stepalign':SA,'bardiag':BD}
for tag in ['250','400','900']:
    f=TTFont(BASE+'/'+FN[tag]); cm=f.getBestCmap(); gs=f.getGlyphSet()
    cff2=f['CFF2'].cff; td=cff2[cff2.fontNames[0]]; csT=td.CharStrings
    nch=0; skip=0
    for k,steps in all_idx.items():
        cp=int(k)
        if cp not in cm: continue
        gn=cm[cp]
        rp=RecordingPen(); gs[gn].draw(rp)
        if not rp.value: continue
        C=contours_from_pen(rp.value)
        ok=True
        for name,hs in steps:
            mod=MODS[name]
            # 校验索引段号有效
            for o in hs:
                ci=o[0]
                if ci>=len(C): ok=False; break
                for idx in o[1:]:
                    if idx>=len(C[ci]['segs']): ok=False; break
                if not ok: break
            if not ok: break
            try:
                C=mod.apply(C,[tuple(o) for o in hs])
            except Exception:
                ok=False; break
        if not ok:
            skip+=1; continue
        NEW=C
        if zero_count(NEW)>zero_count(contours_from_pen(RecordingPen().value) if False else NEW): pass
        old=csT[gn]; csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
        nch+=1
    f['post'].formatType=3.0; f['post'].glyphOrder=None
    out=OUTD+'/'+FN[tag]
    f.save(out); f.close()
    print('residue %s: 应用 %d 字 (跳过 %d)'%(tag,nch,skip), flush=True)
