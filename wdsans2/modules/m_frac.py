#!/usr/bin/env python3
"""m_frac - 分数特性（frac），补齐第 7 个数字特性

机制（参考 OPPO 结构，但自己实现）:
  输入 "1/2" 渲染为真正的分数（分子/分母/分数线）
  1) slash -> fraction (U+2044 分数线，已存在)
  2) zero~nine -> *.numr (MOD23 已建 numr 字形)
  3) ChainContext: fraction 后的 numr -> dnom (MOD23 已建 dnom 字形)

我们已有 numr/dnom 字形（MOD23）与 U+2044，只需补 GSUB 结构。

🔴 关键: 不碰 FeatureList/ScriptList 已有内容，只 append
🔴 ChainContext 用 feaLib 隔离编译（手写 Coverage 会被 HarfBuzz 跳过）
"""
import sys, os, copy
import numpy as np
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib.tables import otTables as ot

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_MOD23')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD24')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}
DIGITS = '0123456789'
DIGIT_NAMES = ['zero','one','two','three','four','five','six','seven','eight','nine']
Q = chr(39)


def find_numr_dnom_maps(gsub):
    """从 MOD23 已建的 numr/dnom 特性里取出映射"""
    numr, dnom = {}, {}
    for fr in gsub.FeatureList.FeatureRecord:
        tag = fr.FeatureTag
        if tag not in ('numr', 'dnom'):
            continue
        for li in fr.Feature.LookupListIndex:
            lk = gsub.LookupList.Lookup[li]
            for st in lk.SubTable:
                t = st.ExtSubTable if hasattr(st, 'ExtSubTable') else st
                m = getattr(t, 'mapping', None)
                if not m:
                    continue
                if tag == 'numr':
                    numr.update(m)
                else:
                    dnom.update(m)
    return numr, dnom


def isolated_chain(src_path, chain_fea):
    """隔离编译，返回 chain subtable（feaLib 生成，HarfBuzz 才能识别）"""
    t = TTFont(src_path)
    if 'GSUB' in t:
        del t['GSUB']
    addOpenTypeFeaturesFromString(t, chain_fea)
    g = t['GSUB'].table
    # 找 ChainContext lookup
    for lk in g.LookupList.Lookup:
        if lk.LookupType == 6:
            st = lk.SubTable[0]
            t.close()
            return st
    t.close()
    return None


def main():
    os.makedirs(OUTD, exist_ok=True)

    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        cm = f.getBestCmap()
        gsub = f['GSUB'].table

        numr_map, dnom_map = find_numr_dnom_maps(gsub)
        # 只保留 tabular 与默认两套（numr/dnom 特性里已是完整映射）
        if not numr_map or not dnom_map:
            print('  %s: 缺 numr/dnom，跳过' % tag, flush=True)
            f.close()
            continue

        # 需要 numr 的默认数字名（用于 frac 的 step2）
        numr_default = {k: v for k, v in numr_map.items() if not k.startswith('glyph')}
        if len(numr_default) < 10:
            numr_default = {cm[ord(c)]: v for c, v in zip(DIGITS, numr_map.values())
                            if ord(c) in cm}
        print('  %s: numr %d 条, dnom %d 条' % (tag, len(numr_map), len(dnom_map)), flush=True)

        # 🔴 locl 会先把 zero~nine 换成 glyph6316x，所以 numr 映射要覆盖两套 input
        locl_tab = {}
        for lk_scan in gsub.LookupList.Lookup:
            for st_scan in lk_scan.SubTable:
                m_scan = getattr(st_scan, 'mapping', None)
                if not m_scan:
                    continue
                if m_scan.get('zero', '').startswith('glyph') and len(m_scan) == 11:
                    locl_tab = {k: v for k, v in m_scan.items() if k in DIGIT_NAMES}
                    break
            if locl_tab:
                break

        numr_map_full = dict(numr_default)
        for dn, tn in locl_tab.items():
            if dn in numr_default:
                numr_map_full[tn] = numr_default[dn]

        # 构造 FEA（只用于隔离编译出 ChainContext）
        numr_names = list(dict.fromkeys(numr_map_full.values()))
        dnom_names = list(dict.fromkeys(dnom_map.values()))
        numr_cls = ' '.join(numr_names)
        dnom_cls = ' '.join(dnom_names)

        # 取一个占位数字名（feaLib 需要具体 glyph 名）
        sample_numr = numr_names[0]
        fea = (
            'lookup FRACDNOM {\n'
            '    sub %s by %s;\n'
            '} FRACDNOM;\n'
            'feature frac {\n'
            '    sub [fraction] %s%s lookup FRACDNOM;\n'
            '    sub [%s] %s%s lookup FRACDNOM;\n'
            '} frac;\n'
            % (sample_numr, dnom_names[0], sample_numr, Q, dnom_cls, sample_numr, Q)
        )

        chain_sub = isolated_chain(SRC + '/' + FN[tag], fea)
        if chain_sub is None:
            print('  %s: 隔离编译失败' % tag, flush=True)
            f.close()
            continue
        print('  %s: 拿到 ChainContext subtable' % tag, flush=True)

        # 1) 追加 SingleSubst: slash -> fraction（若已有则跳过）
        slash_gn = cm.get(0x002F)
        frac_gn = cm.get(0x2044)
        idx_slash = None
        if slash_gn and frac_gn and slash_gn != frac_gn:
            ss = ot.SingleSubst()
            ss.mapping = {slash_gn: frac_gn}
            lk = ot.Lookup()
            lk.LookupType = 1
            lk.LookupFlag = 0
            lk.SubTable = [ss]
            lk.SubTableCount = 1
            idx_slash = len(gsub.LookupList.Lookup)
            gsub.LookupList.Lookup.append(lk)
            gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)

        # 2) 追加 SingleSubst: zero~nine / glyph6316x -> *.numr
        ss2 = ot.SingleSubst()
        ss2.mapping = dict(numr_map_full)
        lk2 = ot.Lookup()
        lk2.LookupType = 1
        lk2.LookupFlag = 0
        lk2.SubTable = [ss2]
        lk2.SubTableCount = 1
        idx_numr = len(gsub.LookupList.Lookup)
        gsub.LookupList.Lookup.append(lk2)
        gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)

        # 3) 追加 SingleSubst: numr -> dnom（供 ChainContext 引用）
        ss3 = ot.SingleSubst()
        ss3.mapping = {nu: dn for nu, dn in zip(numr_names, dnom_names)}
        lk3 = ot.Lookup()
        lk3.LookupType = 1
        lk3.LookupFlag = 0
        lk3.SubTable = [ss3]
        lk3.SubTableCount = 1
        idx_dnom = len(gsub.LookupList.Lookup)
        gsub.LookupList.Lookup.append(lk3)
        gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)

        # 4) 修正 ChainContext 的 SubstLookupRecord 指向 idx_dnom
        for st in ([chain_sub] if not isinstance(chain_sub, list) else chain_sub):
            if hasattr(st, 'SubstLookupRecord') and st.SubstLookupRecord:
                for r in st.SubstLookupRecord:
                    r.LookupListIndex = idx_dnom

        # 5) 追加 ChainContext lookup
        lk4 = ot.Lookup()
        lk4.LookupType = 6
        lk4.LookupFlag = 0
        lk4.SubTable = [chain_sub] if not isinstance(chain_sub, list) else chain_sub
        lk4.SubTableCount = len(lk4.SubTable)
        idx_chain = len(gsub.LookupList.Lookup)
        gsub.LookupList.Lookup.append(lk4)
        gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)

        # 6) 新建 frac feature，挂到所有 script
        lookups = [i for i in (idx_slash, idx_numr, idx_chain) if i is not None]
        fr = ot.FeatureRecord()
        fr.FeatureTag = 'frac'
        fr.Feature = ot.Feature()
        fr.Feature.FeatureParams = None
        fr.Feature.LookupListIndex = lookups
        fr.Feature.LookupCount = len(lookups)
        gsub.FeatureList.FeatureRecord.append(fr)
        gsub.FeatureList.FeatureCount = len(gsub.FeatureList.FeatureRecord)
        new_fi = len(gsub.FeatureList.FeatureRecord) - 1

        for sr in gsub.ScriptList.ScriptRecord:
            if sr.Script.DefaultLangSys:
                sr.Script.DefaultLangSys.FeatureIndex.append(new_fi)
                sr.Script.DefaultLangSys.FeatureCount = len(sr.Script.DefaultLangSys.FeatureIndex)

        feats = set(x.FeatureTag for x in gsub.FeatureList.FeatureRecord)
        need = {'ccmp', 'vert', 'vrt2', 'liga', 'calt', 'locl',
                'sups', 'subs', 'pnum', 'numr', 'dnom'}
        ok = need <= feats
        print('  %s: frac feature#%d (lookups %s), 特性 %d 种, 关键%s'
              % (tag, new_fi, lookups, len(feats),
                 '完整 ✅' if ok else '缺失 %s 🔴' % (need - feats)), flush=True)

        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()


if __name__ == "__main__":
    main()
