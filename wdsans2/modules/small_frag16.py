#!/usr/bin/env python3
"""small_frag16 - 定位 16px 下块数差异最大的字"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-FlatApex-Regular.otf",
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
}
CHARS = "永国字体设计的一是在不了有和人这中大为上个我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严"

def render(path, ch, px):
    try: ft = ImageFont.truetype(path, px)
    except Exception: return None
    img = Image.new("L", (px*3, px*3), 0)
    ImageDraw.Draw(img).text((px//2, px//2), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    if not len(r) or not len(c): return None
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def blocks(bm):
    if bm is None or bm.sum()==0: return None
    return int(ndimage.label(bm)[1])

rows = []
for ch in CHARS:
    a = blocks(render(FONTS["我们"], ch, 16))
    b = blocks(render(FONTS["SHS"], ch, 16))
    if a is None or b is None: continue
    rows.append((a-b, ch, a, b))

rows.sort(reverse=True)
print("=== 16px 块数差 top-15（我们 - SHS）===")
print("%-4s %6s %6s %6s" % ("字", "我们", "SHS", "差"))
for d, ch, a, b in rows[:15]:
    print("%-4s %6d %6d %+6d" % (ch, a, b, d))

print()
print("=== 分布 ===")
ds = [d for d,_,_,_ in rows]
import collections
cnt = collections.Counter(ds)
for k in sorted(cnt):
    print("  差 %+d: %d 字" % (k, cnt[k]))
print()
print("  总字 %d / 块数差 >0 的 %d 字 (%.1f%%)" % (
    len(rows), sum(1 for d in ds if d>0), 100*sum(1 for d in ds if d>0)/len(rows)))
