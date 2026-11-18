#!/usr/bin/env python3
# sig_R33 - 三档签名校验
import sys, json
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

D = "/workspace/wdsans2/build/masters_R33/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
idx = json.load(open(D + "boxrad_index.json"))
cps = [int(k) for k in idx]

def sigs(path, cps):
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    out={}
    for cp in cps:
        if cp not in cm: continue
        rp=RecordingPen()
        try: gs[cm[cp]].draw(rp)
        except Exception: continue
        C=contours_from_pen(rp.value)
        out[cp]=["".join(s[0] for s in c["segs"]) for c in C]
    f.close(); return out

print("校验 %d 字（改动集）" % len(cps))
a=sigs(D+FN["250"], cps); b=sigs(D+FN["400"], cps); c=sigs(D+FN["900"], cps)
bad1=bad2=0
for cp in cps:
    if cp not in a or cp not in b or cp not in c: continue
    if a[cp]!=b[cp]: bad1+=1
    if c[cp]!=b[cp]: bad2+=1
print("250 vs 400 不一致: %d" % bad1)
print("900 vs 400 不一致: %d" % bad2)
print("PASS" if bad1==0 and bad2==0 else "FAIL")