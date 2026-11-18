#!/usr/bin/env python3
"""coverage_audit - 字形覆盖全面性审计
检查: 1) 与 SHS/OPPO/HOS 的 cmap 差异
      2) 常用字覆盖
      3) 拉丁区块覆盖
"""
import sys
from fontTools.ttLib import TTFont

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS": "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS": "/workspace/wdsans/ref/hos/hos-400.ttf",
}

cmaps = {}
for name, path in FONTS.items():
    try:
        f = TTFont(path, lazy=True)
        cmaps[name] = set(f.getBestCmap().keys())
        f.close()
    except Exception as e:
        print("跳过 %s: %s" % (name, e))

print("=== cmap 大小 ===")
for n, c in cmaps.items():
    print("  %-5s %d" % (n, len(c)))
print()

ours = cmaps.get("我们", set())
for n in ("SHS", "OPPO", "HOS"):
    if n not in cmaps: continue
    other = cmaps[n]
    missing = other - ours
    extra = ours - other
    print("vs %s: 我们缺 %d, 我们多 %d" % (n, len(missing), len(extra)))
    if missing:
        s = "".join(chr(c) for c in sorted(missing)[:60] if 0x20 <= c <= 0xFFFF)
        print("   缺的样例: %s" % s)
print()

# 常用字覆盖
COMMON = "的一是不了人我在有他这中大来上国个到说们为子和你地出道也时年得就那要下以生会自着去之过家学对可她里后小么心多天而能好都然没日于起还发成事只作当想看文无开手十用主行方又如前所本见经头面公同三已老从动两长知民样现分将外但身些与高意进把法此实回二理美点月明其种声全工己话儿者向情部正名定女问力机给等几很业最间新什打便位因重被走电四第门相次东政海口使教西再平真听世气信北少关并内加化由却代军产入先山五太水万市眼体别处总才场师书比住员九笑性通目华报立马命张活难神数件安表原车白应路期叫死常提感金何更反合放做系计或司利受光王果亲界及今京务制解各任至清物台象记边共风战干接它许八特觉望直服毛林题建南度统色字请交爱让认算论百吃义科怎元社术结六功指思非流每青管夫连远资队跟带花快条院变联言权往展该领传近留红治决周保达办运武半候七必城父强步完革深区即求品士转量空甚众技轻程告江语英基派满式李息写呢识极令黄德收脸钱党倒未持取设始版双历越史商千片容研像找友孩站广改议形委早房音火际则首单据导影失拿网香似斯专石若兵弟谁校读志飞观争究包组造落视济喜离虽坐集编宝谈府拉黑且随格尽剑讲布杀微怕母调局根曾准团段终乐切级克精哪官示冷块破假队宣续买房养春"
miss = [ch for ch in COMMON if ord(ch) not in ours]
print("常用 508 字缺失: %d %s" % (len(miss), "".join(miss) if miss else ""))
print()

# 拉丁区块
BLOCKS = [
    ("Basic Latin", 0x0020, 0x007E),
    ("Latin-1 Sup", 0x00A0, 0x00FF),
    ("Latin Ext-A", 0x0100, 0x017F),
    ("Latin Ext-B", 0x0180, 0x024F),
    ("IPA", 0x0250, 0x02AF),
    ("Spacing Mod", 0x02B0, 0x02FF),
    ("Comb Diacrit", 0x0300, 0x036F),
    ("Greek", 0x0370, 0x03FF),
    ("Cyrillic", 0x0400, 0x04FF),
    ("Gen Punct", 0x2000, 0x206F),
    ("Currency", 0x20A0, 0x20CF),
    ("Letterlike", 0x2100, 0x214F),
    ("Number Forms", 0x2150, 0x218F),
    ("Arrows", 0x2190, 0x21FF),
    ("Math Ops", 0x2200, 0x22FF),
    ("Box Drawing", 0x2500, 0x257F),
    ("CJK Punct", 0x3000, 0x303F),
    ("Hiragana", 0x3040, 0x309F),
    ("Katakana", 0x30A0, 0x30FF),
    ("Hangul", 0xAC00, 0xD7AF),
]
print("=== 区块覆盖（我们 / SHS / OPPO）===")
print("%-14s %-14s %-14s %s" % ("区块", "我们", "SHS", "OPPO"))
for bname, lo, hi in BLOCKS:
    def cnt(s): return sum(1 for c in range(lo, hi+1) if c in s)
    a = cnt(ours); b = cnt(cmaps.get("SHS", set())); c = cnt(cmaps.get("OPPO", set()))
    tot = hi - lo + 1
    mark = ""
    if a < b and b > 0:
        mark = "   <- 少于SHS %d" % (b - a)
    print("%-14s %-14s %-14s %d%s" % (bname, "%d/%d" % (a,tot), "%d/%d" % (b,tot), c, mark))
