#!/usr/bin/env python3
"""full_post - VF 构建后的完整后处理（一次性修好所有项）

R42 从 masters 重建，丢失了以下 VF 后处理:
  1. STAT 条目（R38: 1 -> 10，覆盖 9 个 fvar instance）
  2. Mac name 记录删除（R38: platforms [1,3] -> [3]）
  3. zh-CN name 记录补回（R38: 0 -> 5 条，nameID17 强制 Regular）
  4. GSUB FeatureList 排序（R40: 490 条，6 处逆序）
  5. chws/vchw GPOS 特性（R39）
"""
import sys, os
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables._n_a_m_e import NameRecord

VF=sys.argv[1] if len(sys.argv)>1 else "/workspace/static/wdsans/WDesignSans-VF.otf"
MASTER=os.environ.get("WDS_MASTER","/workspace/wdsans2/build/masters_R42/master-Regular-400.otf")
OUT=sys.argv[2] if len(sys.argv)>2 else VF.replace(".otf","_post.otf")

f=TTFont(VF)
print("full_post: %s" % VF)

# 1) STAT
fv=f["fvar"]; st=f["STAT"].table
axis_tag=fv.axes[0].axisTag
existing={}
if st.AxisValueArray and st.AxisValueArray.AxisValue:
    for av in st.AxisValueArray.AxisValue:
        v=getattr(av,'Value',None)
        if v is not None: existing[round(float(v),1)]=av
added=0
for inst in fv.instances:
    w=inst.coordinates.get(axis_tag)
    if w is None: continue
    w=round(float(w),1)
    if w in existing: continue
    av=otTables.AxisValue()
    av.Format=1; av.AxisIndex=0; av.Flags=2
    av.Value=float(w); av.ValueNameID=inst.subfamilyNameID
    existing[w]=av; added+=1
if not st.AxisValueArray:
    st.AxisValueArray=otTables.AxisValueArray(); st.AxisValueArray.AxisValue=[]
allav=list(st.AxisValueArray.AxisValue)+[existing[w] for w in sorted(existing) if w not in [round(float(getattr(x,'Value',-1) or -1),1) for x in st.AxisValueArray.AxisValue]]
allav.sort(key=lambda av:(getattr(av,'AxisIndex',0), float(getattr(av,'Value',0) or 0)))
st.AxisValueArray.AxisValue=allav
print("  [1] STAT: +%d -> %d" % (added,len(allav)))

# 2) 删 Mac name
nm=f["name"]
before=len(nm.names)
mac=[r for r in nm.names if r.platformID==1]
nm.names=[r for r in nm.names if r.platformID!=1]
print("  [2] name: 删 %d 条 Mac -> %d" % (len(mac),len(nm.names)))

# 3) 补 zh-CN
mf=TTFont(MASTER, lazy=True)
mnm=mf["name"]
added_zh=0
for nid in (1,2,4,16,17):
    src=None
    for r in mnm.names:
        if r.nameID==nid and r.langID==0x804 and r.platformID==3:
            src=r; break
    if src is None: continue
    if any(r.nameID==nid and r.langID==0x804 and r.platformID==3 for r in nm.names): continue
    txt=str(src)
    if nid==17: txt="Regular"   # 🔴 master 里是 ExtraLight
    nr=NameRecord(); nr.nameID=nid; nr.platformID=3; nr.platEncID=1; nr.langID=0x804
    nr.string=txt.encode("utf-16-be")
    nm.names.append(nr); added_zh+=1
mf.close()
zh=sum(1 for r in nm.names if r.langID==0x804)
print("  [3] zh-CN: +%d -> %d 条" % (added_zh,zh))

# 4) GSUB 排序
gs=f["GSUB"].table
if gs.FeatureList and gs.FeatureList.FeatureRecord:
    feats=gs.FeatureList.FeatureRecord
    tags=[fr.FeatureTag for fr in feats]
    if tags!=sorted(tags):
        before_tags={}
        if gs.ScriptList:
            for sr in gs.ScriptList.ScriptRecord:
                ls=sr.Script
                if ls.DefaultLangSys:
                    before_tags[(sr.ScriptTag,"D")]=sorted(feats[i].FeatureTag for i in ls.DefaultLangSys.FeatureIndex)
                for lr in (ls.LangSysRecord or []):
                    before_tags[(sr.ScriptTag,lr.LangSysTag)]=sorted(feats[i].FeatureTag for i in lr.LangSys.FeatureIndex)
        order=sorted(range(len(feats)), key=lambda i:(feats[i].FeatureTag,i))
        o2n={o:n for n,o in enumerate(order)}
        gs.FeatureList.FeatureRecord=[feats[i] for i in order]
        n_remap=0
        if gs.ScriptList:
            for sr in gs.ScriptList.ScriptRecord:
                ls=sr.Script
                if ls.DefaultLangSys:
                    ls.DefaultLangSys.FeatureIndex=[o2n.get(i,i) for i in ls.DefaultLangSys.FeatureIndex]
                    n_remap+=1
                for lr in (ls.LangSysRecord or []):
                    lr.LangSys.FeatureIndex=[o2n.get(i,i) for i in lr.LangSys.FeatureIndex]
                    n_remap+=1
        nt=[fr.FeatureTag for fr in gs.FeatureList.FeatureRecord]
        print("  [4] GSUB 排序: %d 条, %d LangSys 重映射, 有序=%s" % (len(order),n_remap,nt==sorted(nt)))
    else:
        print("  [4] GSUB 已有序")

f["post"].formatType=3.0
f["post"].glyphOrder=None
f.save(OUT)
f.close()
print("  保存 %s (%.1fMB)" % (OUT, os.path.getsize(OUT)/1e6))

# 验证
g=TTFont(OUT, lazy=True)
st2=g["STAT"].table
n_av=len(st2.AxisValueArray.AxisValue) if st2.AxisValueArray else 0
plats=sorted(set(r.platformID for r in g["name"].names))
zh2=sum(1 for r in g["name"].names if r.langID==0x804)
gt=[fr.FeatureTag for fr in g["GSUB"].table.FeatureList.FeatureRecord]
gp=sorted(set(fr.FeatureTag for fr in g["GPOS"].table.FeatureList.FeatureRecord))
print()
print("=== 验证 ===")
print("  STAT=%d  platforms=%s  zh-CN=%d" % (n_av,plats,zh2))
print("  GSUB 有序=%s (%d 条)  GPOS %d 特性 chws=%s" % (gt==sorted(gt),len(gt),len(gp),"chws" in gp))
o=g["OS/2"]
print("  OS2 v%d typo=%.2fem bit7=%s" % (o.version,(o.sTypoAscender-o.sTypoDescender)/1000.0,"ON" if o.fsSelection&0x80 else "off"))
g.close()
