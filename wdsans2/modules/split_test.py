#!/usr/bin/env python3
# split_test - 验证新切分法在更多字上的准确性
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_boxrad

def allpts(c):
    P=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: P.append(np.array(q,float))
        elif s[0]=="C": P.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q": P.extend([np.array(s[1],float),np.array(s[2],float)])
        else: P.append(np.array(s[1],float))
    return np.array(P)

def info(path, ch):
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    if ord(ch) not in cm: f.close(); return None
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    r=m_boxrad.split_lr(C)
    if not r: return None
    left,right=r
    ps=[allpts(c) for c in C]
    lx0=min(ps[i][:,0].min() for i in left); lx1=max(ps[i][:,0].max() for i in left)
    ly0=min(ps[i][:,1].min() for i in left); ly1=max(ps[i][:,1].max() for i in left)
    ry0=min(ps[i][:,1].min() for i in right); ry1=max(ps[i][:,1].max() for i in right)
    return lx0,lx1,ly0,ly1,(ly0+ly1)/2,(ry0+ry1)/2,len(left),len(right)

SRC="/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
SHS="/workspace/wdsans/ref/shs/shs-400.otf"
CH="叫叨叩叶叹叽叼叭叮叱昨晴暗晚旺昧昭昕晌晖明"
print("%-2s | %-30s | %-30s | %s" % ("ch","R32 左偏旁","SHS 左偏旁","判定"))
print("-"*88)
ok=0; bad=0; miss=0
for ch in CH:
    a=info(SRC,ch); b=info(SHS,ch)
    fa = "x[%3.0f,%3.0f] y[%4.0f,%4.0f] n%d" % (a[0],a[1],a[2],a[3],a[6]) if a else "  ---"
    fb = "x[%3.0f,%3.0f] y[%4.0f,%4.0f] n%d" % (b[0],b[1],b[2],b[3],b[6]) if b else "  ---"
    if a and b:
        dx = abs(a[0]-b[0])+abs(a[1]-b[1])
        v = "OK" if dx < 20 else "X(dx=%.0f)" % dx
        if dx < 20: ok+=1
        else: bad+=1
    elif a:
        v = "only-ours"; ok+=1
    else:
        v = "MISS"; miss+=1
    print("%-2s | %-30s | %-30s | %s" % (ch, fa, fb, v))
print()
print("切分: OK=%d bad=%d miss=%d" % (ok,bad,miss))