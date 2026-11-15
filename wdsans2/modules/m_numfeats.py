#!/usr/bin/env python3
"""m_numfeats - 数字排版特性 + 上标/下标字符

发现的缺陷（对比 OPPO/HOS）:
  参考字体都有 8 个数字特性，我们一个都没有:
    tnum pnum frac subs sups sinf numr dnom
  且上标数字缺 7 个（⁰⁵⁶⁷⁸⁹），下标数字全缺 10 个（₀-₉）

方案:
  1. 上下标字符: 缩放默认数字生成（75% 比例，上/下移位）
     -> 同时补齐 cmap 映射（U+2070..U+2079 / U+2080..U+2089）
  2. sups/subs/sinf: SingleSubst 到这些新字形
  3. tnum: 本字体默认已等宽（locl 实现），无需另做
  4. pnum: 反查 locl 的比例数字，做成 pnum 特性

🔴 槽位分配必须排除 GSUB/GPOS 引用的字形（前一轮踩过坑）
"""
import sys, os
import numpy as np
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib.tables import otTables as ot
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_MOD20')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD22')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}
DIGITS = '0123456789'
SUP_CPS = [0x2070, 0x00B9, 0x00B2, 0x00B3, 0x2074, 0x2075, 0x2076, 0x2077, 0x2078, 0x2079]
SUB_CPS = list(range(0x2080, 0x208A))
SCALE = 0.62          # 上下标相对字号
SUP_SHIFT = 0.34      # 上标上移（em 比例）
DIGIT_NAMES = ['zero','one','two','three','four','five','six','seven','eight','nine']
SUB_SHIFT = 0.16      # 下标下移


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def transform(C, sx, sy, dx, dy):
    """缩放 + 平移轮廓"""
    NEW = []
    for c in C:
        def tp(p):
            return (p[0] * sx + dx, p[1] * sy + dy)
        segs = []
        for s in c['segs']:
            if s[0] == 'L':
                segs.append(['L', tp(s[1])])
            elif s[0] == 'C':
                segs.append(['C', tp(s[1]), tp(s[2]), tp(s[3])])
            elif s[0] == 'Q':
                segs.append(['Q', tp(s[1]), tp(s[2])])
            elif s[0] == 'QM':
                segs.append(['QM', [tp(p) for p in s[1]]])
            else:
                segs.append(list(s))
        NEW.append({'start': tp(c['start']), 'segs': segs})
    return NEW


def collect_gsub_referenced(f):
    used = set()
    for tag in ('GSUB', 'GPOS'):
        if tag not in f:
            continue
        try:
            tbl = f[tag].table
        except Exception:
            continue
        if not hasattr(tbl, 'LookupList') or not tbl.LookupList:
            continue
        for lk in tbl.LookupList.Lookup:
            for st in lk.SubTable:
                t = st.ExtSubTable if hasattr(st, 'ExtSubTable') else st
                for attr in ('Coverage', 'MarkCoverage', 'BaseCoverage',
                             'Mark1Coverage', 'Mark2Coverage', 'LigatureCoverage',
                             'InputCoverage', 'BacktrackCoverage', 'LookAheadCoverage'):
                    covs = getattr(t, attr, None)
                    if covs is None:
                        continue
                    if not isinstance(covs, (list, tuple)):
                        covs = [covs]
                    for c in covs:
                        if c is not None and hasattr(c, 'glyphs'):
                            used.update(c.glyphs)
                m = getattr(t, 'mapping', None)
                if m:
                    for k, v in m.items():
                        used.add(k)
                        if isinstance(v, str):
                            used.add(v)
                for attr in ('ClassDef', 'ClassDef1', 'ClassDef2'):
                    cd = getattr(t, attr, None)
                    if cd is not None and hasattr(cd, 'classDefs'):
                        used.update(cd.classDefs.keys())
    return used


def get_vacant(fp, n):
    f = TTFont(fp)
    mapped = set(f.getBestCmap().values())
    ref = collect_gsub_referenced(f)
    v = [g for g in f.getGlyphOrder()
         if g not in mapped and g != '.notdef' and g not in ref]
    f.close()
    return v[:n]


def main():
    os.makedirs(OUTD, exist_ok=True)
    need = 20     # 10 上标 + 10 下标
    slots = get_vacant(SRC + '/' + FN['400'], need)
    print('空槽位 %d 个: %s...' % (len(slots), slots[:4]), flush=True)
    sup_slots, sub_slots = slots[:10], slots[10:20]

    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        cm = f.getBestCmap()
        gs = f.getGlyphSet()
        cff2 = f['CFF2'].cff
        td = cff2[cff2.fontNames[0]]
        csT = td.CharStrings
        hm = f['hmtx']

        upem = f['head'].unitsPerEm
        sup_map = {}
        sub_map = {}

        for idx, c in enumerate(DIGITS):
            if ord(c) not in cm:
                continue
            src = cm[ord(c)]
            rp = RecordingPen()
            gs[src].draw(rp)
            C = contours_from_pen(rp.value)
            if not C:
                continue
            P = np.vstack([[np.array(c2['start'], float)] +
                           [endp(s) for s in c2['segs']] for c2 in C])
            x0, x1 = float(P[:, 0].min()), float(P[:, 0].max())
            cx = (x0 + x1) / 2.0
            adv = hm[src][0]

            # 上标
            slot_s = sup_slots[idx]
            dx = cx - cx * SCALE       # 保持中心
            dy = upem * SUP_SHIFT
            NEW = transform(C, SCALE, SCALE, dx, dy)
            old = csT[slot_s]
            csT[slot_s] = make_charstring(NEW, old.private, old.globalSubrs)
            hm[slot_s] = (int(adv * SCALE), 0)
            sup_map[src] = slot_s

            # 下标
            slot_b = sub_slots[idx]
            dy2 = -upem * SUB_SHIFT
            NEW2 = transform(C, SCALE, SCALE, dx, dy2)
            old2 = csT[slot_b]
            csT[slot_b] = make_charstring(NEW2, old2.private, old2.globalSubrs)
            hm[slot_b] = (int(adv * SCALE), 0)
            sub_map[src] = slot_b

        print('  %s: 生成 %d 上标 + %d 下标'
              % (tag, len(sup_map), len(sub_map)), flush=True)

        gsub = f['GSUB'].table

        # 🔴 关键: locl 会先把 zero 换成 glyph6316x（等宽版）
        # 所以 sups/subs/sinf 的 mapping 要同时覆盖两套 input
        locl_tabular = {}   # zero -> glyph63166
        for lk in gsub.LookupList.Lookup:
            for st in lk.SubTable:
                m = getattr(st, 'mapping', None)
                if not m or 'zero' not in m:
                    continue
                tgt = m['zero']
                # locl 的目标是 gid 6xxxx 段的（等宽字形）
                if tgt.startswith('glyph'):
                    locl_tabular = {k: v for k, v in m.items() if k in DIGIT_NAMES}
                    break

        def expand(mapping):
            """把 mapping 扩充为同时覆盖默认数字和 locl 等宽数字"""
            out = dict(mapping)
            for dflt_nm, tab_nm in locl_tabular.items():
                if dflt_nm in mapping and tab_nm not in out:
                    out[tab_nm] = mapping[dflt_nm]
            return out

        def add_feature(tag_name, mapping):
            mapping = expand(mapping)
            ss = ot.SingleSubst()
            ss.mapping = dict(mapping)
            lk = ot.Lookup()
            lk.LookupType = 1
            lk.LookupFlag = 0
            lk.SubTable = [ss]
            lk.SubTableCount = 1
            idx = len(gsub.LookupList.Lookup)
            gsub.LookupList.Lookup.append(lk)
            gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)

            fr = ot.FeatureRecord()
            fr.FeatureTag = tag_name
            fr.Feature = ot.Feature()
            fr.Feature.FeatureParams = None
            fr.Feature.LookupListIndex = [idx]
            fr.Feature.LookupCount = 1
            gsub.FeatureList.FeatureRecord.append(fr)
            gsub.FeatureList.FeatureCount = len(gsub.FeatureList.FeatureRecord)
            fi = len(gsub.FeatureList.FeatureRecord) - 1

            for sr in gsub.ScriptList.ScriptRecord:
                if sr.Script.DefaultLangSys:
                    sr.Script.DefaultLangSys.FeatureIndex.append(fi)
                    sr.Script.DefaultLangSys.FeatureCount = len(sr.Script.DefaultLangSys.FeatureIndex)
            return idx, fi

        i1, f1 = add_feature('sups', sup_map)
        i2, f2 = add_feature('subs', sub_map)
        i3, f3 = add_feature('sinf', dict(sub_map))   # sinf 与 subs 同映射

        print('  %s: sups#%d subs#%d sinf#%d' % (tag, i1, i2, i3), flush=True)

        # 补 cmap 映射（上标/下标字符）
        for idx, cp in enumerate(SUP_CPS):
            if cp in cm or idx >= len(sup_slots):
                continue
            for t in f['cmap'].tables:
                if t.isUnicode():
                    t.cmap[cp] = sup_slots[idx]
        for idx, cp in enumerate(SUB_CPS):
            if cp in cm or idx >= len(sub_slots):
                continue
            for t in f['cmap'].tables:
                if t.isUnicode():
                    t.cmap[cp] = sub_slots[idx]

        feats = set(x.FeatureTag for x in gsub.FeatureList.FeatureRecord)
        need_f = {'ccmp', 'vert', 'vrt2', 'liga', 'calt', 'locl'}
        ok = need_f <= feats
        print('  %s: 特性 %d 种, 原特性%s'
              % (tag, len(feats), '完整 ✅' if ok else '缺失 🔴'), flush=True)

        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()


main()
