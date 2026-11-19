#!/usr/bin/env python3
"""probe_302e - 检查 U+302E/302F 的性质"""
from fontTools.ttLib import TTFont
import unicodedata

VF = "/workspace/wdsans2/build/VF_R37.otf"
SHS = "/workspace/wdsans/ref/shs/shs-400.otf"
f = TTFont(VF, lazy=True)
cm = f.getBestCmap(); h = f['hmtx']
print("=== U+302E / U+302F ===")
for cp in (0x302E, 0x302F, 0x302A, 0x302B, 0x302C, 0x302D):
    if cp not in cm:
        print("  U+%04X 无" % cp)
        continue
    gn = cm[cp]
    cat = unicodedata.category(chr(cp))
    nm = unicodedata.name(chr(cp), "?")
    adv = h[gn][0]
    print("  U+%04X %-38s %s adv=%-4d %s" % (
        cp, nm[:38], cat, adv, gn))

print()
print("=== 按 category 分类含义 ===")
print('  Mn = Mark, Nonspacing  -> 真正应进 mark class')
print('  Mc = Mark, Spacing      -> 有 advance，不应进 mark class')
print('  Me = Mark, Enclosing    -> 包围型，应进 mark class')

print()
print("=== 全库按 category 统计组合类字符 ===")
from collections import Counter
c = Counter()
examples = {}
for cp, gn in cm.items():
    try:
        cat = unicodedata.category(chr(cp))
    except Exception:
        continue
    if cat in ('Mn', 'Mc', 'Me'):
        c[cat] += 1
        examples.setdefault(cat, []).append((cp, h[gn][0]))
for cat in ('Mn', 'Mc', 'Me'):
    n = c.get(cat, 0)
    print("  %s: %d 个" % (cat, n))
    if cat == 'Mc':
        for cp, adv in examples.get(cat, []):
            print("      U+%04X adv=%d" % (cp, adv))

print()
print("=== SHS 原版怎么处理 U+302E/302F ===")
g = TTFont(SHS, lazy=True)
gcm = g.getBestCmap()
gcd = g["GDEF"].table.GlyphClassDef.classDefs
for cp in (0x302E, 0x302F):
    if cp not in gcm: continue
    gn = gcm[cp]
    print("  U+%04X %-14s class=%s" % (cp, gn, gcd.get(gn, "未分类")))
g.close()
f.close()