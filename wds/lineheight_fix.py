"""修复行高：启用 USE_TYPO_METRICS，让实际行高 = 1.0em（DESIGN §7 目标）。

## 问题

DESIGN.md §7 明确：typoAscender 880 / typoDescender -120 -> 默认行高 1.0em，
并给排版留出自行调节的空间。REBUILD-PLAN 也把旧版 hhea 1160/-288（1.448em）
列为 ❌ 缺陷。

但实测交付字体：
  hhea  : 1000 / -200 / gap 0  -> 1.200 em
  typo  : 880  / -120 / gap 0  -> 1.000 em   <- 这才是设计目标
  win   : 1160 / 288           -> 1.448 em
  fsSelection bit7 (USE_TYPO_METRICS) = 未置位

未置位时，Windows / 浏览器 / Word 用 hhea 或 win，实际行高 **1.448em**，
比设计目标 1.0em 高 45%，也与 OPPO Sans（1.319em）差距明显。

## 修法

1. OS/2 升到 version 5（bit 7/8/9 只在 v4+ 定义，而
   usLower/UpperOpticalPointSize 是 v5 字段，v3->v5 字节长度 96->100）
2. 置位 fsSelection bit 7 = USE_TYPO_METRICS
3. 保留 Noto 原生 hhea/win/typo 数值不动（只改"用哪一组"）

这样：
  - 现代软件（Win10+/macOS/Linux/浏览器）按 typo 渲染 -> 行高 1.0em
  - 旧软件仍能读 hhea/win，不至于排错

## 注意

fontTools 编译时会把 usUpperOpticalPointSize 乘以 20 再打包成 H，
所以传入值上限是 65535/20 = 3276.75，取 3276。
"""
from __future__ import annotations

USE_TYPO_METRICS_BIT = 1 << 7


def enable_typo_metrics(font):
    os2 = font["OS/2"]
    before = (os2.version, os2.fsSelection)
    if os2.version < 5:
        os2.version = 5
        os2.usLowerOpticalPointSize = 0
        os2.usUpperOpticalPointSize = 3276
    os2.fsSelection |= USE_TYPO_METRICS_BIT
    after = (os2.version, os2.fsSelection)
    return before, after


def report(font):
    upm = font["head"].unitsPerEm
    hhea = font["hhea"]; os2 = font["OS/2"]
    use_typo = bool(os2.fsSelection & USE_TYPO_METRICS_BIT)
    hhea_lh = (hhea.ascender - hhea.descender + hhea.lineGap) / upm
    typo_lh = (os2.sTypoAscender - os2.sTypoDescender + os2.sTypoLineGap) / upm
    win_lh = (os2.usWinAscent + os2.usWinDescent) / upm
    return dict(use_typo=use_typo, hhea=hhea_lh, typo=typo_lh, win=win_lh,
                effective=typo_lh if use_typo else max(hhea_lh, win_lh))
