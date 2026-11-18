#!/usr/bin/env python3
"""small_size - 小字号笔画完整性测试

动机: 本字体面向手机 UI，实际使用多为 12-16px。
      此前所有测量都在 96px 以上，小字号下的笔画粘连/断裂从未验证。

测项（12/14/16/24px，四字体对比）:
  1. 墨量占比（笔画粗细是否失真）
  2. 连通块数（笔画是否断裂或粘连）
  3. 与 SHS 的逐像素差异（继承结构是否保持）
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-FlatApex-Regular.otf",
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
}
SIZES = [12, 14, 16, 24]
CHARS = "永国字体设计的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严"

def render(path, ch, px):
    try:
        ft = ImageFont.truetype(path, px)
    except Exception:
        return None
    img = Image.new("L", (px*3, px*3), 0)
    ImageDraw.Draw(img).text((px//2, px//2), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    if not len(r) or not len(c): return None
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def metrics(bm):
    if bm is None or bm.size == 0: return None
    n = bm.sum()
    if n == 0: return None
    lab, nb = ndimage.label(bm)
    return dict(ink=float(n), area=float(bm.size),
                ratio=float(n)/bm.size, blocks=int(nb),
                h=int(bm.shape[0]), w=int(bm.shape[1]))

print("=== 小字号笔画完整性（%d 字 × %d 字号 × %d 字体）===" % (
    len(CHARS), len(SIZES), len(FONTS)))
print()

for px in SIZES:
    print("--- %dpx ---" % px)
    hdr = "%-6s" % "字体"
    for k in ("墨量%", "块数", "均高", "均宽"):
        hdr += " %8s" % k
    print(hdr)
    for name, path in FONTS.items():
        inks, blocks, hs, ws = [], [], [], []
        for ch in CHARS:
            bm = render(path, ch, px)
            m = metrics(bm)
            if not m: continue
            inks.append(m["ratio"]*100)
            blocks.append(m["blocks"])
            hs.append(m["h"]); ws.append(m["w"])
        if not inks: 
            print("%-6s 无数据" % name); continue
        print("%-6s %8.1f %8.2f %8.1f %8.1f" % (
            name, np.mean(inks), np.mean(blocks), np.mean(hs), np.mean(ws)))
    print()

print("=== 与 SHS 的差异（本字体 - SHS）===")
for px in SIZES:
    di, db = [], []
    for ch in CHARS:
        a = metrics(render(FONTS["我们"], ch, px))
        b = metrics(render(FONTS["SHS"], ch, px))
        if not a or not b: continue
        di.append(a["ratio"]*100 - b["ratio"]*100)
        db.append(a["blocks"] - b["blocks"])
    if not di: continue
    print("  %2dpx  墨量差 %+6.2f%%  块数差 %+6.3f  (n=%d)" % (
        px, np.mean(di), np.mean(db), len(di)))
