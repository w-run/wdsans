#!/usr/bin/env python3
"""m_layoutsort - 修复 Layout 表 FeatureList 排序（R40）

问题: ots-sanitize 报 6 处 WARNING: Layout: tags aren't arranged alphabetically.

实测 GSUB FeatureList 490 条有 6 处逆序:
  [482] vrt2 > sups   [483] sups > subs   [484] subs > sinf
  [485] sinf > numr   [486] numr > dnom   [488] pnum > frac
根因: 历次 m_numfeats/m_frac 等模块直接 append 特性，未排序。

🔴 风险: 排序改变 FeatureRecord 索引，ScriptList 的 742 个 FeatureIndex
       引用都指向这些索引，必须同步重映射，否则所有特性错乱。
"""
import os, sys
from fontTools.ttLib import TTFont

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
OUT = "/workspace/wdsans2/build/VF_R40.otf"


def snapshot_tags(gs):
    feats = gs.FeatureList.FeatureRecord
    res = {}
    if not gs.ScriptList:
        return res
    for sr in gs.ScriptList.ScriptRecord:
        st = sr.ScriptTag
        ls = sr.Script
        if ls.DefaultLangSys:
            fi = list(ls.DefaultLangSys.FeatureIndex)
            res[(st, "Default")] = sorted(feats[i].FeatureTag for i in fi)
        for lr in (ls.LangSysRecord or []):
            fi = list(lr.LangSys.FeatureIndex)
            res[(st, lr.LangSysTag)] = sorted(feats[i].FeatureTag for i in fi)
    return res


def sort_layout(f, tag, dry=False):
    if tag not in f:
        return 0
    tb = f[tag].table
    if not tb.FeatureList or not tb.FeatureList.FeatureRecord:
        return 0
    feats = tb.FeatureList.FeatureRecord
    tags = [fr.FeatureTag for fr in feats]
    if tags == sorted(tags):
        print("  %s FeatureList 已有序（%d 条）" % (tag, len(tags)))
        return 0

    before = snapshot_tags(tb)
    order = sorted(range(len(feats)), key=lambda i: (feats[i].FeatureTag, i))
    old_to_new = dict((old, new) for new, old in enumerate(order))

    if dry:
        print("  %s: %d 条，需重排 %d，重映射 %d 索引" % (tag, len(feats), len(order), len(old_to_new)))
        return len(order)

    tb.FeatureList.FeatureRecord = [feats[i] for i in order]

    n_remap = 0
    if tb.ScriptList:
        for sr in tb.ScriptList.ScriptRecord:
            ls = sr.Script
            if ls.DefaultLangSys:
                ls.DefaultLangSys.FeatureIndex = [old_to_new.get(i, i) for i in ls.DefaultLangSys.FeatureIndex]
                n_remap += 1
            for lr in (ls.LangSysRecord or []):
                lr.LangSys.FeatureIndex = [old_to_new.get(i, i) for i in lr.LangSys.FeatureIndex]
                n_remap += 1

    after = snapshot_tags(tb)
    ok = True
    for k in before:
        if before.get(k) != after.get(k):
            ok = False
            print("    !! %s 引用变了" % (k,))

    new_tags = [fr.FeatureTag for fr in tb.FeatureList.FeatureRecord]
    sorted_ok = new_tags == sorted(new_tags)
    print("  %s: %d 条重排, %d LangSys 重映射, 有序=%s, 引用一致=%s" % (tag, len(order), n_remap, sorted_ok, ok))
    return len(order)


def main(dry=False):
    print("m_layoutsort: %s -> %s dry=%s" % (VF, OUT, dry))
    f = TTFont(VF)
    for tag in ("GSUB", "GPOS"):
        sort_layout(f, tag, dry)
    if dry:
        f.close()
        return
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    f.save(OUT)
    f.close()
    print("  保存 %s (%.1fMB)" % (OUT, os.path.getsize(OUT)/1e6))


if __name__ == "__main__":
    main("--dry" in sys.argv)