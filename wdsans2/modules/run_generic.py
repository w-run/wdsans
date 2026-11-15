#!/usr/bin/env python3
"""run_generic.py - 通用 find/apply 模块三档执行器

用法: python run_generic.py <模块名> <基座目录> <输出目录> [索引json]

从 400 档检测 -> 三档同一索引应用，保证段数与操作符一致。
"""
import sys, os, json, importlib
sys.path.insert(0,'/workspace/wdsans2/probe')
sys.path.insert(0,'/workspace/wdsans2/modules')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

MOD = sys.argv[1]
BASE = sys.argv[2]
OUTD = sys.argv[3]
IDX = sys.argv[4] if len(sys.argv)>4 else '/workspace/wdsans2/build/idx_%s.json'%MOD
SW = {'250':30.0,'400':77.0,'900':150.0}
FN = {'250':'master-ExtraLight-250.otf','400':'master-Regular-400.otf','900':'master-Heavy-900.otf'}
os.makedirs(OUTD, exist_ok=True)
M = importlib.import_module(MOD)

def contours(gs, gn):
    rp = RecordingPen()
    try: gs[gn].draw(rp)
    except Exception: return None
    C = contours_from_pen(rp.value)
    return C if C else None

# 1) 400 档检测
f = TTFont(BASE+'/'+FN['400'], lazy=True)
cm = f.getBestCmap(); gs = f.getGlyphSet()
cjk = [(cp,gn) for cp,gn in cm.items() if 0x4E00<=cp<=0x9FFF]
f.close()
index = {}
for cp,gn in cjk:
    C = contours(gs,gn)
    if not C: continue
    try: hits = M.find(C, SW['400'])
    except Exception: continue
    if hits: index[cp] = hits
nhit = sum(len(v) for v in index.values())
print('%s: 命中 %d 字 / %d 处'%(MOD, len(index), nhit), flush=True)
json.dump({str(k):v for k,v in index.items()}, open(IDX,'w'))

if not index: sys.exit(0)

# 2) 三档应用
for tag in ['250','400','900']:
    f = TTFont(BASE+'/'+FN[tag])
    cm = f.getBestCmap(); gs = f.getGlyphSet()
    cff2 = f['CFF2'].cff
    td = cff2[cff2.fontNames[0]]
    csT = td.CharStrings
    done = 0; skip = 0
    for cp, hits in index.items():
        gn = cm.get(cp)
        if not gn: skip+=1; continue
        C = contours(gs,gn)
        if not C: skip+=1; continue
        try:
            NEW = M.apply(C, hits)
        except Exception:
            skip+=1; continue
        if not NEW: skip+=1; continue
        old = csT[gn]
        csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
        done += 1
    print('  %s: 应用 %d 跳过 %d'%(tag,done,skip), flush=True)
    f['post'].formatType = 3.0
    f['post'].glyphOrder = None
    f.save(OUTD+'/'+FN[tag])
    f.close()
print('完成 -> %s'%OUTD)
