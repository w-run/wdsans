#!/usr/bin/env python3
# verify_R34 - 签名校验 + 都出脚确认
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_radfoot

D = "/workspace/wdsans2/build/masters_R34/"
P = "/workspace/wdsans2/build/masters_R33/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
CHARS = "僘厥塑嵞朔槊磊蒴都鬬鬭"

def sigs(path, chars):
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    out={}
    for ch in chars:
        if ord(ch) not in cm: continue
        rp=RecordingPen()
        try: gs[cm[ord(ch)]].draw(rp)
        except Exception: continue
        C=contours_from_pen(rp.value)
        out[ch]=["".join(s[0] for s in c["segs"]) for c in C]
    f.close(); return out

a=sigs(D+FN["250"], CHARS); b=sigs(D+FN["400"], CHARS); c=sigs(D+FN["900"], CHARS)
bad1=bad2=0
for ch in CHARS:
    if ch not in a or ch not in b or ch not in c: continue
    if a[ch]!=b[ch]: bad1+=1
    if c[ch]!=b[ch]: bad2+=1
print("R34 三档签名: 250vs400=%d  900vs400=%d  %s" % (bad1,bad2,"PASS" if bad1==bad2==0 else "FAIL"))

print()
print("都 出脚确认 (竖条底 vs 方框底):")
for tag in ["250","400","900"]:
    for lbl,path in [("R33前",P+FN[tag]),("R34后",D+FN[tag])]:
        f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
        rp=RecordingPen(); gs[cm[ord("都")]].draw(rp); f.close()
        C=contours_from_pen(rp.value)
        ps=[m_radfoot.allpts(c) for c in C]
        h=m_radfoot.find(C) if lbl=="R33前" else None
        # 找日旁的竖条 (c7) 和方框 (c6)
        if len(ps)>7:
            d = ps[6][:,1].min() - ps[7][:,1].min()
            print("  %s %s: 方框底%.0f 竖条底%.0f 出脚%.0f" % (tag,lbl,ps[6][:,1].min(),ps[7][:,1].min(),d))