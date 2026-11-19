#!/usr/bin/env python3
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
cm = f.getBestCmap(); gs = f.getGlyphSet()

print("=== 现有字形的曲线类型分布 ===")
found_qm = 0; checked = 0
SAMPLES = [(0x00B7, chr(0xB7)), (0x2026, chr(0x2026)), (0x2014, chr(0x2014)), (0x3001, chr(0x3001)), (0x4E00, chr(0x4E00))]
for cp, ch in SAMPLES:
    if cp not in cm: continue
    gn = cm[cp]
    rp = RecordingPen()
    try:
        gs[gn].draw(rp)
    except Exception:
        continue
    C = contours_from_pen(rp.value)
    sig = "/".join("".join(s[0] for s in c["segs"]) for c in C)
    has_qm = ("QM" in sig) or ("Q" in sig.replace("QM",""))
    checked += 1
    if has_qm: found_qm += 1
    print("  U+%04X %-3s %-24s %s" % (cp, ch, sig[:24], "有二次" if has_qm else ""))

print()
print("  检查 %d 个，%d 个含二次曲线" % (checked, found_qm))
f.close()