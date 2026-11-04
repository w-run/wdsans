import sys, os, time
sys.path.insert(0, "/workspace/wdsans")
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen
import statistics
from wds.base import SRC, rebase_axis
from wds import geometry as G

OUT = "/data/build-cache/wdsans-p1"
CHAR = "永国口明湖烟电直骨"

def dens(path, w=400):
    f = TTFont(path)
    if "fvar" in f:
        f = instancer.instantiateVariableFont(f, {"wght": w}, inplace=True, updateFontNames=False, optimize=False)
    gs = f.getGlyphSet(); cmap = f.getBestCmap(); out = []
    for ch in CHAR:
        n = cmap.get(ord(ch))
        if not n: continue
        ap = AreaPen(gs); gs[n].draw(ap)
        bp = BoundsPen(gs); gs[n].draw(bp)
        if not bp.bounds: continue
        x0,y0,x1,y1 = bp.bounds
        b = (x1-x0)*(y1-y0)
        if b > 0: out.append((abs(ap.value)/b, x1-x0, y1-y0))
    f.close()
    if not out: return (0,0,0)
    return (statistics.median(x[0] for x in out),
            statistics.median(x[1] for x in out),
            statistics.median(x[2] for x in out))

os.makedirs(OUT, exist_ok=True)
print("[1] 载入 + 重设轴", flush=True)
f = TTFont(SRC)
f = rebase_axis(f)
before = dens(SRC)
print(f"    Noto 基线: 密度{before[0]:.3f} 宽{before[1]:.0f} 高{before[2]:.0f}", flush=True)

print("[2] 改写 glyf base 轮廓（真正改变默认实例）", flush=True)
t0 = time.time()
sx = 0.985
n = G.face_scale_base(f, sx)
print(f"    缩放 {n} 个字形 x{sx}, {time.time()-t0:.1f}s", flush=True)

out = f"{OUT}/wdsans-p1.ttf"
t0 = time.time()
f.save(out)
print(f"[3] 保存 {time.time()-t0:.1f}s  {os.path.getsize(out)/1024/1024:.1f} MB", flush=True)

after = dens(out)
print()
print("400 字重对比:")
print(f"  Noto 基线   密度{after[0]:.3f} 宽{before[1]:.0f} 高{before[2]:.0f}" if False else f"  Noto 基线   密度{before[0]:.3f} 宽{before[1]:.0f} 高{before[2]:.0f}")
print(f"  本产物      密度{after[0]:.3f} 宽{after[1]:.0f} 高{after[2]:.0f}")
print(f"  OPPO        密度{dens('/workspace/wdsans/ref/ops/ops-400.ttf')[0]:.3f}")