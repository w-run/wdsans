#!/usr/bin/env python3
# sig_3w - verify three-weight operator signature consistency (VF gate)
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

B = '/workspace/wdsans2/build/masters_R31/'
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}


sigs = {}
for tag, fn in FN.items():
    f = TTFont(B + fn, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    d = {}
    for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
        gn = cm[cp]
        rp = RecordingPen()
        try:
            gs[gn].draw(rp)
        except Exception:
            continue
        sig = []
        n = 0
        for op, a in rp.value:
            if op == "moveTo":
                sig.append("|" + str(n))
            elif op == "lineTo":
                sig.append("L")
            elif op == "curveTo":
                sig.append("C")
            elif op == "qCurveTo":
                sig.append("Q")
            n += 1
        d[cp] = "".join(sig)
    f.close()
    sigs[tag] = d

base = sigs["400"]
for tag in ["250", "900"]:
    bad = [cp for cp in base if cp in sigs[tag] and sigs[tag][cp] != base[cp]]
    print("%s vs 400: %d mismatches %s" % (tag, len(bad), "".join(chr(c) for c in bad[:10])))
    if bad:
        cp = bad[0]
        print("   e.g. %s  400=%s  %s=%s" % (chr(cp), base[cp][:40], tag, sigs[tag][cp][:40]))