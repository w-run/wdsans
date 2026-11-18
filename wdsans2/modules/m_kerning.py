#!/usr/bin/env python3
"""m_kerning - 从 Mona Sans 移植拉丁 kerning

问题:
  我们 VF 的 kern 配对记录只有 845 个，Mona 有 3261 个（少 74%）。
  实测 AV 配对墨宽 91px vs Mona 81px（+10px），A/V 未收紧。

字形名交集: 543 个（我们 65,535 vs Mona 797），拉丁常用名全部匹配。

方案:
  1. 从 Mona GPOS 提取全部 kern pair（含 class-based 展开）
  2. 映射到我们的字形名（只保留双方都有的）
  3. 生成新的 PairPos format-1 lookup，追加到我们 GPOS 的 kern feature

注意:
  Mona 有 class-based (Format 2) lookup，需展开成 pair。
  我们已有一个 kern lookup（type 9 扩展，845 对），新增一个独立 lookup 追加即可。
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.otlLib.builder import buildPairPosGlyphs, buildValue

MONA = '/workspace/wdsans/ref/mona/MonaSansVF.ttf'
# kerning 强度系数: Mona 的 kern 值对我们偏紧约 30%
# 实测: 全量注入时 AT 85->75(Mona 81) / LT 68->59(Mona 69) 变差
#       取 0.65 可兼顾"过宽收紧"与"已合适不变差"
KERN_SCALE = float(os.environ.get('WDS_KERN_SCALE', '0.65'))
SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_MOD14')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD15')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}


def extract_mona_kern():
    """提取 Mona 全部 kern pair（展开 class-based）"""
    m = TTFont(MONA)
    g = m['GPOS'].table
    kern_idx = set()
    for fr in g.FeatureList.FeatureRecord:
        if fr.FeatureTag == 'kern':
            kern_idx.update(fr.Feature.LookupListIndex)

    pairs = {}
    for i in sorted(kern_idx):
        lk = g.LookupList.Lookup[i]
        for st in lk.SubTable:
            t = st.ExtSubTable if lk.LookupType == 9 else st
            if not hasattr(t, 'Coverage') or t.Coverage is None:
                continue
            cov = t.Coverage.glyphs
            if hasattr(t, 'PairSet') and t.PairSet:
                for gi, ps in enumerate(t.PairSet):
                    if gi >= len(cov):
                        continue
                    g1 = cov[gi]
                    for pvr in ps.PairValueRecord:
                        v = pvr.Value1.XAdvance if pvr.Value1 else 0
                        if v:
                            pairs[(g1, pvr.SecondGlyph)] = v
            elif hasattr(t, 'ClassDef1') and hasattr(t, 'ClassDef2'):
                cd1 = t.ClassDef1.classDefs
                cd2 = t.ClassDef2.classDefs
                mat = getattr(t, 'Class1Record', None)
                if not mat:
                    continue
                for g1 in cov:
                    c1 = cd1.get(g1, 0)
                    if c1 >= len(mat):
                        continue
                    rec = mat[c1]
                    for g2, c2 in cd2.items():
                        if c2 >= len(rec.Class2Record):
                            continue
                        r2 = rec.Class2Record[c2]
                        if r2.Value1 and r2.Value1.XAdvance:
                            pairs[(g1, g2)] = r2.Value1.XAdvance
    m.close()
    return pairs


def main():
    mona_pairs = extract_mona_kern()
    print('Mona kern pair: %d' % len(mona_pairs), flush=True)

    os.makedirs(OUTD, exist_ok=True)

    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        fgo = set(f.getGlyphOrder())

        # 映射：只保留双方都有的字形
        mapped = {}
        for (g1, g2), v in mona_pairs.items():
            if g1 in fgo and g2 in fgo:
                mapped[(g1, g2)] = v
        print('  %s: 可映射 %d/%d' % (tag, len(mapped), len(mona_pairs)), flush=True)
        if not mapped:
            f.close(); continue

        # 构建新 lookup
        gpos = f['GPOS'].table
        # buildPairPosGlyphs 需要 { (g1,g2): (ValueRecord, ValueRecord) }
        # 返回值是 subtables list，需包进一个 lookup
        pairs_dict = {}
        for (g1, g2), v in mapped.items():
            pairs_dict[(g1, g2)] = (buildValue({'XAdvance': int(round(v * KERN_SCALE))}), None)
        glyphMap = f.getReverseGlyphMap()
        subtables = buildPairPosGlyphs(pairs_dict, glyphMap)

        from fontTools.ttLib.tables import otTables as ot
        new_lookup = ot.Lookup()
        new_lookup.LookupType = 2
        new_lookup.LookupFlag = 0
        new_lookup.SubTable = subtables
        new_lookup.SubTableCount = len(subtables)
        gpos.LookupList.Lookup.append(new_lookup)
        new_idx = len(gpos.LookupList.Lookup) - 1
        gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup)

        # 追加到所有 kern feature（各 script 各一份）
        n_feat = 0
        for fr in gpos.FeatureList.FeatureRecord:
            if fr.FeatureTag == 'kern':
                if new_idx not in fr.Feature.LookupListIndex:
                    fr.Feature.LookupListIndex.append(new_idx)
                    fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
                    n_feat += 1
        print('  %s: 追加到 %d 个 kern feature, lookup#%d' % (tag, n_feat, new_idx), flush=True)

        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()
        print('  %s: saved' % tag, flush=True)


if __name__ == "__main__":
    main()
