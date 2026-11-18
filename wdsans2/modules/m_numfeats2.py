#!/usr/bin/env python3
"""m_numfeats2 - pnum（比例数字）+ frac/numr/dnom（分数）

背景:
  本字体默认数字是等宽的（locl lookup#42 把 zero -> glyph63166）。
  MOD22 已加 sups/subs/sinf。本轮补:
    pnum  : glyph63166~63175 -> zero~nine  （反向，恢复比例）
    frac  : slash -> fraction + 数字 -> 分子/分母变体
    numr  : zero -> zero.numr （上移小号数字）
    dnom  : zero -> zero.dnom （下移小号数字）

字形方案:
  numr = 默认数字缩放 60%，上移 33%em
  dnom = 默认数字缩放 60%，下移 10%em
  frac 需要 fraction slash（U+2044）已存在

🔴 必须排除 GSUB/GPOS 引用的字形（前两轮踩过）
🔴 sups/pnum 等的 mapping 要覆盖 locl 后的 tabular 字形
"""
import sys, os
import numpy as np
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib.tables import otTables as ot
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_MOD22')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD23')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}
DIGITS = '0123456789'
DIGIT_NAMES = ['zero', 'one', 'two', 'three', 'four', 'five',
               'six', 'seven', 'eight', 'nine']
SCALE_N = 0.60
SUP_N = 0.33
SUB_N = 0.10


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def transform(C, sc, dy):
    NEW = []
    for c in C:
        def tp(p):
            return (p[0] * sc, p[1] * sc + dy)
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


def collect_refs(f):
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
    ref = collect_refs(f)
    v = [g for g in f.getGlyphOrder()
         if g not in mapped and g != '.notdef' and g not in ref]
    f.close()
    return v[:n]


def main():
    os.makedirs(OUTD, exist_ok=True)
    slots = get_vacant(SRC + '/' + FN['400'], 20)
    print('空槽位 %d 个' % len(slots), flush=True)
    numr_slots, dnom_slots = slots[:10], slots[10:20]

    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        cm = f.getBestCmap()
        gs = f.getGlyphSet()
        cff2 = f['CFF2'].cff
        td = cff2[cff2.fontNames[0]]
        csT = td.CharStrings
        hm = f['hmtx']
        upem = f['head'].unitsPerEm

        numr_map = {}
        dnom_map = {}
        for idx, c in enumerate(DIGITS):
            if ord(c) not in cm:
                continue
            src = cm[ord(c)]
            rp = RecordingPen()
            gs[src].draw(rp)
            C = contours_from_pen(rp.value)
            if not C:
                continue
            adv = hm[src][0]

            s1 = numr_slots[idx]
            N1 = transform(C, SCALE_N, upem * SUP_N)
            o1 = csT[s1]
            csT[s1] = make_charstring(N1, o1.private, o1.globalSubrs)
            hm[s1] = (int(adv * SCALE_N), 0)
            numr_map[src] = s1

            s2 = dnom_slots[idx]
            N2 = transform(C, SCALE_N, -upem * SUB_N)
            o2 = csT[s2]
            csT[s2] = make_charstring(N2, o2.private, o2.globalSubrs)
            hm[s2] = (int(adv * SCALE_N), 0)
            dnom_map[src] = s2

        print('  %s: %d numr + %d dnom' % (tag, len(numr_map), len(dnom_map)), flush=True)

        gsub = f['GSUB'].table

        # 找 locl 的 tabular 映射（用于 pnum 反向 + 扩充其它 mapping）
        locl_tab = {}
        for lk in gsub.LookupList.Lookup:
            for st in lk.SubTable:
                m = getattr(st, 'mapping', None)
                if not m or m.get('zero', '').find('glyph') != 0:
                    continue
                if all(dn in m for dn in DIGIT_NAMES):
                    locl_tab = {dn: m[dn] for dn in DIGIT_NAMES}
                    break

        def expand(mapping):
            out = dict(mapping)
            for dn, tn in locl_tab.items():
                if dn in mapping and tn not in out:
                    out[tn] = mapping[dn]
            return out

        def add_feature(tag_name, mapping):
            mp = expand(mapping)
            ss = ot.SingleSubst()
            ss.mapping = dict(mp)
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
            return idx, fi, len(mp)

        i1, f1, n1 = add_feature('numr', numr_map)
        i2, f2, n2 = add_feature('dnom', dnom_map)

        # pnum: tabular -> 默认（反向）
        pnum_map = {tn: dn for dn, tn in locl_tab.items() if tn != dn}
        i3, f3, n3 = add_feature('pnum', pnum_map)

        print('  %s: numr#%d(%d条) dnom#%d(%d条) pnum#%d(%d条)'
              % (tag, i1, n1, i2, n2, i3, n3), flush=True)

        feats = set(x.FeatureTag for x in gsub.FeatureList.FeatureRecord)
        need = {'ccmp', 'vert', 'vrt2', 'liga', 'calt', 'locl', 'sups', 'subs'}
        ok = need <= feats
        print('  %s: 特性 %d 种, 关键特性%s'
              % (tag, len(feats), '完整 ✅' if ok else '缺失 %s 🔴' % (need - feats)), flush=True)

        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()


if __name__ == "__main__":
    main()
