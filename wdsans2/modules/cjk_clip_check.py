#!/usr/bin/env python3
"""cjk_clip_check - 确认 CJK 不被裁切"""
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
o = f["OS/2"]
cm = f.getBestCmap(); gs = f.getGlyphSet()
TOP = o.sTypoAscender; BOT = o.sTypoDescender
print("R36 typo 行框: %d ~ %d" % (BOT, TOP))
print()
print("=== 全部 CJK ===")
cjk = [c for c in cm if 0x4E00 <= c <= 0x9FFF]
over = under = 0
worst_hi = worst_lo = None
for cp in cjk:
    bp = BoundsPen(gs)
    try:
        gs[cm[cp]].draw(bp)
    except Exception:
        continue
    if not bp.bounds: continue
    if bp.bounds[3] > TOP:
        over += 1
        if worst_hi is None or bp.bounds[3] > worst_hi[1]: worst_hi = (cp, bp.bounds[3])
    if bp.bounds[1] < BOT:
        under += 1
        if worst_lo is None or bp.bounds[1] < worst_lo[1]: worst_lo = (cp, bp.bounds[1])
print("  CJK %d 字: 超高 %d / 超低 %d" % (len(cjk), over, under))
if worst_hi: print('  最高: %s y=%.0f (上界 %d)' % (chr(worst_hi[0]), worst_hi[1], TOP))
if worst_lo: print('  最低: %s y=%.0f (下界 %d)' % (chr(worst_lo[0]), worst_lo[1], BOT))
print()
print("=== 常用字检查（508 字）===")
COMMON = "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严龙飞"
chit = 0; cover = 0
bad = []
for ch in COMMON:
    cp = ord(ch)
    if cp not in cm: continue
    cover += 1
    bp = BoundsPen(gs)
    try:
        gs[cm[cp]].draw(bp)
    except Exception:
        continue
    if not bp.bounds: continue
    if bp.bounds[3] > TOP or bp.bounds[1] < BOT:
        chit += 1
        bad.append((ch, bp.bounds[1], bp.bounds[3]))
for ch, y0, y1 in bad[:5]:
    print('  超出: %s y=%.0f~%.0f' % (ch, y0, y1))
print('  常用 %d 字: 超出 %d 个' % (cover, chit))
f.close()