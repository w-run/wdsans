#!/usr/bin/env python3
"""replay2 - 用当前 m_barple 在 T6 上重放，测撇厚
安全措施: 所有 WDS_* 环境变量指向临时目录，绝不碰 masters_*
"""
import os, sys, tempfile
TMP = tempfile.mkdtemp(prefix="replay2_")
os.environ["WDS_SRC"] = TMP
os.environ["WDS_OUT"] = TMP
os.environ["WDS_BASE"] = TMP

sys.path.insert(0, "/workspace/wdsans2/probe")
sys.path.insert(0, "/workspace/wdsans2/modules")

import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
import m_barple

SZ = 2000
UPEM = 1000

def thick(path, ch="多"):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    if not len(r): return 0.0
    a = a[r[0]:r[-1]+1, c[0]:c[-1]+1]
    T = ndimage.distance_transform_edt(a) * 2
    H, W = a.shape; k = UPEM / SZ
    vals = []
    for pct in (19, 22, 25, 28):
        y = int(H * pct / 100)
        xs = np.where(a[y])[0]
        if not len(xs): continue
        runs = []; st = xs[0]; pv = xs[0]
        for x in xs[1:]:
            if x - pv > 2:
                runs.append((st, pv)); st = x
            pv = x
        runs.append((st, pv))
        x0, x1 = runs[-1]
        vals.append(T[y, x0:x1+1].max() * k)
    return sum(vals) / len(vals) if vals else 0.0

def allpts(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: P.append(np.array(q, float))
        elif s[0] == "C":
            P.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1],float), np.array(s[2],float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)

SW = {250: 30.0, 400: 77.0, 900: 150.0}
FN = {250: "master-ExtraLight-250.otf", 400: "master-Regular-400.otf", 900: "master-Heavy-900.otf"}
T6D = "/workspace/wdsans2/build/masters_T6/"
R34D = "/workspace/wdsans2/build/masters_R34/"
OUT = "/workspace/wdsans2/build/replay2"
os.makedirs(OUT, exist_ok=True)

print("%-5s %-10s %-12s %-10s %-10s" % ("档", "T6(原)", "重放barple", "SHS", "R34(现)"))
for w in (250, 400, 900):
    src = T6D + FN[w]
    f = TTFont(src)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    gn = cm[ord("多")]
    rp = RecordingPen(); gs[gn].draw(rp)
    C = contours_from_pen(rp.value)
    hits = m_barple.find(C, SW[w])
    if not hits:
        print("%-5d 无命中" % w); f.close(); continue
    NEW = m_barple.apply(C, hits)
    cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
    old = csT[gn]
    csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType = 3.0; f["post"].glyphOrder = None
    p = os.path.join(OUT, "P_%d.otf" % w)
    f.save(p); f.close()
    # 终点坐标
    nb=None
    for ci,c2 in enumerate(NEW):
        sig="".join(s[0] for s in c2["segs"]); P=allpts(c2)
        if sig=="LCCC" and P[:,1].max()>600 and P[:,0].max()>600:
            nb=tuple(round(v) for v in c2["segs"][2][-1]); break
    print("%-5d %-10.0f %-12.0f %-10.0f %-10.0f  终点=%s" % (
        w, thick(src), thick(p),
        thick("/workspace/wdsans/ref/shs/shs-%d.otf" % w),
        thick(R34D + FN[w]), nb))
print()
print("对比: R34 当前 vs 重放结果，差值越小说明历史 MOD 参数不是主因")
