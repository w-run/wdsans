import sys, os, time, statistics
sys.path.insert(0,"/workspace/wdsans")
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen
from wds.base import SRC, rebase_axis
from wds import geometry as G

OUT="/data/build-cache/wdsans-p1"
CHAR="永国口明湖烟电直骨"

def dens(path,w=400):
    f=TTFont(path)
    if "fvar" in f:
        f=instancer.instantiateVariableFont(f,{"wght":w},inplace=True,updateFontNames=False,optimize=False)
    gs=f.getGlyphSet(); cmap=f.getBestCmap(); ds=[]
    for ch in CHAR:
        n=cmap.get(ord(ch));
        if not n: continue
        ap=AreaPen(gs); gs[n].draw(ap)
        bp=BoundsPen(gs); gs[n].draw(bp)
        if not bp.bounds: continue
        x0,y0,x1,y1=bp.bounds; b=(x1-x0)*(y1-y0)
        if b>0: ds.append(abs(ap.value)/b)
    f.close()
    return statistics.median(ds) if ds else 0

os.makedirs(OUT,exist_ok=True)
print("[1] 载入+重设轴", flush=True)
f=TTFont(SRC); f=rebase_axis(f)
print(f"    Noto 密度 {dens(SRC):.3f}", flush=True)

for D in (5.0,):
    print(f"[2] 自校准减细 {D}", flush=True)
    t0=time.time()
    done,skip=G.thin_strokes_base(f, D)
    print(f"    {done} 字形 跳过{skip} {time.time()-t0:.0f}s", flush=True)
    out=f"{OUT}/wdsans-p1-thin{D:.0f}.ttf"
    t0=time.time(); f.save(out)
    print(f"[3] 保存 {time.time()-t0:.0f}s 密度={dens(out):.3f} -> {out}", flush=True)

print(f"参考: OPPO {dens('/workspace/wdsans/ref/ops/ops-400.ttf'):.3f}", flush=True)