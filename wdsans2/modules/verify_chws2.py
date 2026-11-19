#!/usr/bin/env python3
"""verify_chws2 - 正确检查 GPOS 里的 chws/vchw"""
from fontTools.ttLib import TTFont

IN = "/workspace/wdsans2/build/test_chws_in.otf"
OUT = "/workspace/wdsans2/build/test_chws_out.otf"

for lbl, p in (("改前", IN), ("改后", OUT)):
    f = TTFont(p, lazy=True)
    gp = f['GPOS'].table
    feats = []
    if gp.FeatureList:
        feats = [fr.FeatureTag for fr in gp.FeatureList.FeatureRecord]
    print("=== %s ===" % lbl)
    uniq = sorted(set(feats))
    print("  GPOS 特性(%d): %s" % (len(uniq), uniq))
    for tag in ('chws', 'vchw'):
        n = feats.count(tag)
        print('    %-5s 出现 %d 次' % (tag, n))
    print('  GPOS lookups: %d' % len(gp.LookupList.Lookup))
    f.close()
    print()

print("=== chws 挂到哪些 script/lang ===")
f = TTFont(OUT, lazy=True)
gp = f['GPOS'].table
feats = [fr.FeatureTag for fr in gp.FeatureList.FeatureRecord]
chws_idx = set(i for i, t in enumerate(feats) if t in ('chws', 'vchw'))
print("  chws/vchw 的 FeatureIndex: %s" % sorted(chws_idx))
if gp.ScriptList:
    for sr in gp.ScriptList.ScriptRecord:
        tag = sr.ScriptTag
        ls = sr.Script
        if ls.DefaultLangSys:
            fi = list(ls.DefaultLangSys.FeatureIndex)
            hit = chws_idx & set(fi)
            if hit:
                print("  %s/Default 含 chws: %s" % (tag, sorted(hit)))
        for lr in (ls.LangSysRecord or []):
            fi = list(lr.LangSys.FeatureIndex)
            hit = chws_idx & set(fi)
            if hit:
                print("  %s/%s 含 chws: %s" % (tag, lr.LangSysTag, sorted(hit)))
f.close()