#!/usr/bin/env python3
"""labelpts.py - 在字形锚点上标注编号

用法: labelpts.py <字体> <字> [轮廓索引] [输出png] [win=x0,x1,y0,y1]
编号规则: 每个轮廓内 1=start, 2..N = 各段终点
start 用红色, 其余蓝色
"""
import sys, numpy as np, os, subprocess
sys.path.insert(0,'/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from canonpen3 import contours_from_pen

def endp(s):
    if s[0]=='QM': return np.array(s[1][-1],float)
    return np.array(s[-1],float)

def main():
    fp=sys.argv[1]; ch=sys.argv[2]
    ci=int(sys.argv[3]) if len(sys.argv)>3 else 9
    out=sys.argv[4] if len(sys.argv)>4 else '/tmp/pts.png'
    win=None
    for a in sys.argv[5:]:
        if a.startswith('win='):
            win=[float(x) for x in a[4:].split(',')]

    f=TTFont(fp); cm=f.getBestCmap(); gs=f.getGlyphSet(); gn=cm[ord(ch)]
    sp=SVGPathPen(gs); gs[gn].draw(sp); d=sp.getCommands()
    rp=RecordingPen(); gs[gn].draw(rp)
    C=contours_from_pen(rp.value); f.close()

    c=C[ci]; segs=c['segs']
    pts=[np.array(c['start'],float)]+[endp(s) for s in segs]

    if win is None:
        P=np.vstack(pts); pad=50
        win=[P[:,0].min()-pad,P[:,0].max()+pad,P[:,1].min()-pad,P[:,1].max()+pad]
    x0,x1,y0,y1=win
    W=1500; H=int(W*(y1-y0)/(x1-x0)); k=W/(x1-x0)

    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'%(W,H,W,H)]
    parts.append('<rect width="%d" height="%d" fill="#ffffff"/>'%(W,H))
    # 网格 25 单位
    parts.append('<g stroke="#e6e6e6" stroke-width="1">')
    gx=int(np.floor(x0/25))*25
    while gx<=x1:
        sx=(gx-x0)*k
        parts.append('<line x1="%.1f" y1="0" x2="%.1f" y2="%d"/>'%(sx,sx,H)); gx+=25
    gy=int(np.floor(y0/25))*25
    while gy<=y1:
        sy=(y1-gy)*k
        parts.append('<line x1="0" y1="%.1f" x2="%d" y2="%.1f"/>'%(sy,W,sy)); gy+=25
    parts.append('</g>')
    # 坐标标注
    parts.append('<g fill="#999" font-size="14" font-family="sans-serif">')
    gx=int(np.floor(x0/100))*100
    while gx<=x1:
        parts.append('<text x="%.1f" y="16">%d</text>'%((gx-x0)*k,gx)); gx+=100
    gy=int(np.floor(y0/100))*100
    while gy<=y1:
        parts.append('<text x="4" y="%.1f">%d</text>'%((y1-gy)*k,gy)); gy+=100
    parts.append('</g>')
    # 字形
    parts.append('<g transform="translate(0,%f) scale(%f,%f) translate(%f,0)">'%(y1*k,k,-k,-x0))
    parts.append('<path d="%s" fill="#1a1a1a" fill-rule="nonzero"/>'%d)
    parts.append('</g>')
    # 锚点 + 编号
    for i,p in enumerate(pts):
        sx=(p[0]-x0)*k; sy=(y1-p[1])*k
        col='#d00' if i==0 else '#0a58ca'
        parts.append('<circle cx="%.1f" cy="%.1f" r="7" fill="%s" stroke="#fff" stroke-width="2.5"/>'%(sx,sy,col))
        parts.append('<text x="%.1f" y="%.1f" font-size="30" font-weight="bold" fill="%s" '
                     'stroke="#fff" stroke-width="5" paint-order="stroke" font-family="sans-serif">%d</text>'
                     %(sx+11,sy-11,col,i+1))
    parts.append('</svg>')
    sp2=out.replace('.png','.svg')
    open(sp2,'w').write('\n'.join(parts))
    subprocess.run(['rsvg-convert','-w',str(W),'-h',str(H),'-o',out,sp2],check=True)
    print('-> %s (%dx%d)'%(out,W,H))
    print()
    print('轮廓 C%d  %s   共 %d 个锚点'%(ci,''.join(s[0] for s in segs),len(pts)))
    print('  编号   坐标            类型')
    for i,p in enumerate(pts):
        kind='start (闭合起点)' if i==0 else 'seg%d 终点'%(i-1)
        print('   %2d   (%6.1f,%6.1f)   %s'%(i+1,p[0],p[1],kind))

main()
