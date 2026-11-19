#!/usr/bin/env python3
"""m_vertcorner3 三档应用"""
import sys, os, json
sys.path.insert(0,"/workspace/wdsans2/probe")
sys.path.insert(0,"/workspace/wdsans2/modules")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
import m_vertcorner3
from canonpen3 import make_charstring

SRC=os.environ.get("WDS_SRC","/workspace/wdsans2/build/masters_R47")
OUT=os.environ.get("WDS_OUT","/workspace/wdsans2/build/masters_R52")
M=[("master-ExtraLight-250.otf",250),("master-Regular-400.otf",400),("master-Heavy-900.otf",900)]

def to_C(rp):
    C=[]; cur=None
    for op,a in rp.value:
        if op=="moveTo": cur={"start":tuple(a[0]),"segs":[]}; C.append(cur)
        elif op=="lineTo": cur["segs"].append(("L",tuple(a[0])))
        elif op=="curveTo": cur["segs"].append(("C",tuple(a[0]),tuple(a[1]),tuple(a[2])))
        elif op=="qCurveTo": cur["segs"].append(("Q",tuple(a[0]),tuple(a[1])))
        elif op in ("closePath","endPath"): cur=None
    return C

IDXP="/workspace/wdsans2/build/vc3_idx.json"
if os.path.exists(IDXP):
    IDX=json.load(open(IDXP))
    print("reuse idx %d" % len(IDX), flush=True)
else:
    print("=== detect on 400 ===", flush=True)
    f=TTFont(os.path.join(SRC,M[1][0]), lazy=True)
    cm=f.getBestCmap(); gs=f.getGlyphSet()
    IDX={}
    for cp,gn in cm.items():
        if not (0x4E00<=cp<=0x9FFF): continue
        rp=RecordingPen()
        try: gs[gn].draw(rp)
        except Exception: continue
        C=to_C(rp)
        if len(C)<2: continue
        r=m_vertcorner3.find(C)
        if r: IDX[gn]=[[int(x[0]),float(x[1]),float(x[2])] for x in r]
    f.close()
    print("hits %d" % len(IDX), flush=True)
    json.dump(IDX, open(IDXP,"w"), ensure_ascii=False)

os.makedirs(OUT, exist_ok=True)
for fn,w in M:
    dst=os.path.join(OUT,fn)
    if os.path.exists(dst):
        print("[%d] exists" % w, flush=True); continue
    print("[%d] %s" % (w,fn), flush=True)
    f=TTFont(os.path.join(SRC,fn))
    csT=f["CFF2"].cff.topDictIndex[0].CharStrings
    gs=f.getGlyphSet()
    n=0; skip=0
    for gn,recs in IDX.items():
        if gn not in csT.keys(): continue
        rp=RecordingPen()
        try: gs[gn].draw(rp)
        except Exception: continue
        C=to_C(rp)
        ok=True
        for pid,bx1,by1 in recs:
            pid=int(pid)
            if pid>=len(C): ok=False; break
            if len(C[pid]["segs"])<3: ok=False; break
            if C[pid]["segs"][0][0]!="L": ok=False; break
        if not ok: skip+=1; continue

        # find bar contour in THIS master to get local bar y range
        hits=[]
        for pid,bx1,_by1 in recs:
            pid=int(pid)
            # locate the bar (rect contour) whose right edge == bx1
            local_top=None
            for bi,bc in enumerate(C):
                if not m_vertcorner3.is_rect_bar(bc):
                    continue
                bb=m_vertcorner3.bbox_of(bc)
                if abs(bb[1]-bx1)<2 and abs(bb[0]-C[pid]["start"][0])<200:
                    local_top=bb[3]
                    break
            if local_top is None:
                # fallback: search all rect bars for matching right edge
                for bi,bc in enumerate(C):
                    if not m_vertcorner3.is_rect_bar(bc):
                        continue
                    bb=m_vertcorner3.bbox_of(bc)
                    if abs(bb[1]-bx1)<2:
                        local_top=bb[3]
                        break
            if local_top is None:
                continue
            hits.append((pid,float(bx1),float(local_top)))
        if not hits:
            skip+=1; continue
        NEW=m_vertcorner3.apply(C,hits)
        # check segment count unchanged
        bad=False
        for pid,bx1,by1 in hits:
            if len(NEW[pid]["segs"])!=len(C[pid]["segs"]): bad=True; break
        if bad: skip+=1; continue
        old=csT[gn]
        csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
        n+=1
    print("  changed %d skipped %d" % (n,skip), flush=True)
    f["post"].formatType=3.0; f["post"].glyphOrder=None
    f.save(dst)
    f.close()
    print("  saved", flush=True)
print("done")
