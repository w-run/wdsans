#!/usr/bin/env python3
"""ref_chws - 参考字体是否有 chws/vchw"""
from fontTools.ttLib import TTFont

FONTS = [
    ("我们 R38", "/workspace/static/wdsans/WDesignSans-VF.otf"),
    ("我们+chws", "/workspace/wdsans2/build/test_chws_out.otf"),
    ("SHS", "/workspace/wdsans/ref/shs/shs-400.otf"),
    ("OPPO", "/workspace/wdsans/ref/ops/ops-400.ttf"),
    ("HOS", "/workspace/wdsans/ref/hos/hos-400.ttf"),
]

print("%-12s %10s %10s %10s %10s" % ("字体","GSUB特","GPOS特","有chws","有vchw"))
print("-" * 56)
for lbl, p in FONTS:
    f = TTFont(p, lazy=True)
    ns = np = 0
    has_chws = has_vchw = False
    if "GSUB" in f and f["GSUB"].table.FeatureList:
        tags = [fr.FeatureTag for fr in f['GSUB'].table.FeatureList.FeatureRecord]
        ns = len(set(tags))
        has_chws = has_chws or ('chws' in tags)
        has_vchw = has_vchw or ('vchw' in tags)
    if "GPOS" in f and f["GPOS"].table.FeatureList:
        tags = [fr.FeatureTag for fr in f['GPOS'].table.FeatureList.FeatureRecord]
        np = len(set(tags))
        has_chws = has_chws or ('chws' in tags)
        has_vchw = has_vchw or ('vchw' in tags)
    print("%-12s %10d %10d %10s %10s" % (lbl, ns, np, has_chws, has_vchw))
    f.close()

print()
print("=== 结论 ===")
print('若三家参考字体都没有 chws/vchw，则这是可选增强而非缺陷')