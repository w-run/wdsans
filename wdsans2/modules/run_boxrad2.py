#!/usr/bin/env python3
"""三档应用 m_boxrad2（400档检测 + 三档同一索引）"""
import sys, os, json
sys.path.insert(0,"/workspace/wdsans2/probe")
sys.path.insert(0,"/workspace/wdsans2/modules")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
import m_boxrad2
import m_boxrad

SRC=os.environ.get("WDS_SRC","/workspace/wdsans2/build/masters_R37")
OUT=os.environ.get("WDS_OUT","/workspace/wdsans2/build/masters_R46")
MASTERS=[("master-ExtraLight-250.otf",250),
         ("master-Regular-400.otf",400),
         ("master-Heavy-900.otf",900)]

def to_C(rp):
    C=[]; cur=None
    for op,a in rp.value:
        if op=="moveTo": cur={"start":tuple(a[0]),"segs":[]}; C.append(cur)
        elif op=="lineTo": cur["segs"].append(("L",tuple(a[0])))
        elif op=="curveTo": cur["segs"].append(("C",tuple(a[0]),tuple(a[1]),tuple(a[2])))
        elif op=="qCurveTo": cur["segs"].append(("Q",tuple(a[0]),tuple(a[1])))
        elif op in ("closePath","endPath"): cur=None
    return C

# 1) 400档检测
print("=== 400档检测 ===", flush=True)
f=TTFont(os.path.join(SRC,MASTERS[1][0]), lazy=True)
cm=f.getBestCmap(); gs=f.getGlyphSet()
IDX={}
for cp,gn in cm.items():
    if not (0x4E00<=cp<=0x9FFF): continue
    rp=RecordingPen()
    try: gs[gn].draw(rp)
    except Exception: continue
    C=to_C(rp)
    if len(C)<3: continue
    hits=m_boxrad2.find(C)
    if hits:
        # 存完整 hits（left/right/y范围都用400档的值）
        IDX[gn]=[[list(h[0]), list(h[1]), h[2], h[3], h[4], h[5]] for h in hits]
f.close()
print("命中 %d 字" % len(IDX), flush=True)

json.dump(IDX, open("/workspace/wdsans2/build/boxrad2_idx.json","w"), ensure_ascii=False)

# 2) 三档应用
os.makedirs(OUT, exist_ok=True)
for fn,w in MASTERS:
    print("[%d] %s" % (w,fn), flush=True)
    f=TTFont(os.path.join(SRC,fn))
    cm=f.getBestCmap(); gs=f.getGlyphSet()
    csT=f["CFF2"].cff.topDictIndex[0].CharStrings
    n=0; skip=0
    for gn,lefts in IDX.items():
        if gn not in csT.keys(): skip+=1; continue
        rp=RecordingPen()
        try: gs[gn].draw(rp)
        except Exception: skip+=1; continue
        C=to_C(rp)
        # 直接使用 400 档的 hits（三档严格一致）
        hits=[(h[0], h[1], h[2], h[3], h[4], h[5]) for h in lefts]
        if not hits: skip+=1; continue
        # 校验轮廓数一致
        need=max(max(h[0]) if h[0] else 0 for h in hits)
        if need >= len(C):
            skip+=1; continue
        NEW=m_boxrad2.apply(C,hits)
        # 校验段数一致
        ok=True
        for i in range(len(C)):
            if len(C[i]["segs"])!=len(NEW[i]["segs"]) or len(C[i]["segs"])==0:
                ok=False; break
        if not ok: skip+=1; continue
        from canonpen3 import make_charstring
        old=csT[gn]
        csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
        n+=1
    f["post"].formatType=3.0
    f["post"].glyphOrder=None
    f.save(os.path.join(OUT,fn))
    f.close()
    print("  应用 %d 跳过 %d" % (n,skip), flush=True)
print("完成")
