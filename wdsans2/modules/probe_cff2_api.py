#!/usr/bin/env python3
"""probe_cff2_api - 找出向 CFF2 增加新 glyph 的正确方法"""
from fontTools.ttLib import TTFont
mf = TTFont("/workspace/wdsans2/build/masters_R35/master-Regular-400.otf", lazy=True)
cff = mf["CFF2"].cff
td = cff.topDictIndex[0]
cs = td.CharStrings

print("=== CharStrings 类型 ===")
print(type(cs))
print("含方法:", [m for m in dir(cs) if not m.startswith("_")][:20])

print()
print("=== charStrings 内部结构 ===")
inner = getattr(cs, "charStrings", None)
print(type(inner) if inner is not None else '无 charStrings 属性')
if isinstance(inner, dict):
    ks = list(inner.keys())[:3]
    print("前3个键:", ks)
    print("第一个值类型:", type(inner[ks[0]]))

print()
print("=== 是否有 charStringsIndex ===")
for nm in ("charStringsIndex", "charStringsList", "index"):
    v = getattr(cs, nm, None)
    print("  %-20s %s" % (nm, type(v).__name__ if v is not None else "无"))

print()
print("=== CharStringsIndex 的方法 ===")
ci = getattr(cs, "charStringsIndex", None)
if ci is not None:
    print([m for m in dir(ci) if not m.startswith("_")])

print()
print("=== fontTools 版本的 CharStrings 源码位置 ===")
import fontTools.cffLib as cl
import inspect
src_file = inspect.getsourcefile(cl.CharStrings)
print(" ", src_file)
src = inspect.getsource(cl.CharStrings.__setitem__)
print(" __setitem__:")
for ln in src.split(chr(10))[:15]:
    print("   ", ln)
mf.close()