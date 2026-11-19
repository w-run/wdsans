#!/usr/bin/env python3
"""os2_version - OS/2 版本检查与升级影响"""
from fontTools.ttLib import TTFont

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS":  "/workspace/wdsans/ref/hos/hos-400.ttf",
}

print("%-6s %8s %10s %10s %12s" % ("字体","OS/2版本","fsSelection","bit7/8","行高来源"))
print("-" * 56)
for name, path in FONTS.items():
    f = TTFont(path, lazy=True)
    o = f["OS/2"]
    ver = o.version
    fs = o.fsSelection
    b7 = bool(fs & 0x80); b8 = bool(fs & 0x100)
    src = 'typo' if b7 else 'hhea/win'
    print("%-6s %8d 0x%08X %6s/%6s %12s" % (name, ver, fs, "ON" if b7 else "off", "ON" if b8 else "off", src))
    f.close()

print()
print("=== OS/2 version 3 -> 4 需要哪些字段 ===")
print('v4 新增: usLowerOpticalPointSize, usUpperOpticalPointSize（各 2 字节）')
print('其它字段与 v3 完全相同。fontTools 会自动补默认值。')

print()
print('=== 风险评估 ===')
print('1. 表结构变化很小（只多 4 字节）')
print('2. 但改变了 OS/2 版本号 -> 严格的校验工具可能报错')
print('3. 影响范围: 所有平台的行高计算')
print('4. OPPO/HOS 都是 v4（它们能置 bit8 WWS）')

print()
print("=== 决定性考量 ===")
print('本项目是个人使用、面向手机 UI。')
print('行高 1.45em vs OPPO 1.32em 的差异确实可见（14px 下 7 行差 35px）。')
print('但:')
print('  - 网页排版通常用 CSS line-height 显式指定（如 1.5），')
print('    字体自带的行高只在未指定时作 fallback')
print('  - 改动 OS/2 版本 + typo 度量会改变所有未显式指定行高的场景')
print('  - SHS 保持 1.45em 是有意的（容纳注音）')