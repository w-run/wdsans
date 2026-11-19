#!/usr/bin/env python3
"""verify_markpos_r37 - GDEF 改动后验证 mark 定位仍正常"""
import uharfbuzz as hb

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"

blob = hb.Blob.from_file_path(VF)
face = hb.Face(blob)
font = hb.Font(face)
print("=== GDEF 改动对 mark 定位的影响 ===")

# 测试组合字符定位: a + combining acute
TESTS = [
    ("a\u0301", "a + 尖音符"),
    ("e\u0308", "e + 分音符"),
    ("o\u0303", "o + 波浪号"),
    ("n\u0303", "n + 波浪号"),
    ("A\u030A", "A + 上圆圈"),
]

print("%-16s %-10s %s" % ("测试", "字形数", "advance序列"))
print("-" * 60)
for text, desc in TESTS:
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf)
    infos = buf.glyph_infos
    pos = buf.glyph_positions
    advs = [p.x_advance for p in pos]
    offs = [(p.x_offset, p.y_offset) for p in pos]
    print("%-16s %-10d %s" % (desc, len(infos), advs))
    if len(offs) >= 2:
        print("%-16s %-10s offset[1]=%s" % ("", "", offs[1]))

print()
print("=== 零宽 mark 应为 adv=0 ===")
for text, desc in TESTS:
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf)
    pos = buf.glyph_positions
    if len(pos) >= 2:
        m_adv = pos[1].x_advance
        ok = "OK" if m_adv == 0 else "!! 非零"
        print("  %-16s mark adv=%d  %s" % (desc, m_adv, ok))

print()
print("=== 中文与数字不受影响 ===")
for text in ('永国字体', '0123456789', '设置·消息'):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf)
    tot = sum(p.x_advance for p in buf.glyph_positions)
    print("  %-12s 总宽=%d" % (text, tot))