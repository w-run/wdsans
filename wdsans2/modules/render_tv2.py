#!/usr/bin/env python3
import sys, json, os, subprocess
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image, ImageDraw, ImageFont

TV = "/workspace/wdsans2/build/tv_all.otf"
MAPPING = json.load(open("/workspace/wdsans2/build/tv_map.json"))
ORDER = ["orig","L","Ls20","Ls40","Lp15","Lp30"]
LABEL = {"orig":"原版","L":"C->L直拉","Ls20":"L+收20","Ls40":"L+收40",
         "Lp15":"L+法向15","Lp30":"L+法向30"}

f = TTFont(TV, lazy=True)
gs = f.getGlyphSet()

# 统一 bbox（取原版的，保证可比）
gn0 = MAPPING["orig"]
bp = BoundsPen(gs)
gs[gn0].draw(bp)
x0,y0,x1,y1 = bp.bounds
pad = 40
vb = (x0-pad, -(y1+pad), (x1-x0)+2*pad, (y1-y0)+2*pad)
print("viewBox: x=%.0f y=%.0f w=%.0f h=%.0f" % vb)

PX = 700
tiles = []
for tag in ORDER:
    gname = MAPPING[tag]
    sp = SVGPathPen(gs)
    gs[gname].draw(sp)
    d = sp.getCommands()
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.0f %.0f %.0f %.0f" '
           'width="%d" height="%d"><rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" fill="white"/>'
           '<g transform="scale(1,-1)"><path d="%s" fill="black"/></g></svg>') % (vb[0], vb[1], vb[2], vb[3], PX, PX,
                                                    vb[0], vb[1], vb[2], vb[3], d)
    sp_path = "/tmp/tv2_%s.svg" % tag
    open(sp_path, "w").write(svg)
    png = "/tmp/tv2_%s.png" % tag
    subprocess.run(["/usr/bin/rsvg-convert", "-w", str(PX), "-h", str(PX), "-o", png, sp_path],
                   check=False, capture_output=True)
    if os.path.exists(png):
        tiles.append((tag, png))
f.close()
print("渲染 %d 个" % len(tiles))

if tiles:
    ims = [(t, Image.open(p).convert("RGB")) for t, p in tiles]
    W = sum(i.width for _, i in ims)
    H = max(i.height for _, i in ims) + 44
    canvas = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(canvas)
    try:
        lf = ImageFont.truetype("/workspace/wdsans/ref/shs/shs-400.otf", 26)
    except Exception:
        lf = ImageFont.load_default()
    x = 0
    for tag, im in ims:
        canvas.paste(im, (x, 44))
        dr.text((x+8, 8), LABEL.get(tag, tag), fill="red", font=lf)
        x += im.width
    canvas.save("/workspace/wdsans2/build/tv_grid2.png")
    print("saved", canvas.size)
