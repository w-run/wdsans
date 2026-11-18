#!/usr/bin/env python3
# seam_visual - are these seams visible in rendering? bitmap test
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

P = '/workspace/wdsans2/build/masters_R30/master-Regular-400.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'

TESTS = "丁七万下不与丏丐丑丙业东丝永"


def frag(path, ch, size=96):
    ft = ImageFont.truetype(path, size)
    img = Image.new("L", (size*2, size*2), 0)
    ImageDraw.Draw(img).text((size//3, size//3), ch, fill=255, font=ft)
    a = np.array(img) > 128
    lab, n = ndimage.label(a)
    return n, a.sum()


print('%-4s %-14s %-14s %s' % ('char', 'R30 blocks/ink', 'SHS blocks/ink', 'diff'))
for ch in TESTS:
    try:
        n1, i1 = frag(P, ch)
        n2, i2 = frag(SHS, ch)
        d = n1 - n2
        mark = "  <<<" if abs(d) >= 2 else ""
        print("%-4s %-14s %-14s %+d%s" % (ch, "%d/%d" % (n1, i1), "%d/%d" % (n2, i2), d, mark))
    except Exception as e:
        print("%-4s ERR %s" % (ch, e))

print()
print('=== 结论判据: 块数差 >= 2 说明有真实断裂 ===')