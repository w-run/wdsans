#!/usr/bin/env python3
"""vi11 - 验证子集（先解压 woff2，HarfBuzz 不能直接读压缩格式）"""
import sys, io
sys.path.insert(0, '/workspace/wdsans2/probe')
import uharfbuzz as hb
from fontTools.ttLib import TTFont

W = '/workspace/static/wdsans/wd-preview.woff2'
f = TTFont(W); f.flavor = None
buf = io.BytesIO(); f.save(buf); f.close()
data = buf.getvalue()
print('解压后 %.2f MB' % (len(data) / 1e6))


def gids(text, feats=None, dirn='ltr', script='hani', lang='zh'):
    blob = hb.Blob(data); face = hb.Face(blob); font = hb.Font(face)
    b = hb.Buffer(); b.add_str(text)
    b.direction = dirn; b.script = script; b.language = lang
    if feats:
        hb.shape(font, b, feats)
    else:
        hb.shape(font, b)
    return [i.codepoint for i in b.glyph_infos]


print('=== 竖排 ===')
cnt = 0
for ch in '：—…。「」！？～':
    h = gids(ch, None, 'ltr', 'hani', 'zh')
    v = gids(ch, None, 'ttb', 'hani', 'zh')
    ok = h != v
    if ok: cnt += 1
    print('  %s  横=%s 竖=%s  %s' % (ch, h, v, 'OK' if ok else '未替换'))
print('  -> %d/9 有竖排替换' % cnt)

print()
print('=== 数字特性 ===')
print('  默认 123 : %s' % gids('123', None, 'ltr', 'latn', 'en'))
print('  sups 123 : %s' % gids('123', {'sups': True}, 'ltr', 'latn', 'en'))
print('  subs 123 : %s' % gids('123', {'subs': True}, 'ltr', 'latn', 'en'))
print('  frac 1/2 : %s' % gids('1/2', {'frac': True}, 'ltr', 'latn', 'en'))
print('  pnum 123 : %s' % gids('123', {'pnum': True}, 'ltr', 'latn', 'en'))

print()
print('=== calt 冒号 ===')
print('  12:34 = %s' % gids('12:34', None, 'ltr', 'latn', 'en'))
print('  a:b   = %s' % gids('a:b', None, 'ltr', 'latn', 'en'))

print()
print('=== 子集字重变化 ===')


def adv(text, wght, script='latn'):
    blob = hb.Blob(data); face = hb.Face(blob); font = hb.Font(face)
    font.set_variations({'wght': wght})
    b = hb.Buffer(); b.add_str(text)
    b.direction = 'ltr'; b.script = script; b.language = 'en'
    hb.shape(font, b)
    return sum(font.get_glyph_h_advance(i.codepoint) for i in b.glyph_infos)


print('  Hamburgefonstiv %s' % [adv('Hamburgefonstiv', w) for w in [250,400,700,900]])