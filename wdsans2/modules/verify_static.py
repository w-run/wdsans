#!/usr/bin/env python3
"""verify_static - 验证平顶静态版的特性、kern、竖排是否完整"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import uharfbuzz as hb
from fontTools.ttLib import TTFont

FA = '/workspace/static/wdsans/WDesignSans-FlatApex-Regular.otf'
VF = '/workspace/static/wdsans/WDesignSans-VF.otf'

data = open(FA, 'rb').read()


def gids(text, feats=None, dirn='ltr', script='latn', lang='en'):
    blob = hb.Blob(data); face = hb.Face(blob); font = hb.Font(face)
    b = hb.Buffer(); b.add_str(text)
    b.direction = dirn; b.script = script; b.language = lang
    if feats:
        hb.shape(font, b, feats)
    else:
        hb.shape(font, b)
    return [i.codepoint for i in b.glyph_infos]


def adv(text, feats=None, script='latn'):
    blob = hb.Blob(data); face = hb.Face(blob); font = hb.Font(face)
    b = hb.Buffer(); b.add_str(text)
    b.direction = 'ltr'; b.script = script; b.language = 'en'
    if feats:
        hb.shape(font, b, feats)
    else:
        hb.shape(font, b)
    return sum(font.get_glyph_h_advance(i.codepoint) for i in b.glyph_infos)


print('=== 数字特性（中文环境）===')
print('  默认 123 : %s' % gids('123', None, 'ltr', 'latn', 'en'))
print('  sups 123 : %s' % gids('123', {'sups': True}, 'ltr', 'latn', 'en'))
print('  subs 123 : %s' % gids('123', {'subs': True}, 'ltr', 'latn', 'en'))
print('  frac 1/2 : %s' % gids('1/2', {'frac': True}, 'ltr', 'latn', 'en'))
print('  numr 123 : %s' % gids('123', {'numr': True}, 'ltr', 'latn', 'en'))
print('  dnom 123 : %s' % gids('123', {'dnom': True}, 'ltr', 'latn', 'en'))
print('  pnum 123 : %s' % gids('123', {'pnum': True}, 'ltr', 'latn', 'en'))

print()
print('=== 中文环境下 sups（ZHS LangSys 是否注册）===')
print('  zh-hans sups 123: %s' % gids('123', {'sups': True}, 'ltr', 'hani', 'zh-Hans'))

print()
print('=== calt 冒号居中 ===')
print('  12:34 = %s' % gids('12:34', None, 'ltr', 'latn', 'en'))
print('  a:b   = %s' % gids('a:b', None, 'ltr', 'latn', 'en'))

print()
print('=== 竖排 ===')
cnt = 0
for ch in '：—…。「」！？～':
    h = gids(ch, None, 'ltr', 'hani', 'zh-Hans')
    v = gids(ch, None, 'ttb', 'hani', 'zh-Hans')
    if h != v: cnt += 1
    print('  %s 横=%s 竖=%s %s' % (ch, h, v, 'OK' if h != v else '未替换'))
print('  -> %d/9' % cnt)

print()
print('=== 拉丁 kerning ===')
for t in ['AV', 'AY', 'WA', 'VA', 'To', 'AT']:
    print('  %-3s adv=%4d' % (t, adv(t)))

print()
print('=== 中文宽度（应 1000/字）===')
for t in ['永', '永国字体', '永国字体设计的书']:
    print('  %-14s adv=%d' % (t, adv(t, None, 'hani')))

print()
print('=== 表完整性对比 ===')
for p, n in [(FA, 'FlatApex'), (VF, 'VF ')]:
    f = TTFont(p, lazy=True)
    tabs = sorted(t for t in f.reader.tables if t != 'GlyphOrder')
    print('  %s %d 表: %s' % (n, len(tabs), ' '.join(tabs)))
    f.close()