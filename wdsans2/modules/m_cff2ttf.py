#!/usr/bin/env python3
"""m_cff2ttf - CFF2 OTF -> glyf TTF 转换（静态单档）

用途: 用户要求最终产物优先 TTF。
方法: 用 TTGlyphPen + Cu2QuPen 把三次曲线转二次（glyf 只支持二次）。

注意:
- reverse_direction=True 保证轮廓方向正确（CFF 是逆时针，TTF 是顺时针）
- max_err=1.0 em 单位（upm 1000 下约 0.1% 精度）
"""
import sys, os, time
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.ttLib.tables._g_l_y_f import Glyph, table__g_l_y_f
from fontTools.ttLib.tables._l_o_c_a import table__l_o_c_a


def convert(src, dst, max_err=1.0, verbose=True):
    f = TTFont(src)
    gs = f.getGlyphSet()
    order = f.getGlyphOrder()
    if verbose:
        print("  %s: %d 字形" % (os.path.basename(src), len(order)))
    t0 = time.time()

    glyphs = {}
    n_err = 0
    for i, gn in enumerate(order):
        try:
            pen = TTGlyphPen(gs)
            q = Cu2QuPen(pen, max_err=max_err, reverse_direction=True)
            gs[gn].draw(q)
            glyphs[gn] = pen.glyph()
        except Exception as e:
            n_err += 1
            glyphs[gn] = Glyph()
            if verbose and n_err <= 3:
                print("    !! %s: %s" % (gn, str(e)[:70]))
        if verbose and (i + 1) % 20000 == 0:
            print("    已转 %d/%d  %.0fs" % (i + 1, len(order), time.time() - t0), flush=True)

    # 建 glyf
    glyf = newTable("glyf")
    glyf.glyphs = glyphs
    glyf.glyphOrder = order
    f["glyf"] = glyf

    # maxp 改为 version 1.0（TrueType）
    maxp = f["maxp"]
    maxp.tableVersion = 0x00010000
    maxp.maxZones = 1
    maxp.maxTwilightPoints = 0
    maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0
    maxp.maxInstructionDefs = 0
    maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0
    maxp.maxComponentElements = max((len(getattr(g, "components", [])) for g in glyphs.values()), default=0)

    # 移除 CFF 相关表
    for tag in ("CFF2", "CFF", "VORG"):
        if tag in f:
            del f[tag]

    # loca 必须用 table__l_o_c_a 实例（glyf.compile 会调它的 set()）
    loca = table__l_o_c_a()
    f["loca"] = loca

    # head: TrueType 标志
    f["head"].glyphDataFormat = 0
    f["head"].indexToLocFormat = 1

    # post
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None

    # 🔴 sfnt 版本必须改为 0x00010000（TrueType）
    # 从 OTF 复制过来的是 "OTTO"（0x4F54544F），PIL/浏览器会拒绝
    f.sfntVersion = "\x00\x01\x00\x00"
    f.save(dst)
    f.close()
    if verbose:
        print("    完成 %.0fs  失败 %d  输出 %.1fMB" % (
            time.time() - t0, n_err, os.path.getsize(dst) / 1e6))
    return n_err


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: m_cff2ttf.py <src.otf> <dst.ttf>")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
