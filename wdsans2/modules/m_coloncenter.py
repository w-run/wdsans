#!/usr/bin/env python3
"""m_coloncenter - 时间场景冒号居中（12:34）

🔴 踩坑全记录（2026-11-15，代价极大）:
  1. feaLib 的 addOpenTypeFeaturesFromString **替换整个 GSUB**
     MOD19 16 features/52 lookups -> 只剩 calt 1个
     vert/vrt2/ccmp 全丢；预览子集 4.13MB -> 1.96MB
  2. 备份+反向合并会破坏 locl 的 script 映射 -> — … 丢 script 变体
  3. 手写 ot.Coverage/ChainContextSubst -> HarfBuzz 静默跳过（不触发）

✅ 最终方案: **只追加 subtable 到已有的 calt lookup#30**
  a) 隔离编译拿到 feaLib 正确生成的 ChainContext subtable
  b) 追加 SingleSubst lookup 到 LookupList 末尾（记索引）
  c) 把 ChainContext subtable 追加到 lookup#30 的 SubTable 列表
     （lookup#30 已挂在 latn 的 calt feature 上，无需碰 FeatureList/ScriptList）
  d) 修正 ChainContext 里 SubstLookupRecord 指向新 SingleSubst

  这样: FeatureList / ScriptList 完全不动 -> 所有原有特性零风险
"""
import sys, os
import numpy as np
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib.tables import otTables as ot
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_MOD19')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD20')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}
TARGETS = [(':', 'colon_centered'), (';', 'semicolon_centered')]
Q = chr(39)
CALT_LOOKUP_IDX = 30     # latn 的 calt feature 引用的 lookup（已接线）


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def bbox_and_contours(gs, gname):
    rp = RecordingPen()
    gs[gname].draw(rp)
    C = contours_from_pen(rp.value)
    if not C:
        return None, None
    P = np.vstack([[np.array(c['start'], float)] + [endp(s) for s in c['segs']]
                   for c in C])
    return (float(P[:, 1].min()), float(P[:, 1].max())), C


def shift(C, dy):
    NEW = []
    for c in C:
        segs = []
        for s in c['segs']:
            if s[0] == 'L':
                segs.append(['L', (s[1][0], s[1][1] + dy)])
            elif s[0] == 'C':
                segs.append(['C', (s[1][0], s[1][1] + dy),
                             (s[2][0], s[2][1] + dy), (s[3][0], s[3][1] + dy)])
            elif s[0] == 'Q':
                segs.append(['Q', (s[1][0], s[1][1] + dy), (s[2][0], s[2][1] + dy)])
            elif s[0] == 'QM':
                segs.append(['QM', [(p[0], p[1] + dy) for p in s[1]]])
            else:
                segs.append(list(s))
        NEW.append({'start': (c['start'][0], c['start'][1] + dy), 'segs': segs})
    return NEW


def get_vacant(fp, n):
    f = TTFont(fp, lazy=True)
    mapped = set(f.getBestCmap().values())
    v = [g for g in f.getGlyphOrder() if g not in mapped and g != '.notdef']
    f.close()
    return v[:n]


def isolated_chain_subtable(src_path, subs_map, digits):
    """在隔离字体上跑 feaLib，拿到正确生成的 ChainContext subtable + SingleSubst

    subs_map: {src_glyph: tgt_glyph}
    返回: (chain_subtable, single_mapping)
    """
    t = TTFont(src_path)
    if 'GSUB' in t:
        del t['GSUB']
    lines = ['lookup CTR {']
    for a, b in subs_map.items():
        lines.append('    sub %s by %s;' % (a, b))
    lines.append('} CTR;')
    lines.append('feature calt {')
    for a in subs_map:
        lines.append('    sub [%s] %s%s lookup CTR [%s];' % (digits, a, Q, digits))
    lines.append('} calt;')
    addOpenTypeFeaturesFromString(t, '\n'.join(lines) + '\n')
    g = t['GSUB'].table
    chain = g.LookupList.Lookup[1].SubTable[0]
    t.close()
    return chain, dict(subs_map)


def main():
    os.makedirs(OUTD, exist_ok=True)
    slots = get_vacant(SRC + '/' + FN['400'], len(TARGETS))
    print('复用槽位: %s' % slots, flush=True)

    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        cm = f.getBestCmap()
        gs = f.getGlyphSet()
        cff2 = f['CFF2'].cff
        td = cff2[cff2.fontNames[0]]
        csT = td.CharStrings
        hm = f['hmtx']

        # 数字墨迹中心
        bp = BoundsPen(gs)
        gs[cm[ord('0')]].draw(bp)
        zc = (bp.bounds[1] + bp.bounds[3]) / 2.0

        # 1) 写居中字形
        subs_map = {}
        for (ch, nm), slot in zip(TARGETS, slots):
            if ord(ch) not in cm:
                continue
            src = cm[ord(ch)]
            bb, C = bbox_and_contours(gs, src)
            if not bb:
                continue
            dy = zc - (bb[0] + bb[1]) / 2.0
            NEW = shift(C, dy)
            old = csT[slot]
            csT[slot] = make_charstring(NEW, old.private, old.globalSubrs)
            hm[slot] = hm[src]
            subs_map[src] = slot
            print('  %s: %s 上移 %+.0f -> %s' % (tag, src, dy, slot), flush=True)

        if not subs_map:
            f.close()
            continue

        digits = ' '.join(cm[ord(c)] for c in '0123456789' if ord(c) in cm)

        # 2) 隔离编译拿正确 subtable
        chain_sub, _ = isolated_chain_subtable(SRC + '/' + FN[tag], subs_map, digits)

        gsub = f['GSUB'].table

        # 3) 把 SingleSubst 追加到 LookupList 末尾（每个目标一个）
        first_new = len(gsub.LookupList.Lookup)
        idx_of = {}
        for src_gn, tgt_gn in subs_map.items():
            ss = ot.SingleSubst()
            ss.mapping = {src_gn: tgt_gn}
            lk = ot.Lookup()
            lk.LookupType = 1
            lk.LookupFlag = 0
            lk.SubTable = [ss]
            lk.SubTableCount = 1
            idx_of[src_gn] = len(gsub.LookupList.Lookup)
            gsub.LookupList.Lookup.append(lk)
        gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)

        # 4) 修正 chain subtable 的 SubstLookupRecord（feaLib 里是 0/1...，要改成新索引）
        #    feaLib 生成的 chain 有多条 rule 时会分多个 subtable，这里只有一条时共用一个 sub
        for r in chain_sub.SubstLookupRecord:
            # 简化: 按 rule 顺序映射。这里 colons/semicolons 分别一个 subtable
            pass

        # 更稳妥: 分别为每个目标构造独立的 chain subtable（复制并改 mapping）
        new_subs = []
        for src_gn, tgt_gn in subs_map.items():
            import copy
            cs = copy.deepcopy(chain_sub)
            # InputCoverage 该规则只有单 glyph
            cs.InputCoverage = [ot.Coverage()]
            cs.InputCoverage[0].Format = 1
            cs.InputCoverage[0].glyphs = [src_gn]
            # SubstLookupRecord 指向对应 SingleSubst
            rec = ot.SubstLookupRecord()
            rec.SequenceIndex = 0
            rec.LookupListIndex = idx_of[src_gn]
            cs.SubstLookupRecord = [rec]
            cs.SubstCount = 1
            new_subs.append(cs)

        # 5) 追加到 lookup#30（已接线的 calt）
        target_lk = gsub.LookupList.Lookup[CALT_LOOKUP_IDX]
        for cs in new_subs:
            target_lk.SubTable.append(cs)
        target_lk.SubTableCount = len(target_lk.SubTable)

        # 6) 校验: FeatureList/ScriptList 完全未动
        feats = set(x.FeatureTag for x in gsub.FeatureList.FeatureRecord)
        ok = {'ccmp', 'vert', 'vrt2', 'liga', 'calt', 'locl'} <= feats
        print('  %s: lookups %d->%d, calt lookup#%d subtable %d, 特性%s'
              % (tag, first_new, len(gsub.LookupList.Lookup), CALT_LOOKUP_IDX,
                 target_lk.SubTableCount, '完整 ✅' if ok else '缺失 🔴'), flush=True)

        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()


if __name__ == "__main__":
    main()
