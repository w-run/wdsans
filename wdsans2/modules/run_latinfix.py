#!/usr/bin/env python3
"""run_latinfix - 用 Mona 替换 i/j 和带音标拉丁（三档）

档位映射:
  我们的 250 -> Mona 200 (更细，解决 lat/cjk 失衡)
  我们的 400 -> Mona 400
  我们的 900 -> Mona 900
"""
import sys, os
sys.path.insert(0,"/workspace/wdsans2/probe")
sys.path.insert(0,"/workspace/wdsans2/modules")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
import numpy as np
import m_latinfix as M
from canonpen3 import make_charstring

SRC=os.environ.get("WDS_SRC","/workspace/wdsans2/build/masters_R56")
OUT=os.environ.get("WDS_OUT","/workspace/wdsans2/build/masters_R57")

# 我们的档 -> Mona 档
WEIGHT_MAP=[("master-ExtraLight-250.otf",250,200),
            ("master-Regular-400.otf",400,400),
            ("master-Heavy-900.otf",900,850)]

# 要替换的码位范围
RANGES=[(0x0020,0x007F),(0x00A0,0x024F),(0x1E00,0x1EFF)]
SPECIAL=[ord("i"),ord("j")]

os.makedirs(OUT, exist_ok=True)
for fn,w,mw in WEIGHT_MAP:
    dst=os.path.join(OUT,fn)
    if os.path.exists(dst):
        print("[%d] exists" % w, flush=True); continue
    print("[%d] %s  (Mona %d)" % (w,fn,mw), flush=True)
    mp=M.instantiate_mona(mw)
    fm=TTFont(mp,lazy=True)
    cmm=fm.getBestCmap(); gsm=fm.getGlyphSet()
    f=TTFont(os.path.join(SRC,fn))
    csT=f["CFF2"].cff.topDictIndex[0].CharStrings
    cm=f.getBestCmap()
    n=0; skip=0
    cps=list(SPECIAL)
    for lo,hi in RANGES:
        for c in range(lo,hi+1):
            if c not in cps: cps.append(c)
    for cp in cps:
        gnm=cmm.get(cp); gno=cm.get(cp)
        if not gnm or not gno:
            continue
        if gno not in csT.keys():
            continue
        pen=DecomposingRecordingPen(gsm)
        try: gsm[gnm].draw(pen)
        except Exception:
            skip+=1; continue
        C=M.rp_to_C(pen.value)
        if not C:
            skip+=1; continue
        old=csT[gno]
        try:
            csT[gno]=make_charstring(C, old.private, old.globalSubrs)
        except Exception:
            skip+=1; continue
        n+=1
    fm.close()
    print("  替换 %d 跳过 %d" % (n,skip), flush=True)
    f["post"].formatType=3.0; f["post"].glyphOrder=None
    f.save(dst)
    f.close()
    print("  saved", flush=True)
print("done")
