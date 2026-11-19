#!/usr/bin/env python3
"""chws_behavior - 验证 chws 的实际行为与副作用"""
import uharfbuzz as hb

IN = "/workspace/wdsans2/build/test_chws_in.otf"
OUT = "/workspace/wdsans2/build/test_chws_out.otf"

def load(p):
    return hb.Font(hb.Face(hb.Blob.from_file_path(p)))

def shape(font, text, feats=None):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if feats:
        hb.shape(font, buf, feats)
    else:
        hb.shape(font, buf)
    return [(p.x_advance, p.x_offset, p.y_offset) for p in buf.glyph_positions]

fa = load(IN); fb = load(OUT)

print("=== 1. 默认排版不能变（chws 是 opt-in 特性）===")
TESTS = ['永国字体', '设置·消息', '0123456789', 'Hamburgefonstiv',
         '。、，：；！？', '「测试」', '《书名》', '（括号）', '12:34', 'a:b', '1/2']
diff = 0
for t in TESTS:
    a = shape(fa, t); b = shape(fb, t)
    if a != b:
        diff += 1
        print("  !! %s 不同" % t)
        print("     改前: %s" % a[:4])
        print("     改后: %s" % b[:4])
print("  %d 项测试，%d 项不同 %s" % (len(TESTS), diff, "OK" if diff == 0 else "!! 有副作用"))

print()
print("=== 2. 启用 chws 后的效果 ===")
chws_tests = ['、。，「」', '（）《》', 'あ、い。う', '漢字、かな。']
for t in chws_tests:
    a = shape(fa, t)
    b = shape(fb, t, {'chws': True})
    print("  %-14s" % t)
    print("    无chws: %s" % [x[0] for x in a])
    print("    有chws: %s" % [x[0] for x in b])
    changed = sum(1 for x, y in zip(a, b) if x[0] != y[0])
    print("    宽度变化: %d/%d 个字符" % (changed, len(a)))

print()
print("=== 3. 竖排 vchw ===")
for t in ['、。', '「」']:
    buf = hb.Buffer()
    buf.add_str(t)
    buf.direction = 'ttb'
    buf.script = 'hani'
    buf.language = 'ja'
    hb.shape(fb, buf, {'vchw': True})
    ys = [p.y_advance for p in buf.glyph_positions]
    print("  %-8s 竖排 y_advance: %s" % (t, ys))

print()
print("=== 4. 特性数量确认 ===")
for lbl, p in (("改前", IN), ("改后", OUT)):
    f = __import__('fontTools.ttLib', fromlist=['TTFont']).TTFont(p, lazy=True)
    gs = f['GSUB'].table
    gp = f['GPOS'].table
    ns = sorted(set(fr.FeatureTag for fr in gs.FeatureList.FeatureRecord)) if gs.FeatureList else []
    np = sorted(set(fr.FeatureTag for fr in gp.FeatureList.FeatureRecord)) if gp.FeatureList else []
    print("  %s: GSUB=%d GPOS=%d" % (lbl, len(ns), len(np)))
    # 确认原有 23 个 GSUB 特性都在
    need = ['calt','ccmp','frac','liga','locl','sups','subs','pnum','numr','dnom','vert','vrt2']
    miss = [x for x in need if x not in ns]
    print("    关键 GSUB 特性缺失: %s" % (miss if miss else "无"))
    f.close()