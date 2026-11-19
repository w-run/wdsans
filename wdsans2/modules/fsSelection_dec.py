#!/usr/bin/env python3
"""fsSelection_dec - 解析 fsSelection 的每个 bit，判断实际行高来源"""
from fontTools.ttLib import TTFont

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS":  "/workspace/wdsans/ref/hos/hos-400.ttf",
}

# fsSelection bits 相关说明
BITS = [
    (0, "ITALIC"),
    (1, "UNDERSCORE"),
    (2, "NEGATIVE"),
    (3, "OUTLINED"),
    (4, "STRIKEOUT"),
    (5, "BOLD"),
    (6, "REGULAR"),
    (7, "USE_TYPO_METRICS"),
    (8, "WWS"),
    (9, "OBLIQUE"),
]

print("%-6s %8s  %s" % ("字体", "fsSel", "置位的 bit"))
print("-" * 60)
for name, path in FONTS.items():
    f = TTFont(path, lazy=True)
    v = f["OS/2"].fsSelection
    on = [nm for bit, nm in BITS if v & (1 << bit)]
    print("%-6s 0x%04X  %s" % (name, v, ", ".join(on) if on else "无"))
    f.close()

print()
print("=== USE_TYPO_METRICS (bit7) 的影响 ===")
print('  置位: 应用用 sTypoAscender/Descender/LineGap 排版')
print('  未置: 应用用 usWinAscent/Descent（Windows）或 hhea（macOS）')

for name, path in FONTS.items():
    f = TTFont(path, lazy=True)
    v = f["OS/2"].fsSelection; os2 = f["OS/2"]; hh = f["hhea"]
    typo = os2.sTypoAscender - os2.sTypoDescender + os2.sTypoLineGap
    win = os2.usWinAscent + os2.usWinDescent
    hhea_v = hh.ascent - hh.descent + hh.lineGap
    used = typo if (v & 0x80) else win
    print("  %-6s typo=%-5d win=%-5d hhea=%-5d  -> 实际用 %d (%.2fem)" % (
        name, typo, win, hhea_v, used, used/1000.0))
    f.close()

print()
print("=== 若关闭 bit7，我们与 SHS 都变成 usWin=1448 (1.45em) ===")
print("  这是 CJK 字体的常见设定（留出注音/上标空间）")
print("  OPPO=1319 (1.32em) / HOS typo=1327 (1.33em) 都更紧凑")