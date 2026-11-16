#!/usr/bin/env python3
"""vi10 - 验证子集里中文竖排与关键特性是否真正可用"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import uharfbuzz as hb

W = '/workspace/static/wdsans/wd-preview.woff2'
data = open(W, 'rb').read()


def gids(text, feats=None, dirn='ltr', script='hani', lang='zh'):
    blob = hb.Blob(data); face = hb.Face(blob); font = hb.Font(face)
    b = hb.Buffer(); b.add_str(text)
    b.direction = dirn; b.script = script; b.language = lang
    if feats:
        hb.shape(font, b, feats)
    else:
        hb.shape(font, b)
    return [i.codepoint for i in b.glyph_infos]


print('=== 子集竖排验证 ===')
for ch in '：—…。「」！？～':
    h = gids(ch, None, 'ltr', 'hani', 'zh')
    v = gids(ch, None, 'ttb', 'hani', 'zh')
    print('  %s  横=%s 竖=%s  %s' % (ch, h, v, 'OK替换' if h != v else '无替换'))

print()
print('=== 数字特性 ===')
print('  sups 123 : %s' % gids('123', {'sups': True}, 'ltr', 'latn', 'en'))
print('  subs 123 : %s' % gids('123', {'subs': True}, 'ltr', 'latn', 'en'))
print('  frac 1/2 : %s' % gids('1/2', {'frac': True}, 'ltr', 'latn', 'en'))
print('  pnum 123 : %s' % gids('123', {'pnum': True}, 'ltr', 'latn', 'en'))
print('  默认 123 : %s' % gids('123', None, 'ltr', 'latn', 'en'))

print()
print('=== calt 冒号居中 ===')
print('  12:34 = %s' % gids('12:34', None, 'ltr', 'latn', 'en'))
print('  a:b   = %s' % gids('a:b', None, 'ltr', 'latn', 'en'))

print()
print('=== 中文字重变化（子集）===')


def adv(text, wght):
    blob = hb.Blob(data); face = hb.Face(blob); font = hb.Font(face)
    font.set_variations({'wght': wght})
    b = hb.Buffer(); b.add_str(text)
    b.direction = 'ltr'; b.script = 'latn'; b.language = 'en'
    hb.shape(font, b)
    return sum(font.get_glyph_h_advance(i.codepoint) for i in b.glyph_infos)


for text in ['Hamburgefonstiv', '永国字体']:
    vals = [adv(text, w) for w in [250, 400, 700, 900]]
    print('  %-18s %s' % (text, vals))