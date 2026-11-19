#!/usr/bin/env python3
"""chws_regress - chws 版本的完整回归测试"""
import uharfbuzz as hb
from fontTools.ttLib import TTFont

IN = "/workspace/static/wdsans/WDesignSans-VF.otf"
OUT = "/workspace/wdsans2/build/test_chws_out.otf"

fa = hb.Font(hb.Face(hb.Blob.from_file_path(IN)))
fb = hb.Font(hb.Face(hb.Blob.from_file_path(OUT)))

def shape(font, text, feats=None, lang=None):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if lang:
        buf.language = lang
    if feats:
        hb.shape(font, buf, feats)
    else:
        hb.shape(font, buf)
    return ([i.codepoint for i in buf.glyph_infos],
            [(p.x_advance, p.x_offset, p.y_offset) for p in buf.glyph_positions])

print("=== 1. 已有功能保持 ===")
CASES = [
    ("永国字体设计", None),
    ("设置·消息·相机", None),
    ("0123456789", None),
    ("Hamburgefonstiv minimum", None),
    ("fifi ffl office", None),
    ("12:34 a:b", None),
    ("123", {"sups": True}),
    ("123", {"subs": True}),
    ("123", {"numr": True}),
    ("123", {"dnom": True}),
    ("1/2 3/4", {"frac": True}),
    ("123", {"pnum": True}),
    ("b\u0301 d\u0301 g\u0303", None),
    ("一\u0301", None),
    ("ABCDEFGHIJ", None),
    ("、。，：；！？", None),
    ("「测试」「引用」", None),
]
diff = 0
for text, feats in CASES:
    a = shape(fa, text, feats)
    b = shape(fb, text, feats)
    if a != b:
        diff += 1
        print("  !! %s feats=%s" % (text[:20], feats))
for lang in ('zh-hans', 'zh-hant', 'ja', 'ko', 'en'):
    a = shape(fa, "永国字体 123", None, lang)
    b = shape(fb, "永国字体 123", None, lang)
    if a != b:
        diff += 1
        print("  !! lang=%s" % lang)
print("  共 %d 用例，%d 不同 %s" % (len(CASES)+5, diff, "OK" if diff == 0 else "!!"))

print()
print("=== 2. 表格结构 ===")
ta = set(TTFont(IN, lazy=True).keys())
tb = set(TTFont(OUT, lazy=True).keys())
print("  表数 %d -> %d  新增 %s  删除 %s" % (len(ta), len(tb), sorted(tb-ta) or "无", sorted(ta-tb) or "无"))

print()
print("=== 3. 关键元数据 ===")
a = TTFont(IN, lazy=True)
b = TTFont(OUT, lazy=True)
for lbl, f in (("改前", a), ("改后", b)):
    o = f['OS/2']
    st = f['STAT'].table
    n_av = len(st.AxisValueArray.AxisValue) if st.AxisValueArray else 0
    zh = sum(1 for r in f['name'].names if r.langID == 0x804)
    cd = f['GDEF'].table.GlyphClassDef.classDefs
    mk = sum(1 for v in cd.values() if v == 3)
    rev = f['head'].fontRevision
    typo = (o.sTypoAscender - o.sTypoDescender) / 1000.0
    ng = f['maxp'].numGlyphs
    nc = len(f.getBestCmap())
    print("  %s: rev=%.3f OS2v=%d typo=%.2f STAT=%d zh=%d mark=%d glyphs=%d cmap=%d" % (lbl, rev, o.version, typo, n_av, zh, mk, ng, nc))
a.close()
b.close()