#!/usr/bin/env python3
"""m_markpos - 重建完整的 mark + mkmk 定位表

问题:
  我们 VF 的 mark feature 只覆盖 6 个组合符号（共 22 个），
  mkmk 完全缺失。导致 a+acute+tilde 横向并排而非垂直叠加。

  实测（80px）:
    组合                 我们     Mona
    a+acute+tilde       宽69     宽34    <- 横排了
    o+diaeresis+macron  宽55     宽37    <- 横排了

方案: 自己生成定位表（不依赖 Mona，因为 Mona 的 mkmk 只覆盖 23+2 个符号）
  1. 测量每个组合符号的锚点（底部中心 = 附着点）
  2. 测量每个基字母的锚点（顶部中心 = 承重点）
  3. 生成 MarkBasePos (mark) 和 MarkMarkPos (mkmk)

锚点规则:
  - 组合符号: 底部包围盒中心 (x_mid, y_min)
  - 基字母:   顶部包围盒中心 (x_mid, y_max)
  - 上层符号: 底部中心作为 Mark2 的承重点
"""
import sys, os
import numpy as np
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib.tables import otTables as ot
from canonpen3 import contours_from_pen

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_MOD15')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD16')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}

COMB_RANGE = (0x0300, 0x036F)
# 拉丁基字母范围（需要承重锚点）
BASE_RANGES = [(0x0020, 0x007E), (0x00A0, 0x024F), (0x1E00, 0x1EFF)]


def glyph_bbox(gs, gname):
    rp = RecordingPen()
    try:
        gs[gname].draw(rp)
    except Exception:
        return None
    if not rp.value:
        return None
    C = contours_from_pen(rp.value)
    if not C:
        return None
    pts = []
    for c in C:
        pts.append(np.array(c['start'], float))
        for s in c['segs']:
            if s[0] == 'QM':
                pts.extend([np.array(p, float) for p in s[1]])
            else:
                pts.extend([np.array(a, float) for a in s[1:] if isinstance(a, tuple)])
    if not pts:
        return None
    P = np.vstack(pts)
    return (float(P[:, 0].min()), float(P[:, 0].max()),
            float(P[:, 1].min()), float(P[:, 1].max()))


def build_tables(f):
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()

    # 1) 组合符号的锚点（底部中心）
    marks = {}
    for cp in range(COMB_RANGE[0], COMB_RANGE[1] + 1):
        if cp not in cmap:
            continue
        gn = cmap[cp]
        bb = glyph_bbox(gs, gn)
        if not bb:
            continue
        x0, x1, y0, y1 = bb
        marks[gn] = ((x0 + x1) / 2.0, y0)

    # 2) 基字母的锚点（顶部中心）
    bases = {}
    for lo, hi in BASE_RANGES:
        for cp in range(lo, hi + 1):
            if cp not in cmap:
                continue
            gn = cmap[cp]
            if gn in marks:
                continue
            bb = glyph_bbox(gs, gn)
            if not bb:
                continue
            x0, x1, y0, y1 = bb
            bases[gn] = ((x0 + x1) / 2.0, y1)

    return marks, bases


def make_markbase(marks, bases, gidmap):
    """构造 MarkBasePos subtable（Coverage 必须按 glyph id 排序）"""
    mk = sorted(marks.keys(), key=lambda g: gidmap.get(g, 999999))
    bs = sorted(bases.keys(), key=lambda g: gidmap.get(g, 999999))
    if not mk or not bs:
        return None

    st = ot.MarkBasePos()
    st.Format = 1

    cov_m = ot.Coverage(); cov_m.glyphs = mk
    st.MarkCoverage = cov_m
    cov_b = ot.Coverage(); cov_b.glyphs = bs
    st.BaseCoverage = cov_b

    st.ClassCount = 1
    mc = ot.MarkArray(); mc.MarkCount = len(mk); mc.MarkRecord = []
    for g in mk:
        rec = ot.MarkRecord()
        rec.Class = 0
        anc = ot.Anchor(); anc.Format = 1
        anc.XCoordinate = int(round(marks[g][0])); anc.YCoordinate = int(round(marks[g][1]))
        rec.MarkAnchor = anc
        mc.MarkRecord.append(rec)
    st.MarkArray = mc

    ba = ot.BaseArray(); ba.BaseCount = len(bs); ba.BaseRecord = []
    for g in bs:
        rec = ot.BaseRecord()
        anc = ot.Anchor(); anc.Format = 1
        anc.XCoordinate = int(round(bases[g][0])); anc.YCoordinate = int(round(bases[g][1]))
        rec.BaseAnchor = [anc]
        ba.BaseRecord.append(rec)
    st.BaseArray = ba
    return st


def make_markmark(marks, gidmap):
    """构造 MarkMarkPos subtable（Coverage 必须按 glyph id 排序）"""
    mk = sorted(marks.keys(), key=lambda g: gidmap.get(g, 999999))
    if len(mk) < 2:
        return None

    st = ot.MarkMarkPos()
    st.Format = 1

    cov1 = ot.Coverage(); cov1.glyphs = mk
    st.Mark1Coverage = cov1
    cov2 = ot.Coverage(); cov2.glyphs = mk
    st.Mark2Coverage = cov2
    st.ClassCount = 1

    m1 = ot.MarkArray(); m1.MarkCount = len(mk); m1.MarkRecord = []
    for g in mk:
        rec = ot.MarkRecord(); rec.Class = 0
        anc = ot.Anchor(); anc.Format = 1
        anc.XCoordinate = int(round(marks[g][0])); anc.YCoordinate = int(round(marks[g][1]))
        rec.MarkAnchor = anc
        m1.MarkRecord.append(rec)
    st.Mark1Array = m1

    m2 = ot.Mark2Array(); m2.Mark2Count = len(mk); m2.Mark2Record = []
    for g in mk:
        rec = ot.Mark2Record()
        anc = ot.Anchor(); anc.Format = 1
        # 上层符号的承重点 = 其顶部中心（可继续往上叠）
        anc.XCoordinate = int(round(marks[g][0]))
        anc.YCoordinate = int(round(marks[g][1]))
        rec.Mark2Anchor = [anc]
        m2.Mark2Record.append(rec)
    st.Mark2Array = m2
    return st


def main():
    os.makedirs(OUTD, exist_ok=True)
    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        marks, bases = build_tables(f)
        print('  %s: %d 组合符号, %d 基字母' % (tag, len(marks), len(bases)), flush=True)
        if not marks or not bases:
            f.close(); continue

        gpos = f['GPOS'].table
        gidmap = f.getReverseGlyphMap()

        # 加 mark lookup
        st_mb = make_markbase(marks, bases, gidmap)
        lk_mb = ot.Lookup(); lk_mb.LookupType = 4; lk_mb.LookupFlag = 0
        lk_mb.SubTable = [st_mb]; lk_mb.SubTableCount = 1
        gpos.LookupList.Lookup.append(lk_mb)
        idx_mb = len(gpos.LookupList.Lookup) - 1
        gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup)

        # 加 mkmk lookup
        st_mm = make_markmark(marks, gidmap)
        idx_mm = None
        if st_mm:
            lk_mm = ot.Lookup(); lk_mm.LookupType = 6; lk_mm.LookupFlag = 0
            lk_mm.SubTable = [st_mm]; lk_mm.SubTableCount = 1
            gpos.LookupList.Lookup.append(lk_mm)
            idx_mm = len(gpos.LookupList.Lookup) - 1
            gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup)

        # 挂到 feature（没有则新建）
        have_mark = False; have_mkmk = False
        for fr in gpos.FeatureList.FeatureRecord:
            if fr.FeatureTag == 'mark':
                fr.Feature.LookupListIndex = [idx_mb]   # 替换（旧的覆盖不全）
                fr.Feature.LookupCount = 1
                have_mark = True
            elif fr.FeatureTag == 'mkmk' and idx_mm is not None:
                fr.Feature.LookupListIndex = [idx_mm]
                fr.Feature.LookupCount = 1
                have_mkmk = True

        if not have_mark:
            fr = ot.FeatureRecord()
            fr.FeatureTag = 'mark'
            fr.Feature = ot.Feature()
            fr.Feature.LookupListIndex = [idx_mb]
            fr.Feature.LookupCount = 1
            gpos.FeatureList.FeatureRecord.append(fr)
            gpos.FeatureList.FeatureCount = len(gpos.FeatureList.FeatureRecord)
            # 挂到所有 script
            for sr in gpos.ScriptList.ScriptRecord:
                if sr.Script.DefaultLangSys:
                    sr.Script.DefaultLangSys.FeatureIndex.append(len(gpos.FeatureList.FeatureRecord) - 1)
                    sr.Script.DefaultLangSys.FeatureCount = len(sr.Script.DefaultLangSys.FeatureIndex)
        if not have_mkmk and idx_mm is not None:
            fr = ot.FeatureRecord()
            fr.FeatureTag = 'mkmk'
            fr.Feature = ot.Feature()
            fr.Feature.LookupListIndex = [idx_mm]
            fr.Feature.LookupCount = 1
            gpos.FeatureList.FeatureRecord.append(fr)
            gpos.FeatureList.FeatureCount = len(gpos.FeatureList.FeatureRecord)
            for sr in gpos.ScriptList.ScriptRecord:
                if sr.Script.DefaultLangSys:
                    sr.Script.DefaultLangSys.FeatureIndex.append(len(gpos.FeatureList.FeatureRecord) - 1)
                    sr.Script.DefaultLangSys.FeatureCount = len(sr.Script.DefaultLangSys.FeatureIndex)

        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()
        print('  %s: mark lookup#%d, mkmk lookup#%s' % (tag, idx_mb, idx_mm), flush=True)


if __name__ == "__main__":
    main()
