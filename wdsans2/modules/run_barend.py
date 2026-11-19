#!/usr/bin/env python3
"""三档应用 m_barend - 单次加载单次保存"""
import sys, os, json
sys.path.insert(0,"/workspace/wdsans2/probe")
sys.path.insert(0,"/workspace/wdsans2/modules")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
import m_barend
from canonpen3 import make_charstring

SRC=os.environ.get("WDS_SRC","/workspace/wdsans2/build/masters_R47")
OUT=os.environ.get("WDS_OUT","/workspace/wdsans2/build/masters_R48")
MASTERS=[("master-ExtraLight-250.otf",250),("master-Regular-400.otf",400),("master-Heavy-900.otf",900)]

IDX=json.load(open("/workspace/wdsans2/build/barend_idx.json"))
print("索引 %d 字" % len(IDX), flush=True)

def to_C(rp):
    C=[]; cur=None
    for op,a in rp.value:
        if op=="moveTo": cur={"start":tuple(a[0]),"segs":[]}; C.append(cur)
        elif op=="lineTo": cur["segs"].append(("L",tuple(a[0])))
        elif op=="curveTo": cur["segs"].append(("C",tuple(a[0]),tuple(a[1]),tuple(a[2])))
        elif op=="qCurveTo": cur["segs"].append(("Q",tuple(a[0]),tuple(a[1])))
        elif op in ("closePath","endPath"): cur=None
    return C

os.makedirs(OUT, exist_ok=True)
for fn,w in MASTERS:
    dst=os.path.join(OUT,fn)
    if os.path.exists(dst):
        print("[%d] 已存在" % w, flush=True); continue
    print("[%d] %s" % (w,fn), flush=True)
    f=TTFont(os.path.join(SRC,fn))
    csT=f["CFF2"].cff.topDictIndex[0].CharStrings
    gs=f.getGlyphSet()
    n=0
    for gn,recs in IDX.items():
        if gn not in csT.keys(): continue
        rp=RecordingPen()
        try: gs[gn].draw(rp)
        except Exception: continue
        C=to_C(rp)
        need=max(r[0] for r in recs)
        if need>=len(C): continue
        ok=True
        for r in recs:
            if r[1]>=1+len(C[r[0]]["segs"]): ok=False; break
        if not ok: continue
        NEW=m_barend.apply(C,[(r[0],r[1],r[2],r[3]) for r in recs])
        old=csT[gn]
        csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
        n+=1
    print("  改 %d" % n, flush=True)
    f["post"].formatType=3.0; f["post"].glyphOrder=None
    f.save(dst)
    f.close()
    print("  已保存", flush=True)
print("完成")
