#!/usr/bin/env python3
# interp_check - 验证 VF 中间字重的插值平滑性
# 用拉丁字（CJK advance 恒定，测不出插值）
import sys, io
sys.path.insert(0, '/workspace/wdsans2/probe')
import uharfbuzz as hb
from fontTools.ttLib import TTFont

VF="/workspace/static/wdsans/WDesignSans-VF.otf"

def adv(text, wght):
    blob = hb.Blob.from_file_path(VF)
    face = hb.Face(blob)
    font = hb.Font(face)
    font.set_variations({"wght": wght})
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf)
    return sum(p.x_advance for p in buf.glyph_positions)

WEIGHTS = [250, 300, 350, 400, 500, 600, 700, 800, 900]
TESTS = [("Hamburgefonstiv", "拉丁"), ("minimum", "拉丁小写"), ("0123456789", "数字")]
for t, lbl in TESTS:
    vals = [adv(t, w) for w in WEIGHTS]
    mono = all(vals[i] < vals[i+1] for i in range(len(vals)-1))
    print("%-16s %s  %s" % (lbl, " ".join("%d" % v for v in vals), "单调递增 OK" if mono else "!!!"))

print()
print("CJK advance (应恒定 1000/字):")
for t in ["永", "永国字体", "永国字体设计的书"]:
    vals = [adv(t, w) for w in [250,400,700,900]]
    print("  %-10s %s" % (t, vals))