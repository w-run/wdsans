#!/usr/bin/env python3
"""m_build_ttf_vf - 构建可变 TTF（从三档静态 OTF master）

流程:
  1. 三档 master CFF2 -> TTF（cu2qu 转二次）
  2. 用 varLib 合成可变 TTF
  3. 注入 chws/vchw（从现有部署版 GPOS 复制）
"""
import sys, os, time, shutil
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.varLib import build

sys.path.insert(0, "/workspace/wdsans2/modules")
import m_cff2ttf

SRC="masters_R42"
BASE="/workspace/wdsans2/build"
TTFDIR=os.path.join(BASE,"ttf_masters")
OUT_TTF=os.path.join(BASE,"WDesignSansVF.ttf")
CHWS_SRC="/workspace/static/wdsans/WDesignSans-VF.otf"

os.makedirs(TTFDIR, exist_ok=True)

MASTERS=[("master-ExtraLight-250.otf","master-ExtraLight-250.ttf",250),
         ("master-Regular-400.otf","master-Regular-400.ttf",400),
         ("master-Heavy-900.otf","master-Heavy-900.ttf",900)]

print("=== 1. OTF -> TTF (三档) ===")
for otf, ttf, w in MASTERS:
    src=os.path.join(BASE,SRC,otf)
    dst=os.path.join(TTFDIR,ttf)
    if os.path.exists(dst):
        print("  %d 档已存在，跳过" % w); continue
    print("  [%d]" % w)
    m_cff2ttf.convert(src, dst, max_err=1.0, verbose=True)

print()
print("=== 2. 建 TTF designspace ===")
ds=DesignSpaceDocument()
from fontTools.designspaceLib import SourceDescriptor, AxisDescriptor
for otf, ttf, w in MASTERS:
    s=SourceDescriptor()
    s.path=os.path.join(TTFDIR,ttf)
    s.name="wght%d" % w
    s.location={"wght": float(w)}
    s.designLocation={"wght": float(w)}
    if w==400:
        s.copyInfo=True
        s.copyLib=True
        s.copyGroups=True
        s.copyFeatures=True
    ds.addSource(s)
ds.default=400
ax=AxisDescriptor()
ax.tag="wght"; ax.name="Weight"; ax.minimum=250; ax.maximum=900; ax.default=400
ds.addAxis(ax)
DS_PATH=os.path.join(BASE,"ttf.designspace")
ds.write(DS_PATH)
print("  ->", DS_PATH)

print()
print("=== 3. varLib 合成可变 TTF ===")
t0=time.time()
vf, _, _ = build(DS_PATH)
vf["post"].formatType=3.0
vf["post"].glyphOrder=None
vf.save(OUT_TTF)
vf.close()
print("  完成 %.0fs -> %s (%.1fMB)" % (time.time()-t0, OUT_TTF, os.path.getsize(OUT_TTF)/1e6))

print()
print("=== 4. 注入 chws/vchw ===")
a=TTFont(OUT_TTF)
b=TTFont(CHWS_SRC)
ta=sorted(set(fr.FeatureTag for fr in a["GPOS"].table.FeatureList.FeatureRecord))
tb=sorted(set(fr.FeatureTag for fr in b["GPOS"].table.FeatureList.FeatureRecord))
print("  当前 GPOS(%d): %s" % (len(ta),ta))
print("  参考 GPOS(%d): %s" % (len(tb),tb))
if "chws" not in ta:
    a["GPOS"]=b["GPOS"]
    a["GDEF"]=b["GDEF"]
    a["post"].formatType=3.0
    a["post"].glyphOrder=None
    a.save(OUT_TTF)
    print("  已注入 GPOS+GDEF，重存")
a.close(); b.close()

print()
print("=== 5. 验证 ===")
g=TTFont(OUT_TTF, lazy=True)
print("  表:", sorted(g.keys()))
print("  glyphs %d  cmap %d" % (g["maxp"].numGlyphs, len(g.getBestCmap())))
print("  fvar:", [(a.axisTag,a.minValue,a.defaultValue,a.maxValue) for a in g["fvar"].axes] if "fvar" in g else "无")
t=sorted(set(fr.FeatureTag for fr in g["GPOS"].table.FeatureList.FeatureRecord))
print("  GPOS(%d) chws=%s vchw=%s" % (len(t),"chws" in t,"vchw" in t))
g.close()
