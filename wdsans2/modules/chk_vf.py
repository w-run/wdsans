import sys
sys.path.insert(0,'/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

VF='/workspace/static/wdsans/WDesignSans-VF.otf'
f=TTFont(VF,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
def tb(ch):
    if ord(ch) not in cm: return None
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    cs=[];cur=None
    for op,args in rp.value:
        if op=='moveTo':
            if cur: cs.append(cur)
            cur=[tuple(args[0])]
        elif op in ('lineTo','curveTo','qCurveTo'):
            if cur:
                for a in args:
                    if hasattr(a,'__len__') and len(a)==2 and not isinstance(a[0],(list,tuple)):
                        cur.append(tuple(a))
        elif op=='closePath':
            if cur: cs.append(cur)
            cur=None
    if cur: cs.append(cur)
    gx1=max(p[0] for c in cs for p in c); gmax=max(p[1] for c in cs for p in c)
    best=None
    for c in cs:
        xs=[p[0] for p in c]; ys=[p[1] for p in c]
        w=max(xs)-min(xs); h=max(ys)-min(ys)
        if w<300 or w/max(h,1)<2.5: continue
        if max(ys)<gmax-320: continue
        m=gx1-max(xs)
        if best is None or m<best: best=m
    return (gx1,best)
print('部署版 VF (R29) 顶部横笔右余:')
for ch in '各冬条备务形几散':
    r=tb(ch)
    print('  %s  %s'%(ch,('余%.0f'%r[1]) if r and r[1] is not None else '-'))
print()
print('对照组（不应有整字顶横）:')
for ch in '口回十中田日':
    r=tb(ch)
    print('  %s  %s'%(ch,('余%.0f'%r[1]) if r and r[1] is not None else '-'))
f.close()
