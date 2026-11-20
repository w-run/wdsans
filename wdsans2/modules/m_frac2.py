#!/usr/bin/env python3
"""m_frac2 - 重建 frac 特性（修 ChainContext 只覆盖1字形）

现状 bug:
  GSUB frac lookups=[60, 61, 63]
    [60] slash -> fraction
    [61] zero~nine -> *.numr    (20 条，所有数字都变 numr)
    [63] ChainContext Format3:
           Backtrack=[fraction]
           Input=[glyph61925]   <- 只有 zero.numr 一个!
           Subst -> lookup[62] (numr->dnom)

  实测 1/2 -> [61927(one.numr), 3265(fraction), 61928(two.numr)]
  分母停在 numr 位置 y[326,772]，没变 dnom y[-104,342]

根因:
  feaLib 编译 sub [dnom_cls] sample_numr lookup 时,
  Input 只展开 sample_numr 一个字形, 不是整个类。

正解:
  手工构造 ChainContext Format3, InputCoverage 用完整 20 个 numr 字形
    Backtrack = [fraction]
    Input     = [numr_1 ... numr_20]
    Subst     = 0 -> lookup(numr->dnom)
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot



def get_numr_dnom_maps(gsub):
    numr, dnom = {}, {}
    for fr in gsub.FeatureList.FeatureRecord:
        if fr.FeatureTag not in ("numr", "dnom"):
            continue
        for li in fr.Feature.LookupListIndex:
            lk = gsub.LookupList.Lookup[li]
            if lk.LookupType != 1:
                continue
            m = getattr(lk.SubTable[0], "mapping", {})
            if len(m) <= 5:
                continue
            (numr if fr.FeatureTag == "numr" else dnom).update(m)
    return numr, dnom


def find_frac_feature(gsub):
    for i, fr in enumerate(gsub.FeatureList.FeatureRecord):
        if fr.FeatureTag == "frac":
            return i, fr
    return None, None


def rebuild(font, verbose=True):
    gsub = font["GSUB"].table
    cm = font.getBestCmap()

    numr, dnom = get_numr_dnom_maps(gsub)
    if not numr or not dnom:
        if verbose:
            print("  缺 numr/dnom，跳过")
        return 0

    fi, fr = find_frac_feature(gsub)
    if fr is None:
        if verbose:
            print("  无 frac 特性，跳过")
        return 0

    # ---- 1) 收集 numr 字形名（含 tabular 变体）
    numr_names = list(dict.fromkeys(numr.values()))
    dnom_map_by_numr = {}
    for src_name, nu_name in numr.items():
        if src_name in dnom:
            dnom_map_by_numr[nu_name] = dnom[src_name]
    if verbose:
        print("  numr 字形 %d 个，可映射到 dnom 的 %d 个" % (len(numr_names), len(dnom_map_by_numr)))

    luks = gsub.LookupList.Lookup

    # ---- 2) numr->dnom 的 SingleSubst
    ss = ot.SingleSubst()
    ss.mapping = dict(dnom_map_by_numr)
    lk_dn = ot.Lookup()
    lk_dn.LookupType = 1
    lk_dn.LookupFlag = 0
    lk_dn.SubTable = [ss]
    lk_dn.SubTableCount = 1
    idx_dn = len(luks)
    luks.append(lk_dn)

    # ---- 3) slash -> fraction 的 SingleSubst
    slash_gn = cm.get(0x002F)
    frac_gn = cm.get(0x2044)
    idx_slash = None
    if slash_gn and frac_gn and slash_gn != frac_gn:
        ss2 = ot.SingleSubst()
        ss2.mapping = {slash_gn: frac_gn}
        lk2 = ot.Lookup()
        lk2.LookupType = 1
        lk2.LookupFlag = 0
        lk2.SubTable = [ss2]
        lk2.SubTableCount = 1
        idx_slash = len(luks)
        luks.append(lk2)

    # ---- 4) 原始数字 -> numr 的 SingleSubst（含 tabular）
    numr_full = dict(numr)
    locl_tab = {}
    for fr2 in gsub.FeatureList.FeatureRecord:
        if fr2.FeatureTag == "locl":
            for li in fr2.Feature.LookupListIndex:
                lk = luks[li]
                if lk.LookupType == 1:
                    m = getattr(lk.SubTable[0], "mapping", {})
                    if len(m) >= 10:
                        locl_tab.update(m)
    for dn, tn in locl_tab.items():
        if dn in numr:
            numr_full[tn] = numr[dn]

    ss3 = ot.SingleSubst()
    ss3.mapping = dict(numr_full)
    lk3 = ot.Lookup()
    lk3.LookupType = 1
    lk3.LookupFlag = 0
    lk3.SubTable = [ss3]
    lk3.SubTableCount = 1
    idx_numr = len(luks)
    luks.append(lk3)

    # ---- 5) ChainContext: fraction 后连续 numr 全转 dnom
    # 关键: HarfBuzz 对每个字形只应用一次 lookup，且从左到右。
    # 处理第 2 个数字时，前一个已是 numr（不是 fraction），backtrack 失效。
    # 解法: 对第 k 个数字用 LookAhead 判断「后面还有 N 个 numr」，
    #       配合不同的 depth 从后往前贪婪匹配。
    #
    # 更简单可靠的方案: 用 AGAIN 标志不可行（OpenType 无）。
    # 实际采用: 对每个位置 k，Backtrack = [fraction, numr*(k-1)] 用 ORIGINAL 判断。
    #   HarfBuzz 的 backtrack 基于【当前字形之前的原始字形】还是【已替换的】？
    #   实测表明: 同一 lookup 内的替换对后续字形的 backtrack 不可见，
    #   但【不同 lookup】之间是可见的。
    # => 把 4 条规则拆成 4 个独立 lookup，按从后往前顺序执行。
    #
    # 从后往前: 先处理第 4 个数字（lookahead 0 个 numr），
    #           再第 3 个（lookahead 1 个），以此类推。
    chain_lookups = []
    for depth in range(4, 0, -1):
        chain = ot.ChainContextSubst()
        chain.Format = 3
        # Backtrack: [numr*(depth-1), fraction]  (从近到远)
        chain.BacktrackGlyphCount = depth
        chain.BacktrackCoverage = []
        for _ in range(depth - 1):
            cov = ot.Coverage()
            cov.glyphs = sorted(numr_names)
            chain.BacktrackCoverage.append(cov)
        cov_f = ot.Coverage()
        cov_f.glyphs = [frac_gn]
        chain.BacktrackCoverage.append(cov_f)
        # Input: 目标 numr
        chain.InputGlyphCount = 1
        chain.InputCoverage = [ot.Coverage()]
        chain.InputCoverage[0].glyphs = sorted(numr_names)
        chain.LookAheadGlyphCount = 0
        chain.LookAheadCoverage = []
        chain.SubstCount = 1
        rec = ot.SubstLookupRecord()
        rec.SequenceIndex = 0
        rec.LookupListIndex = idx_dn
        chain.SubstLookupRecord = [rec]

        lk_chain = ot.Lookup()
        lk_chain.LookupType = 6
        lk_chain.LookupFlag = 0
        lk_chain.SubTable = [chain]
        lk_chain.SubTableCount = 1
        idx_c = len(luks)
        luks.append(lk_chain)
        chain_lookups.append(idx_c)

    idx_chain = chain_lookups[0]
    if verbose:
        print("  ChainContext %d 条 (从后往前): %s" % (len(chain_lookups), chain_lookups))

    gsub.LookupList.LookupCount = len(luks)

    # ---- 6) 重写 frac 的 lookup 列表（顺序关键: slash -> numr -> chain）
    new_list = []
    if idx_slash is not None:
        new_list.append(idx_slash)
    new_list.append(idx_numr)
    new_list.extend(chain_lookups)
    fr.Feature.LookupListIndex = new_list
    fr.Feature.LookupCount = len(new_list)

    if verbose:
        print("  frac lookups -> %s" % new_list)
        print("    [%d] slash->fraction" % idx_slash if idx_slash else "    (无 slash 替换)")
        print("    [%d] 数字->numr (%d 条)" % (idx_numr, len(numr_full)))
        print("    [%d] ChainContext [fraction] numr->dnom (%d 字形)" % (idx_chain, len(numr_names)))

    return 1



def main():
    import os
    SRC = os.environ.get("WDS_SRC", "/workspace/wdsans2/build/masters_R58")
    OUT = os.environ.get("WDS_OUT", "/workspace/wdsans2/build/masters_R59")
    FILES = [("master-ExtraLight-250.otf", 250),
             ("master-Regular-400.otf", 400),
             ("master-Heavy-900.otf", 900)]
    os.makedirs(OUT, exist_ok=True)
    for fn, w in FILES:
        dst = os.path.join(OUT, fn)
        if os.path.exists(dst):
            print("[%d] exists" % w, flush=True)
            continue
        print("[%d] %s" % (w, fn), flush=True)
        f = TTFont(os.path.join(SRC, fn))
        n = rebuild(f, verbose=True)
        if n:
            f["post"].formatType = 3.0
            f["post"].glyphOrder = None
            f.save(dst)
            print("  saved", flush=True)
        f.close()
    print("done")


if __name__ == "__main__":
    main()

