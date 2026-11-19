#!/usr/bin/env python3
"""verify_chws - 验证 chws_tool 的改动"""
from fontTools.ttLib import TTFont

IN = "/workspace/wdsans2/build/test_chws_in.otf"
OUT = "/workspace/wdsans2/build/test_chws_out.otf"

def info(p, lbl):
    f = TTFont(p, lazy=True)
    print("=== %s ===" % lbl)
    print("  glyphs=%d cmap=%d" % (f["maxp"].numGlyphs, len(f.getBestCmap())))
    if "GSUB" in f:
        gs = f['GSUB'].table
        feats = []
        if gs.FeatureList:
            feats = sorted(set(fr.FeatureTag for fr in gs.FeatureList.FeatureRecord))
        print("  特性(%d): %s" % (len(feats), feats))
        has_chws = 'chws' in feats
        has_vchw = 'vchw' in feats
        print('  有 chws: %s   有 vchw: %s' % (has_chws, has_vchw))
        print('  lookups: %d' % len(gs.LookupList.Lookup))
    for t in ("GDEF", "GPOS", "OS/2", "fvar", "STAT", "name", "hmtx", "head"):
        print('  %-6s %s' % (t, t in f))
    f.close()
    print()

info(IN, '改前')
info(OUT, '改后 (chws_tool)')

print("=== 关键度量对比（不能变）===")
for lbl, p in (("改前", IN), ("改后", OUT)):
    f = TTFont(p, lazy=True)
    o = f['OS/2']
    n_av = 0
    if 'STAT' in f:
        st = f['STAT'].table
        if st.AxisValueArray:
            n_av = len(st.AxisValueArray.AxisValue)
    zh = sum(1 for r in f['name'].names if r.langID == 0x804)
    cd = f['GDEF'].table.GlyphClassDef.classDefs
    mk = sum(1 for v in cd.values() if v == 3)
    rev = f['head'].fontRevision
    typo = (o.sTypoAscender - o.sTypoDescender) / 1000.0
    print("  %s: head.rev=%.3f OS2v=%d typo=%.2fem STAT=%d zh=%d mark=%d" % (
        lbl, rev, o.version, typo, n_av, zh, mk))
    f.close()