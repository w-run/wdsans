#!/usr/bin/env python3
"""crop.py - 按 bbox 比例裁剪渲染 (避免猜绝对坐标)

用法: crop.py <字符> <左> <右> <下> <上> [font1:label ...]
      比例 0~1 相对该字 bbox
"""
import sys, numpy as np, os, subprocess
sys.path.insert(0,'/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from canonpen3 import contours_from_pen

def load(fp,ch):
    f=TTFont(fp); cm=f.getBestCmap()
    if ord(ch) not in cm: f.close(); return None,None
    gs=f.getGlyphSet(); gn=cm[ord(ch)]
    sp=SVGPathPen(gs); gs[gn].draw(sp)
    bp=BoundsPen(gs); gs[gn].draw(bp)
    f.close()
    return sp.getCommands(), bp.bounds

def main():
    ch=sys.argv[1]
    fL,fR,fB,fT=[float(x) for x in sys.argv[2:6]]
    fonts=[s.split(':') for s in sys.argv[6:]]
    # 先用第一个字体求 bbox
    d0,bb0=load(fonts[0][0],ch)
    if bb0 is None:
        print('no glyph'); return
    x0,y0,x1,y1=bb0
    w=x1-x0; h=y1-y0
    win=(x0+fL*w, x0+fR*w, y0+fB*h, y0+fT*h)
    print('bbox=(%.0f,%.0f,%.0f,%.0f)  win=(%.0f,%.0f,%.0f,%.0f)'%(x0,y0,x1,y1,*win))

    cells=[]
    for fp in fonts:
        d,bb=load(fp[0],ch)
        if d is None: continue
        lbl=fp[1] if len(fonts[0])>1 and len(fp)>1 else os.path.basename(fp[0])
        cells.append(('%s %s'%(ch,lbl), d, bb))
    if not cells: return

    wx0,wx1,wy0,wy1=win
    cw=460
    k=cw/(wx1-wx0)
    H=int(cw*(wy1-wy0)/(wx1-wx0))
    W=cw*len(cells)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'%(W,H,W,H)]
    parts.append('<rect width="%d" height="%d" fill="#fff"/>'%(W,H))
    for i,(lbl,d,bb) in enumerate(cells):
        ox=i*cw
        # 字体坐标 y 向上; SVG y 向下. 变换: x'=(x-wx0)*k+ox, y'=(wy1-y)*k
        parts.append('<g transform="translate(%f,%f) scale(%f,%f) translate(%f,%f)">'%(ox,wy1*k,k,-k,-wx0,0))
        # 网格 每 25 单位
        parts.append('<g stroke="#dcdcdc" stroke-width="%.2f" fill="none">'%(0.8/k))
        gx=int(np.floor(wx0/25))*25
        while gx<=wx1:
            parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d"/>'%(gx,wy0,gx,wy1)); gx+=25
        gy=int(np.floor(wy0/25))*25
        while gy<=wy1:
            parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d"/>'%(wx0,gy,wx1,gy)); gy+=25
        parts.append('</g>')
        parts.append('<path d="%s" fill="#141414" fill-rule="nonzero"/>'%d)
        parts.append('</g>')
        parts.append('<text x="%d" y="15" font-size="13" fill="#c00" font-family="sans-serif">%s</text>'%(ox+5,lbl))
    parts.append('</svg>')
    sp='/tmp/crop.svg'; open(sp,'w').write('\n'.join(parts))
    out='/tmp/crop.png'
    subprocess.run(['rsvg-convert','-w',str(W),'-h',str(H),'-o',out,sp],check=True)
    print('-> %s  %dx%d'%(out,W,H))

main()
