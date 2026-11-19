#!/usr/bin/env python3
"""verify_r38 - R38 修复验证 + 无回归检查"""
import uharfbuzz as hb
from fontTools.ttLib import TTFont

R37 = "/workspace/wdsans2/build/VF_R37.otf"
R38 = "/workspace/wdsans2/build/VF_R38.otf"

print("=== 1. 三项修复确认 ===")
print("%-10s %8s %12s %10s %10s" % ("版本","STAT","name平台","zh-CN","nameID17"))
print("-" * 56)
for lbl, p in (("R37", R37), ("R38", R38)):
    f = TTFont(p, lazy=True)
    st = f['STAT'].table
    n_av = len(st.AxisValueArray.AxisValue) if st.AxisValueArray else 0
    plats = sorted(set(r.platformID for r in f['name'].names))
    zh = sum(1 for r in f['name'].names if r.langID == 0x804)
    n17 = [str(r) for r in f['name'].names if r.nameID == 17 and r.langID == 0x804]
    n17s = n17[0] if n17 else '-'
    print("%-10s %8d %12s %10d %10s" % (lbl, n_av, str(plats), zh, n17s))
    f.close()

print()
print("=== 2. 关键不变项（不能回归）===")
print("%-6s %10s %10s %8s %8s %8s" % ("版本","head.rev","OS2ver","mark","glyphs","cmap"))
print("-" * 58)
for lbl, p in (("R37", R37), ("R38", R38)):
    f = TTFont(p, lazy=True)
    cd = f['GDEF'].table.GlyphClassDef.classDefs
    print("%-6s %10.3f %10d %8d %8d %8d" % (
        lbl, f['head'].fontRevision, f['OS/2'].version,
        sum(1 for v in cd.values() if v==3), f['maxp'].numGlyphs, len(f.getBestCmap())))
    f.close()

print()
print("=== 3. HarfBuzz shaping 一致性 ===")
def shape_all(path):
    blob = hb.Blob.from_file_path(path)
    font = hb.Font(hb.Face(blob))
    out = {}
    TESTS = ['永国字体', '0123456789', '设置·消息', 'Hamburgefonstiv',
             'b\u0301', 'd\u0301', 'g\u0303', '一\u0301', '12:34', 'a:b', '1/2']
    for t in TESTS:
        buf = hb.Buffer()
        buf.add_str(t)
        buf.guess_segment_properties()
        hb.shape(font, buf)
        out[t] = ([i.codepoint for i in buf.glyph_infos],
                  [(p.x_advance, p.x_offset, p.y_offset) for p in buf.glyph_positions])
    return out

a = shape_all(R37); b = shape_all(R38)
diff = 0
for t in a:
    same = a[t] == b[t]
    if not same:
        diff += 1
        print("  !! 不同: %s" % t)
print("  %d 项测试，%d 项不同 %s" % (len(a), diff, "OK" if diff==0 else "!!"))

print()
print("=== 4. STAT 条目明细 ===")
f = TTFont(R38, lazy=True)
st = f['STAT'].table
for av in st.AxisValueArray.AxisValue:
    v = getattr(av, 'Value', None)
    nid = getattr(av, 'ValueNameID', None)
    nm = f['name'].getDebugName(nid) if nid else '?'
    print("  Format=%d  wght=%-6s  %s" % (av.Format, v, nm))
f.close()