#!/usr/bin/env python3
# test_boxrad - 在几个字上试 m_boxrad, 测调整后的高度和中心
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_boxrad
from PIL import Image, ImageDraw, ImageFont

SRC = "/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
OUT = "/workspace/wdsans2/build/boxrad_test"
os.makedirs(OUT, exist_ok=True)
SZ = 1600; UPEM = 1000

CHARS = "叫叨叩叶叹叽叮叱昨晴暗"

f = TTFont(SRC)
gs = f.getGlyphSet(); cm = f.getBestCmap()
cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
n = 0; hitc = []
for ch in CHARS:
    if ord(ch) not in cm: continue
    gn = cm[ord(ch)]
    rp = RecordingPen(); gs[gn].draw(rp)
    C = contours_from_pen(rp.value)
    hits = m_boxrad.find(C)
    if not hits: continue
    NEW = m_boxrad.apply(C, hits)
    old = csT[gn]
    csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
    n += 1; hitc.append(ch)
f["post"].formatType = 3.0; f["post"].glyphOrder = None
p = os.path.join(OUT, "B.otf")
f.save(p); f.close()
print("改动 %d 字: %s" % (n, "".join(hitc)))

def leftband(path, ch, frac=0.42):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    if not len(r): return None
    a = a[r[0]:r[-1]+1, c[0]:c[-1]+1]
    H, W = a.shape
    L = a[:, :int(W*frac)]
    ys = np.where(L.any(axis=1))[0]
    if not len(ys): return None
    sc = UPEM/H
    return ys[0]*sc, ys[-1]*sc, (ys[-1]-ys[0])*sc, (ys[0]+ys[-1])/2*sc

S = "/workspace/wdsans/ref/shs/shs-400.otf"
print()
print("%-2s | %-24s | %-24s | %-24s" % ("ch","R32原始","m_boxrad后","SHS基准"))
print("-"*82)
for ch in CHARS:
    a = leftband(SRC, ch); b = leftband(p, ch); c = leftband(S, ch)
    if not a or not b: continue
    fmt = lambda t: "[%4.0f,%4.0f] h%3.0f c%3.0f" % (t[0],t[1],t[2],t[3]) if t else "--"
    print("%-2s | %-24s | %-24s | %-24s" % (ch, fmt(a), fmt(b), fmt(c)))