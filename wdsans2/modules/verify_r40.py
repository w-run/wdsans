#!/usr/bin/env python3
"""verify_r40 - 排序后逐字符验证渲染不变"""
import uharfbuzz as hb
from fontTools.ttLib import TTFont

OLD = "/workspace/static/wdsans/WDesignSans-VF.otf"
NEW = "/workspace/wdsans2/build/VF_R40.otf"

fa = hb.Font(hb.Face(hb.Blob.from_file_path(OLD)))
fb = hb.Font(hb.Face(hb.Blob.from_file_path(NEW)))

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

print("=== 1. 全特性覆盖测试 ===")
CASES = [
    ("123", {"sups": True}), ("123", {"subs": True}),
    ("123", {"sinf": True}), ("123", {"numr": True}),
    ("123", {"dnom": True}), ("1/2 3/4", {"frac": True}),
    ("123", {"pnum": True}), ("123", {"tnum": True}),
    ("fifi ffl", {"liga": True}), ("fifi ffl", {"dlig": True}),
    ("12:34", {"calt": True}), ("(a)", {"aalt": True}),
    ("ABC", {"smcp": True}), ("abc", {"fwid": True}),
    ("abc", {"hwid": True}), ("abc", {"pwid": True}),
    ("あ", {"vert": True}), ("あ", {"vrt2": True}),
    ("、。", {"chws": True}), ("、。", {"halt": True}),
    ("、。", {"palt": True}), ("AV", {"kern": True}),
    ("永国字体", None), ("设置·消息", None),
    ("0123456789", None), ("Hamburgefonstiv", None),
    ("b\u0301 d\u0301", None), ("一\u0301", None),
]
diff = 0
for text, feats in CASES:
    a = shape(fa, text, feats)
    b = shape(fb, text, feats)
    if a != b:
        diff += 1
        print("  !! %r feats=%s" % (text, feats))
        print("     旧: %s" % (a,))
        print("     新: %s" % (b,))
print("  %d 用例，%d 不同 %s" % (len(CASES), diff, "OK" if diff == 0 else "!! 有变化"))

print()
print("=== 2. 5 种语言 × 各特性 ===")
diff2 = 0
for lang in ('zh-hans', 'zh-hant', 'ja', 'ko', 'en'):
    for feats in (None, {"sups": True}, {"frac": True}, {"palt": True}):
        a = shape(fa, "永国字体 123 1/2 、。", feats, lang)
        b = shape(fb, "永国字体 123 1/2 、。", feats, lang)
        if a != b:
            diff2 += 1
            print("  !! lang=%s feats=%s" % (lang, feats))
print("  20 组，%d 不同 %s" % (diff2, "OK" if diff2 == 0 else "!!"))

print()
print("=== 3. 大规模字符集（3755 常用字）===")
COMMON = "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严龙飞"
diff3 = 0
n = 0
for ch in COMMON:
    n += 1
    a = shape(fa, ch)
    b = shape(fb, ch)
    if a != b:
        diff3 += 1
        if diff3 <= 3:
            print("  !! %s" % ch)
print("  %d 字，%d 不同 %s" % (n, diff3, "OK" if diff3 == 0 else "!!"))

print()
print("=== 4. 表结构与元数据 ===")
a = TTFont(OLD, lazy=True)
b = TTFont(NEW, lazy=True)
ta = set(a.keys()); tb = set(b.keys())
print("  表: %d -> %d，新增 %s 删除 %s" % (len(ta), len(tb), sorted(tb-ta) or "无", sorted(ta-tb) or "无"))
for lbl, f in (("旧", a), ("新", b)):
    o = f['OS/2']
    gst = f['GSUB'].table
    gpt = f['GPOS'].table
    ns = len(gst.FeatureList.FeatureRecord)
    np2 = len(gpt.FeatureList.FeatureRecord)
    zh = sum(1 for r in f['name'].names if r.langID == 0x804)
    st = f['STAT'].table
    n_av = len(st.AxisValueArray.AxisValue) if st.AxisValueArray else 0
    print("  %s: GSUB特=%d GPOS特=%d rev=%.3f OS2v=%d STAT=%d zh=%d glyphs=%d" % (lbl, ns, np2, f["head"].fontRevision, o.version, n_av, zh, f["maxp"].numGlyphs))
a.close()
b.close()