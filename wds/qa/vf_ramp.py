"""VF 全字重验证（修正版）。

前一版 bug：instantiateVariableFont(inplace=True) 会**修改传入的 font 对象**，
所以复用同一个对象会导致 SRC 读数被污染（读到的是 NEW 的值）。
修法：每次重新 TTFont(path)。
"""
import sys
sys.path.insert(0,"/workspace/wdsans")
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen
import statistics

SRC="/workspace/wdsans/ref/NotoSansCJKsc-VF.ttf"
NEW="/data/build-cache/wdsans-p1/wdsans-p2-feet.ttf"

def measure(path, w):
    f=TTFont(path)                       # 每次新开
    i=instancer.instantiateVariableFont(f,{"wght":w},inplace=True,updateFontNames=False,optimize=False)
    gs=i.getGlyphSet(); cm=i.getBestCmap()
    def bb(ch):
        n=cm.get(ord(ch))
        if not n: return None
        bp=BoundsPen(gs); gs[n].draw(bp); return bp.bounds
    h=bb("一"); v=bb("丨")
    hth=(h[3]-h[1]) if h else 0
    vw=(v[2]-v[0]) if v else 0
    ds=[]
    for ch in "永国口明湖烟电直骨":
        n=cm.get(ord(ch))
        if not n: continue
        a=AreaPen(gs); gs[n].draw(a)
        b=BoundsPen(gs); gs[n].draw(b)
        if not b.bounds: continue
        x0,y0,x1,y1=b.bounds; ar=(x1-x0)*(y1-y0)
        if ar>0: ds.append(abs(a.value)/ar)
    i.close(); f.close()
    return hth, vw, (statistics.median(ds) if ds else 0)

weights=[250,300,350,400,500,600,700,800,900]
print(f"{'wght':>5} | {'Noto 横/竖/密度':>20} | {'本产物 横/竖/密度':>20} | {'竖/横':>6} | {'横减细':>7} {'竖减细':>7}")
print("-"*88)
prev_h=None; prev_v=None; ok=True
for w in weights:
    ah,av,ad = measure(SRC,w)
    bh,bv,bd = measure(NEW,w)
    ratio = bv/bh if bh else 0
    dh=ah-bh; dv=av-bv
    flag=""
    if prev_h is not None and bh<=prev_h: flag+=" 横非单调!"; ok=False
    if prev_v is not None and bv<=prev_v: flag+=" 竖非单调!"; ok=False
    prev_h,prev_v=bh,bv
    print(f"{w:5d} | {ah:6.1f}/{av:6.1f}/{ad:.3f} | {bh:6.1f}/{bv:6.1f}/{bd:.3f} | {ratio:6.3f} | {dh:7.1f} {dv:7.1f}{flag}")
print()
print("单调性:", "PASS" if ok else "FAIL")