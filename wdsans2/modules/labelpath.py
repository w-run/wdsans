#!/usr/bin/env python3
"""labelpath.py - 显示轮廓路径(线条) + 锚点编号"""
import sys, numpy as np, subprocess
sys.path.insert(0,'/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
def endp(s):
    if s[0]=='QM': return np.array(s[1][-1],float)
    return np.array(s[-1],float)

fp=sys.argv[1]; ch=sys.argv[2]; ci=int(sys.argv[3]); out=sys.argv[4]
win=None
for a in sys.argv[5:]:
    if a.startswith('win='): win=[float(x) for x in a[4:].split(',')]

f=TTFont(fp); cm=f.getBestCmap(); gs=f.getGlyphSet()
rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp)
C=contours_from_pen(rp.value); f.close()
c=C[ci]; segs=c['segs']
pts=[np.array(c['start'],float)]+[endp(s) for s in segs]

if win is None:
    P=np.vstack(pts); pad=60
    win=[P[:,0].min()-pad,P[:,0].max()+pad,P[:,1].min()-pad,P[:,1].max()+pad]
x0,x1,y0,y1=win
W=1500; H=int(W*(y1-y0)/(x1-x0)); k=W/(x1-x0)
def SX(x): return (x-x0)*k
def SY(y): return (y1-y)*k

parts=['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'%(W,H,W,H)]
parts.append('<rect width="%d" height="%d" fill="#ffffff"/>'%(W,H))
# 网格
parts.append('<g stroke="#eee" stroke-width="1">')
gx=int(np.floor(x0/25))*25
while gx<=x1:
    parts.append('<line x1="%.1f" y1="0" x2="%.1f" y2="%d"/>'%(SX(gx),SX(gx),H)); gx+=25
gy=int(np.floor(y0/25))*25
while gy<=y1:
    parts.append('<line x1="0" y1="%.1f" x2="%d" y2="%.1f"/>'%(SY(gy),W,SY(gy))); gy+=25
parts.append('</g>')
# 字形淡色填充
d=[]
d.append('M %.2f %.2f'%(pts[0][0],pts[0][1]))
for s in segs:
    if s[0]=='L': d.append('L %.2f %.2f'%(s[1][0],s[1][1]))
    elif s[0]=='C': d.append('C %.2f %.2f %.2f %.2f %.2f %.2f'%(s[1][0],s[1][1],s[2][0],s[2][1],s[3][0],s[3][1]))
d.append('Z')
parts.append('<g transform="translate(0,%f) scale(%f,%f) translate(%f,0)">'%(y1*k,k,-k,-x0))
parts.append('<path d="%s" fill="#e8e8e8" fill-rule="nonzero"/>'%' '.join(d))
parts.append('</g>')
# 轮廓路径(粗线)
parts.append('<g stroke="#0a58ca" stroke-width="3" fill="none" stroke-linejoin="round">')
for kk,s in enumerate(segs):
    a=pts[kk]; b=pts[kk+1]
    if s[0]=='L':
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'%(SX(a[0]),SY(a[1]),SX(b[0]),SY(b[1])))
    elif s[0]=='C':
        parts.append('<path d="M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f"/>'%(
            SX(a[0]),SY(a[1]),SX(s[1][0]),SY(s[1][1]),SX(s[2][0]),SY(s[2][1]),SX(b[0]),SY(b[1])))
parts.append('</g>')
# 段号标注(线段中点)
for kk,s in enumerate(segs):
    a=pts[kk]; b=pts[kk+1]; mid=(a+b)/2
    parts.append('<text x="%.1f" y="%.1f" font-size="17" fill="#0a8f3c" font-family="monospace">s%d</text>'%(SX(mid[0])+5,SY(mid[1])-5,kk))
# 锚点
for i,p in enumerate(pts):
    col='#d00' if i==0 else '#0a58ca'
    parts.append('<circle cx="%.1f" cy="%.1f" r="8" fill="%s" stroke="#fff" stroke-width="2"/>'%(SX(p[0]),SY(p[1]),col))
    parts.append('<text x="%.1f" y="%.1f" font-size="34" font-weight="bold" fill="%s" stroke="#fff" stroke-width="6" paint-order="stroke" font-family="sans-serif">%d</text>'%(SX(p[0])+12,SY(p[1])-12,col,i+1))
parts.append('</svg>')
sp=out.replace('.png','.svg'); open(sp,'w').write('\n'.join(parts))
subprocess.run(['rsvg-convert','-w',str(W),'-h',str(H),'-o',out,sp],check=True)
print('-> %s'%out)
print()
for i,p in enumerate(pts):
    print('  锚点%2d (%6.1f,%6.1f)'%(i+1,p[0],p[1]))
print()
for kk,s in enumerate(segs):
    a=pts[kk]; b=pts[kk+1]
    L=float(np.linalg.norm(b-a))
    print('  seg%d %s 锚点%d->锚点%d  L=%5.1f'%(kk,s[0],kk+1,kk+2,L))
