import sys, os, time, statistics
sys.path.insert(0,"/workspace/wdsans")
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen
from wds.base import SRC, rebase_axis
from wds import thinning as T

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

os.makedirs(OUT, exist_ok=True)
h0,v0,d0 = measure(inst(SRC))
print(f"[0] Noto 400: 横{h0:.1f} 竖{v0:.1f} 竖/横{v0/h0:.3f} 密度{d0:.3f}", flush=True)

f=TTFont(SRC); f=rebase_axis(f)

# 目标 竖/横 ≈ 1.06，总密度 ~0.37
# 横 82 -> 70 (d_h=6), 竖 81 -> 74 (d_v=3.5)
D_H, D_V = 6.0, 3.5
print(f"[1] 边级方向减细 横{D_H}/侧 竖{D_V}/侧", flush=True)
t0=time.time()
done,skip=T.thin_edges(f, D_H, D_V)
print(f"    {done} 字形 跳过{skip} {time.time()-t0:.0f}s", flush=True)

out=f"{OUT}/wdsans-p1-edge.ttf"
t0=time.time(); f.save(out)
print(f"[2] 保存 {time.time()-t0:.0f}s", flush=True)

h1,v1,d1 = measure(inst(out))
print()
print(f"  本产物: 横{h1:.1f} 竖{v1:.1f} 竖/横{v1/h1:.3f} 密度{d1:.3f}")
oh,ov,od = measure(TTFont("/workspace/wdsans/ref/ops/ops-400.ttf"))
print(f"  OPPO  : 横{oh:.1f} 竖{ov:.1f} 竖/横{ov/oh:.3f} 密度{od:.3f}")