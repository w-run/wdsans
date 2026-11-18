#!/usr/bin/env python3
# regen_poster_paths - regenerate poster SVG path data from CURRENT VF
#
# Bug: glyphdata.json was generated before the R31 seam fix, so poster-01
# (cover 永) and poster-02 (cell 04 钩) embedded the OLD path where the
# vertical-hook contour ended at (546,18) instead of closing on (543,17).
# Fonts were fixed but the hard-coded SVG data was not.
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
OUT = '/workspace/wdsans2/build/paths_fresh.json'

CHARS = "永口田王人今合会横竖撇捺折点提钩笔锋端面重心宫平顶结构"
CHARS += "了力几及目日一十中申甲国回"

f = TTFont(VF)
gs = f.getGlyphSet(); cm = f.getBestCmap(); hm = f["hmtx"]
out = {}
for ch in CHARS:
    if ord(ch) not in cm:
        continue
    gn = cm[ord(ch)]
    sp = SVGPathPen(gs)
    gs[gn].draw(sp)
    d = sp.getCommands()
    if d:
        out[ch] = {"d": d, "w": hm[gn][0]}
f.close()

json.dump(out, open(OUT, "w"), ensure_ascii=False)
print("saved %d glyphs -> %s" % (len(out), OUT))

# verify 永 c4 closure
y = out["永"]["d"]
parts = [p.strip() for p in y.split("Z") if p.strip()]
for i, p in enumerate(parts):
    if "V634" in p or ("463" in p and "634" in p):
        nums = [float(x) for x in __import__("re").findall(r"-?\d+\.?\d*", p)]
        print("c%d first=(%s,%s) last=(%s,%s)" % (i, nums[0], nums[1], nums[-2], nums[-1]))