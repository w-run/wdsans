#!/usr/bin/env python3
"""m_prune_glyphs - 删除子集中无人引用的字形

问题: fontTools subsetter 保留 7940 个字形，但:
  4231 在 cmap 中
  1531 被 GSUB 引用
  2292 纯冗余（无人引用）

这些冗余字形贡献了 gvar 和 glyf 的额外体积。
本模块在 subset 后清理，保持 cmap 与 GSUB 完整性。
"""
import sys
from fontTools.ttLib import TTFont


def collect_used(font):
    """收集所有被引用的字形"""
    used = set()
    # cmap
    for table in font["cmap"].tables:
        used |= set(table.cmap.values())
    # GSUB / GPOS 引用
    for tag in ("GSUB", "GPOS"):
        if tag not in font:
            continue
        t = font[tag].table
        if not t.LookupList:
            continue
        for lk in t.LookupList.Lookup:
            for st in lk.SubTable:
                for attr in ("mapping", "alternates", "ligatures", "Coverage",
                             "BacktrackCoverage", "InputCoverage", "LookAheadCoverage"):
                    v = getattr(st, attr, None)
                    if v is None:
                        continue
                    if attr == "mapping":
                        used |= set(v.keys()) | set(v.values())
                    elif attr == "alternates":
                        for lst in v.values():
                            used |= set(lst)
                        used |= set(v.keys())
                    elif attr == "ligatures":
                        for lst in v.values():
                            for lig in lst:
                                used |= set(lig.Component) | {lig.LigGlyph}
                        used |= set(v.keys())
                    elif isinstance(v, list):
                        for cov in v:
                            if hasattr(cov, "glyphs"):
                                used |= set(cov.glyphs)
                    elif hasattr(v, "glyphs"):
                        used |= set(v.glyphs)
                # Context / ChainContext
                for rs_attr in ("SubRuleSet", "SubClassSet", "ChainSubRuleSet", "ChainSubClassSet"):
                    rss = getattr(st, rs_attr, None)
                    if not rss:
                        continue
                    for rs in rss:
                        if rs is None:
                            continue
                        rules = getattr(rs, "SubRule", None) or getattr(rs, "ChainSubRule", None) or getattr(rs, "SubClassRule", None) or getattr(rs, "ChainSubClassRule", None) or []
                        for r in rules:
                            for a in ("Input", "Backtrack", "LookAhead"):
                                vv = getattr(r, a, None)
                                if isinstance(vv, list):
                                    used |= set(x for x in vv if isinstance(x, str))
                # MarkBasePos / MarkMarkPos / CursivePos
                for a in ("MarkCoverage", "BaseCoverage", "Mark1Coverage", "Mark2Coverage"):
                    cov = getattr(st, a, None)
                    if cov is not None and hasattr(cov, "glyphs"):
                        used |= set(cov.glyphs)
    # GDEF
    if "GDEF" in font:
        g = font["GDEF"].table
        if g.GlyphClassDef:
            used |= set(g.GlyphClassDef.classDefs.keys())
        if g.LigCaretList and g.LigCaretList.Coverage:
            used |= set(g.LigCaretList.Coverage.glyphs)
        if g.MarkAttachClassDef:
            used |= set(g.MarkAttachClassDef.classDefs.keys())
    return used


def prune(font, verbose=True):
    used = collect_used(font)
    allg = set(font.getGlyphOrder())
    drop = allg - used - {".notdef"}
    if verbose:
        print("    总字形 %d, 使用 %d, 可删 %d" % (len(allg), len(used), len(drop)), flush=True)
    if not drop:
        return 0
    # fontTools 的 subsetter 可以做精确裁剪
    from fontTools import subset
    opt = subset.Options()
    opt.glyph_names = True
    opt.notdef_outline = True
    opt.name_IDs = ["*"]
    opt.name_legacy = True
    opt.layout_features = ["*"]
    opt.drop_tables = []
    opt.passthrough_tables = False
    ss = subset.Subsetter(options=opt)
    ss.populate(glyphs=sorted(used | {".notdef"}))
    ss.subset(font)
    if verbose:
        print("    裁剪后字形 %d" % len(font.getGlyphOrder()), flush=True)
    return len(drop)

