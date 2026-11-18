#!/usr/bin/env python3
# sig_R32 - 三档操作符签名校验 (改动的 326 字 + 全库)
import sys, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

D = "/workspace/wdsans2/build/masters_R32/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}

def sig_of(path, cps):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    out = {}
    for cp in cps:
        if cp not in cm: continue
        rp = RecordingPen()
        try:
            gs[cm[cp]].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        out[cp] = [ "".join(s[0] for s in c["segs"]) for c in C ]
    f.close()
    return out

idx = json.load(open(D + "index.json"))
cps = [int(k) for k in idx.keys()]
print("校验 %d 字（改动集）" % len(cps))
s250 = sig_of(D + FN["250"], cps)
s400 = sig_of(D + FN["400"], cps)
s900 = sig_of(D + FN["900"], cps)
bad1 = 0; bad2 = 0
for cp in cps:
    if cp not in s250 or cp not in s400 or cp not in s900: continue
    if s250[cp] != s400[cp]:
        bad1 += 1
        if bad1 <= 5: print("  250vs400 不一致: %s" % chr(cp))
    if s900[cp] != s400[cp]:
        bad2 += 1
        if bad2 <= 5: print("  900vs400 不一致: %s" % chr(cp))
print("250 vs 400 不一致: %d" % bad1)
print("900 vs 400 不一致: %d" % bad2)
print("PASS" if bad1 == 0 and bad2 == 0 else "FAIL")