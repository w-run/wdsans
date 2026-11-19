#!/usr/bin/env python3
"""probe_mark_range - 扫描所有组合类字符，确定 GDEF 分类范围"""
from fontTools.ttLib import TTFont
import unicodedata

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
cm = f.getBestCmap()
gd = f["GDEF"].table
cd = gd.GlyphClassDef.classDefs if gd.GlyphClassDef else {}

# 当前已标 mark 的 4 个
print("=== 当前已标 mark 的 4 个 glyph ===")
cur = [gn for gn, c in cd.items() if c == 3]
rev = {}
for cp, gn in cm.items(): rev.setdefault(gn, []).append(cp)
for gn in cur:
    cps = rev.get(gn, [])
    desc = ", ".join("U+%04X" % c for c in cps[:4]) or "无映射"
    print("  %-16s %s" % (gn, desc))

print()
print("=== 扫描 unicodedata 判定为 Mn/Mc/Me 的字符 ===")
marks = []
risk = []
for cp, gn in cm.items():
    try:
        cat = unicodedata.category(chr(cp))
    except Exception:
        continue
    if cat in ('Mn', 'Mc', 'Me'):
        marks.append((cp, gn, cat))
        # 检查同一 glyph 是否也被非组合字符映射（危险）
        others = [c for c in rev.get(gn, []) if c != cp]
        for oc in others:
            try:
                ocat = unicodedata.category(chr(oc))
            except Exception:
                ocat = '?'
            if ocat not in ('Mn', 'Mc', 'Me'):
                risk.append((cp, gn, oc, ocat))
                break

print("  unicodedata 组合类字符总数: %d" % len(marks))
print("  其中已在 GDEF mark: %d" % sum(1 for cp, gn, _ in marks if cd.get(gn) == 3))
print("  需要补充: %d" % sum(1 for cp, gn, _ in marks if cd.get(gn) != 3))

print()
print("=== 🔴 风险: 组合字符与普通字符共用 glyph ===")
if risk:
    for cp, gn, oc, ocat in risk[:15]:
        print("  %s <- U+%04X(Mn) + U+%04X(%s)  共用" % (gn, cp, oc, ocat))
    print("  合计 %d 处冲突（这些 glyph 不能简单标为 mark）" % len(risk))
else:
    print("  无冲突")

print()
print("=== 按 Unicode 区块统计需补充的 ===")
from collections import Counter
blk = Counter()
for cp, gn, cat in marks:
    if cd.get(gn) == 3: continue
    if 0x300 <= cp <= 0x36F: blk['Combining Diacritical Marks'] += 1
    elif 0x483 <= cp <= 0x489: blk['Cyrillic'] += 1
    elif 0x591 <= cp <= 0x5C7: blk['Hebrew'] += 1
    elif 0x610 <= cp <= 0x61A: blk['Arabic'] += 1
    elif 0x64B <= cp <= 0x65F: blk['Arabic marks'] += 1
    elif 0x670 <= cp <= 0x6D3: blk['Arabic/Syriac'] += 1
    elif 0x900 <= cp <= 0x97F: blk['Devanagari'] += 1
    elif 0x1AB0 <= cp <= 0x1AFF: blk['Comb Diacr Ext'] += 1
    elif 0x1DC0 <= cp <= 0x1DFF: blk['Comb Diacr Suppl'] += 1
    elif 0x20D0 <= cp <= 0x20FF: blk['Comb Diacr Symbols'] += 1
    elif 0x302A <= cp <= 0x302F: blk['CJK Tone Marks'] += 1
    elif 0x3099 <= cp <= 0x309A: blk['Kana Voicing'] += 1
    elif 0xFE00 <= cp <= 0xFE0F: blk['Variation Selectors'] += 1
    elif 0xFE20 <= cp <= 0xFE2F: blk['Comb Half Marks'] += 1
    elif 0xE0100 <= cp <= 0xE01EF: blk['Var Selectors Suppl'] += 1
    else: blk['其他 (U+%04X)' % cp] += 1
for k, v in sorted(blk.items(), key=lambda x: -x[1]):
    print("  %-28s %d" % (k, v))

f.close()