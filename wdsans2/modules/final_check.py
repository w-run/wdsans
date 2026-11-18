#!/usr/bin/env python3
# final_check - 用已确认的 SHS 基准表逐字核对 R33
import sys, json
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_boxrad

D="/workspace/wdsans2/build/masters_R33/"
FN={"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
idx=json.load(open(D+"boxrad_index.json"))

# 已确认的 SHS 400档基准 (来自 shs_bench.py 实测)
SHS400 = {
"叫":(79,749),"叨":(86,748),"叩":(96,766),"叽":(88,748),"叮":(88,748),
"叱":(85,737),"昨":(30,762),"晴":(36,771),"暗":(28,767),"晚":(36,769),
"旺":(35,767),"昧":(28,767),"昭":(33,765),"昕":(30,767),"晌":(36,771),
"晖":(36,771),"明":(88,779)}

def mine(path, ch, lid):
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    if ord(ch) not in cm: f.close(); return None
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    ps=[m_boxrad.allpts(c) for c in C]
    if lid is None or max(lid)>=len(ps): return None
    y0=min(ps[i][:,1].min() for i in lid); y1=max(ps[i][:,1].max() for i in lid)
    return y0,y1,y1-y0,(y0+y1)/2

print("R33 vs SHS (400档)")
print("%-2s | %-22s | %-22s | %s" % ("ch","R33","SHS","判定"))
print("-"*72)
ok=0; tot=0
for ch,(sy0,sy1) in SHS400.items():
    lid=idx.get(str(ord(ch)))
    a=mine(D+FN["400"], ch, lid)
    if not a: continue
    tot+=1
    sh=sy1-sy0; sc=(sy0+sy1)/2
    dh=a[2]-sh; dc=a[3]-sc
    v = "OK" if abs(dh)<25 and abs(dc)<25 else "!!"
    if v=="OK": ok+=1
    print("%-2s | h%3.0f c%3.0f y[%4.0f,%4.0f] | h%3.0f c%3.0f y[%4.0f,%4.0f] | dh%+4.0f dc%+4.0f %s" % (
        ch, a[2],a[3],a[0],a[1], sh,sc,sy0,sy1, dh,dc,v))
print()
print("--> %d/%d 匹配" % (ok,tot))