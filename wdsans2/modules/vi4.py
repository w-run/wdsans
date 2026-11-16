#!/usr/bin/env python3
"""vi4 - 验证字宽变体（用拉丁与符号，CJK 是等宽 1000 恒定的）"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import uharfbuzz as hb

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
data = open(VF, 'rb').read()


def shape_w(wght, text, script=
            'latn'):
    blob = hb.Blob(data); face = hb.Face(blob); font = hb.Font(face)
    font.set_variations({'wght': wght})
    b = hb.Buffer(); b.add_str(text)
    b.direction = 'ltr'; b.script = script; b.language = 'en'
    hb.shape(font, b)
    return sum(font.get_glyph_h_advance(i.codepoint) for i in b.glyph_infos)


print('=== 拉丁字宽随字重变化 ===')
TESTS = [('Hamburgefonstiv', 'latn'), ('minimum', 'latn'),
         ('0123456789', 'latn'), ('—', 'latn')]
for text, sc in TESTS:
    vals = [shape_w(w, text, sc) for w in [250, 400, 700, 900]]
    flag = '' if len(set(vals)) > 1 else '  <<< 无变化!'
    print('  %-18s 250=%4d 400=%4d 700=%4d 900=%4d%s' %
          (text, *vals, flag))

print()
print('=== CJK advance（应恒定 1000*n）===')
for text in ['永', '永国字体', '永国字体设计的书']:
    vals = [shape_w(w, text, 'hani') for w in [250, 400, 700, 900]]
    print('  %-18s %s' % (text, vals))