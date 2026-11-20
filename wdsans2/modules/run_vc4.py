#!/usr/bin/env python3
"""run_vc4 - m_vertcorner3(扩展版) 三档应用"""
import sys, os
sys.path.insert(0,"/workspace/wdsans2/probe")
sys.path.insert(0,"/workspace/wdsans2/modules")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
import m_vertcorner3 as M
from canonpen3 import make_charstring

SRC=os.environ.get("WDS_SRC","/workspace/wdsans2/build/masters_R47")
OUT=os.environ.get("WDS_OUT","/workspace/wdsans2/build/masters_R55")
MS=[("master-ExtraLight-250.otf",250),("master-Regular-400.otf",400),("master-Heavy-900.otf",900)]

def to_C(rp):
    C=[]; cur=None
    for op,a in rp.value:
        if op=="moveTo": cur={"start":tuple(a[0]),"segs":[]}; C.append(cur)
        elif op=="lineTo": cur["segs"].append(("L",tuple(a[0])))
        elif op=="curveTo": cur["segs"].append(("C",tuple(a[0]),tuple(a[1]),tuple(a[2])))
        elif op=="qCurveTo": cur["segs"].append(("Q",tuple(a[0]),tuple(a[1])))
        elif op in ("closePath","endPath"): cur=None
    return [c for c in C if c["segs"]]

os.makedirs(OUT, exist_ok=True)
for fn,w in MS:
    dst=os.path.join(OUT,fn)
    if os.path.exists(dst):
        print("[%d] exists" % w, flush=True); continue
    print("[%d] %s" % (w,fn), flush=True)
    f=TTFont(os.path.join(SRC,fn))
    csT=f["CFF2"].cff.topDictIndex[0].CharStrings
    gs=f.getGlyphSet()
    n=0
    for gn in list(csT.keys()):
        rp=RecordingPen()
        try: gs[gn].draw(rp)
        except Exception: continue
        C=to_C(rp)
        if len(C)<2: continue
        h=M.find(C)
        if not h: continue
        NEW=M.apply(C,h)
        old=csT[gn]
        try: csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
        except Exception: continue
        n+=1
    print("  changed %d" % n, flush=True)
    f["post"].formatType=3.0; f["post"].glyphOrder=None
    f.save(dst)
    f.close()
    print("  saved", flush=True)
print("done")
