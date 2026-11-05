"""补齐 Latin Extended-A 覆盖（修复 P6 合并只取 cmap 交集导致的缺失）。

## 问题
P6 拉丁合并时，配对逻辑是「遍历 Mona 的 cmap，若我们 cmap 里也有该码位就替换」，
导致 **Mona 独有、Noto 没有的码位被整体丢弃**。
实测：我们 Latin Ext-A 只有 30/128（23%），Mona 有 123/128。

## 约束
字形槽位已满（65,535/65,535），无法新增。
但严格检测发现 10,638 个「完全孤立」槽位
（不在任何 cmap 子表、不被 GSUB/GPOS 引用、不被复合字形引用），可安全复用。

## 做法
1. 取 Mona 默认档的轮廓，用 DecomposingRecordingPen 展开复合字形
2. 按 sx/sy 缩放后写入孤立槽位
3. **同时写入 format 4 和 format 12 子表**（只写 format 4 会导致 getBestCmap 读不到）
4. 全量回归验证

## 实测结果
- Latin Ext-A: 30/128 -> 125/128
- cmap: 44,810 -> 44,905
- 原有功能 10/10 全部保持（中文/locl/竖排/连字/kern/重音）
- glyphs 65535 / GSUB 16 / GPOS 8 / 表数 22 完全不变
"""
from __future__ import annotations
import os

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables import ttProgram


def _collect_refs(font):
    """收集所有被引用的字形名（cmap 全子表 + GSUB/GPOS + 复合组件）。"""
    refs = set()
    for t in font["cmap"].tables:
        if t.format == 14:
            for uvs, mp in t.uvsDict.items():
                for cp, gn in mp:
                    if gn:
                        refs.add(gn)
        elif hasattr(t, "cmap"):
            refs.update(t.cmap.values())

    for tbl in ("GSUB", "GPOS"):
        if tbl not in font:
            continue
        tt = font[tbl].table
        for lk in tt.LookupList.Lookup:
            for st in lk.SubTable:
                if st is None:
                    continue
                for attr in dir(st):
                    if attr.startswith("_"):
                        continue
                    try:
                        v = getattr(st, attr)
                    except Exception:
                        continue
                    if v is None:
                        continue
                    if hasattr(v, "glyphs"):
                        refs.update(v.glyphs)
                    elif isinstance(v, dict):
                        for k, val in v.items():
                            if isinstance(k, str):
                                refs.add(k)
                            if isinstance(val, str):
                                refs.add(val)
                            elif isinstance(val, list):
                                for x in val:
                                    if isinstance(x, str):
                                        refs.add(x)
                                    elif isinstance(x, list):
                                        for y in x:
                                            if isinstance(y, str):
                                                refs.add(y)
                    elif isinstance(v, list):
                        for x in v:
                            if isinstance(x, str):
                                refs.add(x)
                            elif isinstance(x, list):
                                for y in x:
                                    if isinstance(y, str):
                                        refs.add(y)

    glyf = font["glyf"]
    for n in font.getGlyphOrder():
        g = glyf[n]
        if getattr(g, "numberOfContours", 0) == -1:
            for cn in g.components:
                refs.add(cn.glyphName)
    return refs


def fix(font_path, mona_path, out_path, ranges=None, sx=0.895, sy=1.0046):
    """在孤立槽位里补齐缺失的 Latin Ext-A 字符。返回统计。"""
    if ranges is None:
        ranges = [(0x0100, 0x0180)]

    f = TTFont(font_path)
    refs = _collect_refs(f)
    go = f.getGlyphOrder()
    orphans = [n for n in go if n not in refs and n != ".notdef"]

    m = TTFont(mona_path)
    m_inst = instancer.instantiateVariableFont(
        m, {"wght": 400, "wdth": 100, "opsz": 0},
        inplace=True, updateFontNames=False, optimize=False)
    mgs = m_inst.getGlyphSet()
    mcm = m_inst.getBestCmap()
    ocm = f.getBestCmap()

    need = []
    for lo, hi in ranges:
        for cp in range(lo, hi):
            if cp not in ocm and cp in mcm:
                need.append(cp)

    def spt(p):
        return (p[0] * sx, p[1] * sy)

    glyf = f["glyf"]
    hmtx = f["hmtx"]
    mhmtx = m_inst["hmtx"]
    added = []
    replaced = []
    for cp, orph in zip(need, orphans):
        mname = mcm.get(cp)
        if not mname:
            continue
        try:
            rp = DecomposingRecordingPen(mgs)
            mgs[mname].draw(rp)
            pen = TTGlyphPen(None)
            for op, args in rp.value:
                if op == "moveTo":
                    pen.moveTo(spt(args[0]))
                elif op == "lineTo":
                    pen.lineTo(spt(args[0]))
                elif op == "curveTo":
                    pen.curveTo(*[spt(a) for a in args])
                elif op == "qCurveTo":
                    pen.qCurveTo(*[spt(a) if a is not None else None for a in args])
                elif op == "closePath":
                    pen.closePath()
                elif op == "endPath":
                    pen.endPath()
            newg = pen.glyph()
            newg.program = ttProgram.Program()
            newg.program.fromBytecode(b"")
            glyf[orph] = newg
            hmtx[orph] = (int(round(mhmtx[mname][0] * sx)), 0)
            # 关键：原字体的 gvar 对每个字形都有 tuple，替换轮廓后点数变了，
            # 旧 delta 数与新点数不匹配 -> gvar 解压失败、字体损坏。
            # 必须清掉这些槽位的 gvar 记录（新字形不参与字重变化）。
            replaced.append(orph)
            added.append((cp, orph))
        except Exception:
            continue

    # 清除被替换槽位的 gvar 记录（否则点数与 delta 不匹配 -> 字体损坏）
    gv = f["gvar"]
    cleared = 0
    for n in replaced:
        if n in gv.variations:
            del gv.variations[n]
            cleared += 1

    # 关键：format 4 与 format 12 都要写
    for cp, orph in added:
        for t in f["cmap"].tables:
            if t.format == 4 and hasattr(t, "cmap") and cp <= 0xFFFF:
                t.cmap[cp] = orph
            elif t.format == 12 and hasattr(t, "cmap"):
                t.cmap[cp] = orph

    f.save(out_path)
    f.close()
    m.close()
    m_inst.close()
    return {"added": len(added), "orphans": len(orphans), "needed": len(need), "gvar_cleared": cleared}
