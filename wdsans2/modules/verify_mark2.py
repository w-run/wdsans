#!/usr/bin/env python3
"""verify_mark2 - 用无可预组合的字符测 mark 定位"""
import uharfbuzz as hb

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
R36 = "/workspace/wdsans2/build/VF_R36_backup.otf"

def test(path, label):
    blob = hb.Blob.from_file_path(path)
    face = hb.Face(blob)
    font = hb.Font(face)
    print('=== %s ===' % label)
    # 这些组合没有预组合字符，必须靠 mark 定位
    TESTS = [
        ("b\u0301", "b+acute (无预组合)"),
        ("d\u0301", "d+acute"),
        ("g\u0303", "g+tilde"),
        ("k\u0308", "k+diaeresis"),
        ("\u4e00\u0301", "一+acute"),
    ]
    print("  %-20s %6s %14s %22s" % ("测试", "字形数", "advance", "mark offset"))
    print("  " + "-" * 66)
    for text, desc in TESTS:
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf)
        pos = buf.glyph_positions
        advs = [p.x_advance for p in pos]
        if len(pos) >= 2:
            off = '(%d,%d)' % (pos[1].x_offset, pos[1].y_offset)
        else:
            off = '-'
        print("  %-20s %6d %14s %22s" % (desc, len(pos), advs, off))
    print()

test(R36, 'R36 (GDEF mark=4)')
test(VF, 'R37 (GDEF mark=30)')

print("=== 结论 ===")
print('若两版 offset 相同 -> GDEF 扩充未影响既有 mark 定位')