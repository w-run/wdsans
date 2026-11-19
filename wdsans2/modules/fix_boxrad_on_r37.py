#!/usr/bin/env python3
"""在 R37 上修正 m_boxrad 的内横漂移

R37 = R32 + m_boxrad(错误) + 后续小改动
问题: m_boxrad 把外框拉高 80，但内横绝对位置没变
      -> 内横相对位置从 0.507 漂到 0.561 -> 下格变大

修正: 在 R37 上把内横重新放到正确的相对位置。
      正确相对位置 = R32 的值（R32 与 SHS 一致）。
      由于 R37 的外框已经是拉长后的，我们需要知道 R32 的原始相对位置。

方法:
  1. 从 R32 检测: (glyph, bar_id, 原始相对位置 rel)
  2. 在 R37 上: 外框已经拉长，把内横移到 new_y0 + rel * target_h
  3. 外框不动（R37 的外框已经是目标状态）
"""
import sys, os, json
sys.path.insert(0,"/workspace/wdsans2/probe")
sys.path.insert(0,"/workspace/wdsans2/modules")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
import m_boxrad as _base
import m_boxrad2
from canonpen3 import make_charstring

R32="/workspace/wdsans2/build/masters_R32"
R37="/workspace/wdsans2/build/masters_R37"
OUT=os.environ.get("WDS_OUT","/workspace/wdsans2/build/masters_R47")
MASTERS=[("master-ExtraLight-250.otf",250),("master-Regular-400.otf",400),("master-Heavy-900.otf",900)]

def to_C(rp):
    C=[]; cur=None
    for op,a in rp.value:
        if op=="moveTo":
            cur={"start":tuple(a[0]),"segs":[]}; C.append(cur)
        elif op=="lineTo" and cur is not None:
            cur["segs"].append(("L",tuple(a[0])))
        elif op=="curveTo" and cur is not None:
            cur["segs"].append(("C",tuple(a[0]),tuple(a[1]),tuple(a[2])))
        elif op=="qCurveTo" and cur is not None:
            pts=[p for p in a if p is not None]
            if len(pts)>=2:
                cur["segs"].append(("Q",tuple(pts[-2]),tuple(pts[-1])))
            elif pts:
                cur["segs"].append(("L",tuple(pts[-1])))
        elif op in ("closePath","endPath"):
            cur=None
    # 过滤掉点不足的轮廓
    out=[]
    for c in C:
        if c["segs"]: out.append(c)
    return out

# 1) 从 R32 提取「正确相对位置」
print("=== 从 R32 提取内横相对位置 ===", flush=True)
f=TTFont(os.path.join(R32,MASTERS[1][0]), lazy=True)
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
    if not hits: continue
    rec=[]
    for left,right,ly0,ly1,ry0,ry1 in hits:
        lh=ly1-ly0
        if lh<=0: continue
        boxes=[]
        for i in left:
            x0,x1,y0,y1=m_boxrad2.bbox_of(C[i])
            boxes.append((i,x0,x1,y0,y1,y1-y0,x1-x0))
        outer=max(boxes,key=lambda t:t[5]*t[6])
        ow=outer[6]
        bars=[(i,y0,y1) for i,x0,x1,y0,y1,h,w in boxes
              if i!=outer[0] and h<130 and w>ow*0.45]
        rec.append({"left":[int(x) for x in left],
                    "bars":[[int(b[0]),round((b[1]+b[2])/2.0,1)] for b in bars],
                    "ly0":ly0,"ly1":ly1})
    if rec: IDX[gn]=rec
f.close()
print("命中 %d 字" % len(IDX), flush=True)
json.dump(IDX, open("/workspace/wdsans2/build/rel_idx.json","w"), ensure_ascii=False)

# 2) 在 R37 上修正
print()
print("=== 在 R37 上修正 ===", flush=True)
os.makedirs(OUT, exist_ok=True)
for fn,w in MASTERS:
    print("[%d]" % w, flush=True)
    f32=TTFont(os.path.join(R32,fn), lazy=True)
    gs32=f32.getGlyphSet()
    f=TTFont(os.path.join(R37,fn))
    cm=f.getBestCmap(); gs=f.getGlyphSet()
    csT=f["CFF2"].cff.topDictIndex[0].CharStrings
    n=0; skip=0
    for gn,recs in IDX.items():
        if gn not in csT.keys(): skip+=1; continue
        if gn not in cm.values(): skip+=1; continue
        rp=RecordingPen()
        try: gs[gn].draw(rp)
        except Exception: skip+=1; continue
        C=to_C(rp)
        if len(C)<3: skip+=1; continue
        # R37 的外框 y 范围（C 是 dict 列表，用 bbox_of 取边界）
        boxes37=[m_boxrad2.bbox_of(c) for c in C]
        allx=[b[0] for b in boxes37]+[b[1] for b in boxes37]
        xlim=min(allx)+(max(allx)-min(allx))*0.45
        parts=[b for b in boxes37 if b[1]<xlim]
        if not parts: skip+=1; continue
        ny0=min(b[2] for b in parts); ny1=max(b[3] for b in parts)
        nh=ny1-ny0
        if nh<=0: skip+=1; continue
        ok=True; changes=[]
        for rec in recs:
            lh=rec["ly1"]-rec["ly0"]
            if lh<=0: ok=False; break
            for bi,bc32 in rec["bars"]:
                if bi>=len(C): ok=False; break
                rel=(bc32-rec["ly0"])/lh
                x0,x1,by0,by1=m_boxrad2.bbox_of(C[bi])
                cur_c=(by0+by1)/2.0
                new_c=ny0+rel*nh
                changes.append((bi,new_c-cur_c))
        if not ok: skip+=1; continue
        if not changes: skip+=1; continue
        # 应用
        NEW=[]
        for i,c in enumerate(C):
            sh2=0.0
            for bi,d in changes:
                if bi==i: sh2=d; break
            if abs(sh2)<0.5:
                NEW.append(c); continue
            def ty(v,s=sh2): return v+s
            NEW.append(m_boxrad2._map_c(c,ty))
        old=csT[gn]
        csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
        n+=1
    f["post"].formatType=3.0
    f["post"].glyphOrder=None
    f.save(os.path.join(OUT,fn))
    f.close(); f32.close()
    print("  修正 %d 跳过 %d" % (n,skip), flush=True)
print("完成")
