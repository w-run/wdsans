#!/usr/bin/env python3
"""probe_sort_impact - 排序影响分析"""
from fontTools.ttLib import TTFont
from collections import Counter

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
gs = f["GSUB"].table
feats = gs.FeatureList.FeatureRecord
print("=== FeatureList 现状 ===")
print("  共 %d 条" % len(feats))
tags = [fr.FeatureTag for fr in feats]
print("  前 5: %s" % tags[:5])
print("  482-490: %s" % tags[482:491])

order = sorted(range(len(feats)), key=lambda i: (feats[i].FeatureTag, i))
old_to_new = {old: new for new, old in enumerate(order)}
print("  重映射表: %d 项" % len(old_to_new))

n_scripts = 0
n_refs = 0
if gs.ScriptList:
    for sr in gs.ScriptList.ScriptRecord:
        n_scripts += 1
        ls = sr.Script
        if ls.DefaultLangSys:
            n_refs += len(ls.DefaultLangSys.FeatureIndex)
        for lr in (ls.LangSysRecord or []):
            n_refs += len(lr.LangSys.FeatureIndex)
print("  ScriptList: %d script, %d FeatureIndex 需重映射" % (n_scripts, n_refs))

sorted_tags = [tags[i] for i in order]
print("  排序后有序: %s" % (sorted_tags == sorted(sorted_tags)))
bad = []
for i in range(1, len(sorted_tags)):
    if sorted_tags[i-1] > sorted_tags[i]:
        bad.append(i)
print("  逆序处: %d" % len(bad))

c = Counter(tags)
dup = dict((k, v) for k, v in c.items() if v > 1)
print("  重复 tag: %d 种" % len(dup))
for k in list(dup)[:6]:
    print("    %s x%d" % (k, dup[k]))
f.close()