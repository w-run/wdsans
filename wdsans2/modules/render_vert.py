#!/usr/bin/env python3
import sys, json, os, subprocess
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image, ImageDraw, ImageFont

SRC = "/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"
NEW = "/workspace/wdsans2/build/tv2_all.otf"
MAP = json.load(open("/workspace/wdsans2/build/tv2_map.json"))
CHARS = list(MAP.keys())

# 原版字符 + 新版槽位
def render_char(path, ch_or_glyph, is_glyph=False, PX=560):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    gn = ch_or_glyph if is_glyph else cm[ord(ch_or_glyph)]
    bp = BoundsPen(gs); gs[gn].draw(bp)
    if not bp.bounds: f.close(); return None
    x0,y0,x1,y1 = bp.bounds
    pad = 40
    # 统一 viewBox: em 方框
    vb = (-50, -1050, 1100, 1100)
    sp = SVGPathPen(gs); gs[gn].draw(sp)
    d = sp.getCommands()
    f.close()
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%f %f %f %f" width="%d" height="%d">'
           '<rect x="%f" y="%f" width="%f" height="%f" fill="white"/>'
           '<g transform="scale(1,-1)"><path d="%s" fill="black"/></g></svg>') % (
           vb[0],vb[1],vb[2],vb[3],PX,PX, vb[0],vb[1],vb[2],vb[3], d)
    sp_path = "/tmp/v_%s.svg" % str(ch_or_glyph)
    open(sp_path,"w").write(svg)
    png = "/tmp/v_%s.png" % str(ch_or_glyph)
    subprocess.run(["/usr/bin/rsvg-convert","-w",str(PX),"-h",str(PX),"-o",png,sp_path], check=False, capture_output=True)
    return png if os.path.exists(png) else None

rows = []
for ch in CHARS:
    old = render_char(SRC, ch)
    new = render_char(NEW, MAP[ch], is_glyph=True)
    oppo = render_char("/workspace/wdsans/ref/ops/ops-400.ttf", ch)
    items = [("原版", old), ("改后", new), ("OPPO", oppo)]
    items = [(l,p) for l,p in items if p]
    if items:
        rows.append((ch, items))

if rows:
    PX = 560
    cols = max(len(r[1]) for r in rows)
    W = PX*cols
    H = PX*len(rows) + 30*len(rows)
    canvas = Image.new("RGB",(W,H),"white")
    dr = ImageDraw.Draw(canvas)
    try: lf = ImageFont.truetype("/workspace/wdsans/ref/shs/shs-400.otf", 22)
    except Exception: lf = ImageFont.load_default()
    y = 0
    for ch, items in rows:
        for i,(lbl,p) in enumerate(items):
            im = Image.open(p).convert("RGB")
            canvas.paste(im, (i*PX, y+30))
            dr.text((i*PX+6, y+4), "%s %s" % (ch, lbl), fill="red", font=lf)
        y += PX + 30
    canvas.save("/workspace/wdsans2/build/vert_grid.png")
    print("saved", canvas.size)
