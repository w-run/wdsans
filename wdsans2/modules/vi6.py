#!/usr/bin/env python3
"""vi6 - 确认 CJK 通过 locl 访问还是直接 cmap 映射"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import uharfbuzz as hb
from fontTools.ttLib import TTFont

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
f = TTFont(VF, lazy=True)
cm = f.getBestCmap()

print('=== 抽查 CJK 的 cmap 映射 ===')
for ch in '永国字体设计的一是不了在人有':
    cp = ord(ch)
    gn = cm.get(cp)
    print('  %s U+%04X -> %s' % (ch, cp, gn if gn else '未映射!'))

# 检查这些字形是否在 glyphOrder 里
go = f.getGlyphOrder()
print()
print('=== 这些字形是否在字形表 ===')
for ch in '永国':
    gn = cm.get(ord(ch))
    print('  %s -> %s : %s' % (ch, gn, '在' if gn in go else '不在!'))
f.close()

print()
print('=== HarfBuzz 实际渲染 ===')
data = open(VF, 'rb').read()


def gids(text, script, lang):
    blob = hb.Blob(data); face = hb.Face(blob); font = hb.Font(face)
    b = hb.Buffer(); b.add_str(text)
    b.direction = 'ltr'; b.script = script; b.language = lang
    hb.shape(font, b)
    return [(i.codepoint, font.glyph_to_string(i.codepoint)) for i in b.glyph_infos]

print('  永 (hani/zh):    %s' % gids('永', 'hani', 'zh'))
print('  永 (latn/en):    %s' % gids('永', 'latn', 'en'))
print('  永国 (hani/zh):  %s' % gids('永国', 'hani', 'zh'))