#!/usr/bin/env python3
# step_visual - bitmap test: does a step actually show as a notch?
#
# Per AGENTS.md methodology, geometric candidates must be confirmed at the
# bitmap layer. Test: render the glyph, scan its right profile, look for a
# local x jump between adjacent rows.
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R31 = '/workspace/wdsans2/build/masters_R31/master-Regular-400.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'

SZ = 400


def right_profile(path, ch):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//3, SZ//3), ch, fill=255, font=ft)
    a = np.array(img) > 128
    rows = np.where(a.any(axis=1))[0]
    if not len(rows):
        return None
    prof = []
    for y in rows:
        xs = np.where(a[y])[0]
        prof.append(xs[-1] if len(xs) else -1)
    return np.array(prof)


def max_step(prof):
    """largest inward jump of right edge between adjacent rows"""
    if prof is None or len(prof) < 3:
        return 0
    d = np.diff(prof.astype(int))
    return int(-d.min()) if d.min() < 0 else 0


TESTS = "及永力了刀九几乃予勇另"
print('%-4s %-10s %-10s %s' % ('char', 'R31 maxstep', 'SHS maxstep', 'diff'))
for ch in TESTS:
    try:
        a = max_step(right_profile(R31, ch))
        b = max_step(right_profile(SHS, ch))
        mark = "  <<<" if a - b >= 8 else ""
        print("%-4s %-10d %-10d %+d%s" % (ch, a, b, a-b, mark))
    except Exception as e:
        print("%-4s ERR %s" % (ch, e))