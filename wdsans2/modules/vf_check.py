#!/usr/bin/env python3
# vf_check - render 永 hook from deployed VF at 3 weights via instance
import sys, io
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
from PIL import Image, ImageDraw, ImageFont

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'


def endp(s):
    return np.array(s[1][-1], float) if s[0] == "QM" else np.array(s[-1], float)


def poly(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: P.append(np.array(q, float))
        elif s[0] == "C":
            P.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1],float), np.array(s[2],float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)


def area(P):
    x = P[:,0]; y = P[:,1]
    return 0.5*abs(float(np.dot(x, np.roll(y,1)) - np.dot(y, np.roll(x,1))))


for w in [250, 400, 900]:
    f = TTFont(VF)
    f = instantiateVariableFont(f, {"wght": w}, inplace=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("永")]].draw(rp)
    C = contours_from_pen(rp.value)
    seams = 0
    for c in C:
        if len(c["segs"]) < 3:
            continue
        st = np.array(c["start"], float)
        gap = float(np.hypot(*(endp(c["segs"][-1]) - st)))
        if 0.8 < gap < 12 and area(poly(c))/max(gap,1e-6) > 1000:
            seams += 1
    # render
    buf = io.BytesIO(); f.save(buf); f.close(); buf.seek(0)
    ft = ImageFont.truetype(buf, 700)
    img = Image.new("L", (1400, 1400), 255)
    ImageDraw.Draw(img).text((350, 350), "永", fill=0, font=ft)
    img.save("/workspace/wdsans2/build/vf_w%d.png" % w)
    print("  wght %d: seams=%d  saved vf_w%d.png" % (w, seams, w))