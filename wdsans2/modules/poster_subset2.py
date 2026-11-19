#!/usr/bin/env python3
"""poster_subset2 - 按页面实际用字生成子集（避免字体回退）"""
import sys, os, re, json, glob
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools import subset
from fontTools.pens.svgPathPen import SVGPathPen

DIR = '/workspace/static/wdsans/poster'
VF = '/workspace/static/wdsans/WDesignSans-VF.ttf'

# 1) 扫描所有 HTML 的可见文字
chars = set()
for p in glob.glob(DIR + '/*.html'):
    s = open(p, encoding="utf-8").read()
    s = re.sub(r"<style[\\s\\S]*?</style>", " ", s)
    s = re.sub(r"<script[\\s\\S]*?</script>", " ", s)
    # 保留 style 属性里的文字（content 等不用管）
    s = re.sub(r"<[^>]+>", " ", s)
    for ch in s:
        if ord(ch) > 0x20:
            chars.add(ch)

# 2) 补齐常用字符（数字、字母、标点，防止动态内容回退）
EXTRA = ("0123456789" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "abcdefghijklmnopqrstuvwxyz"
         "·—…、，。：；！？（）「」『』《》【】〈〉“”‘’" 
         "／％＋－＝×÷≤≥±°€¥$©®™")
chars.update(EXTRA)
chars = sorted(chars)
print('页面用字 + 常用符号: %d 个' % len(chars))


def make(src, dst, flavor="woff2"):
    f = TTFont(src)
    cm = f.getBestCmap()
    ok = [c for c in chars if ord(c) in cm]
    miss = [c for c in chars if ord(c) not in cm]
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.notdef_outline = True
    opts.recalc_bounds = True
    opts.drop_tables += ["DSIG"]
    opts.flavor = flavor
    sub = subset.Subsetter(options=opts)
    sub.populate(unicodes=[ord(c) for c in ok])
    sub.subset(f)
    f.flavor = flavor
    f.save(dst)
    f.close()
    return len(ok), miss


n1, m1 = make(VF, DIR + '/wd-vf.woff2')
print('  wd-vf.woff2  %d 字  %.0f KB' % (n1, os.path.getsize(DIR+'/wd-vf.woff2')/1024))

if m1:
    print('  ⚠ 缺字: %s' % ''.join(m1))
else:
    print('  ✓ 无缺字')

# 3) 重新导出 glyphdata（含新字）
def paths(path, chs):
    f = TTFont(path)
    gs = f.getGlyphSet(); cm = f.getBestCmap(); hm = f["hmtx"]
    out = {}
    for ch in chs:
        if ord(ch) not in cm:
            continue
        sp = SVGPathPen(gs)
        gs[cm[ord(ch)]].draw(sp)
        d = sp.getCommands()
        if d:
            out[ch] = {"d": d, "w": hm[cm[ord(ch)]][0]}
    f.close()
    return out

glyphs = paths(VF, chars)
data = {"glyphs": glyphs}
json.dump(data, open(DIR + '/glyphdata.json','w'), ensure_ascii=False)
print('  glyphdata.json  %d 字形' % len(glyphs))