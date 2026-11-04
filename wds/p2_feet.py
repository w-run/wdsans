import sys, os, time, statistics
sys.path.insert(0,"/workspace/wdsans")
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen
from wds.base import SRC, rebase_axis
from wds import thinning as T, feet

OUT="/data/build-cache/wdsans-p1"

def measure(f):
    gs=f.getGlyphSet(); cm=f.getBestCmap()
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
    return hth, vw, (statistics.median(ds) if ds else 0)

def inst(p):
    return instancer.instantiateVariableFont(TTFont(p),{"wght":400},inplace=True,updateFontNames=False,optimize=False)

f=TTFont(SRC); f=rebase_axis(f)
print("[1] 方向性减细 横6.0/侧 竖3.5/侧", flush=True)
t0=time.time(); T.thin_edges(f, 6.0, 3.5)
print(f"    {time.time()-t0:.0f}s", flush=True)

print("[2] 去出脚", flush=True)
t0=time.time()
ng,nb,det=feet.remove_feet(f, only_cjk=True)
print(f"    {ng} 字 {nb} 条 {time.time()-t0:.0f}s", flush=True)
print(f"    样例: {det[:12]}", flush=True)

out=f"{OUT}/wdsans-p2-feet.ttf"
t0=time.time(); f.save(out)
print(f"[3] 保存 {time.time()-t0:.0f}s", flush=True)

h1,v1,d1 = measure(inst(out))
print()
print(f"  本产物: 横{h1:.1f} 竖{v1:.1f} 竖/横{v1/h1:.3f} 密度{d1:.3f}")
oh,ov,od = measure(TTFont("/workspace/wdsans/ref/ops/ops-400.ttf"))
print(f"  OPPO  : 横{oh:.1f} 竖{ov:.1f} 竖/横{ov/oh:.3f} 密度{od:.3f}")