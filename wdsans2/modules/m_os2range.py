#!/usr/bin/env python3
"""m_os2range - 按实际 cmap 重算 OS/2 ulUnicodeRange 与 ulCodePageRange

问题:
  我们补了 143 个 Latin Ext 字符，但 OS/2 的 ulUnicodeRange 位仍是 SHS 原版的值。
  系统/应用依赖这些位判断字体是否支持某字符范围，位没置就等于「不支持」。

实测缺失的 14 个 bit:
  bit2   Latin Extended-A        125/128
  bit3   Latin Extended-B         30/208
  bit4   IPA Extensions            2/96
  bit5   Spacing Modifier         14/80
  bit6   Combining Diacrit        22/112
  bit9   Cyrillic                 66/304
  bit30  Superscripts              1/48
  bit31  Currency Symbols          8/48
  bit32  Combining Diacrit Symb    2/48
  bit33  Letterlike Symbols       17/80
  bit34  Number Forms             28/64
  bit35  Arrows                   25/112
  bit62  Alphabetic Pres Forms     5/80
  bit70  Halfwidth And Fullwidth 225/240

方案: 按 OpenType 规范定义的区间，检查每个 bit 是否有任何码位在 cmap 中，
      有则置位。同时按需累积 ulCodePageRange。
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_MOD18')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD19')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}

# OpenType OS/2 ulUnicodeRange 位 -> 码位区间（规范定义，取主要区间）
# 参考: https://learn.microsoft.com/en-us/typography/opentype/spec/os2
UNICODE_RANGES = {
    0: [(0x0000, 0x007F)],
    1: [(0x0080, 0x00FF)],
    2: [(0x0100, 0x017F)],
    3: [(0x0180, 0x024F)],
    4: [(0x0250, 0x02AF), (0x1D00, 0x1D7F), (0x1D80, 0x1DBF)],
    5: [(0x02B0, 0x02FF), (0xA700, 0xA71F)],
    6: [(0x0300, 0x036F), (0x1DC0, 0x1DFF)],
    7: [(0x0370, 0x03FF), (0x1F00, 0x1FFF)],
    8: [(0x2C80, 0x2CFF), (0x2C00, 0x2C5F)],
    9: [(0x0400, 0x04FF), (0x0500, 0x052F), (0x2DE0, 0x2DFF), (0xA640, 0xA69F)],
    10: [(0x0530, 0x058F)],
    11: [(0x0590, 0x05FF)],
    12: [(0xA500, 0xA63F)],
    13: [(0x0600, 0x06FF), (0x0750, 0x077F)],
    14: [(0x07C0, 0x07FF)],
    15: [(0x0900, 0x097F)],
    16: [(0x0980, 0x09FF)],
    17: [(0x0A00, 0x0A7F)],
    18: [(0x0A80, 0x0AFF)],
    19: [(0x0B00, 0x0B7F)],
    20: [(0x0B80, 0x0BFF)],
    21: [(0x0C00, 0x0C7F)],
    22: [(0x0C80, 0x0CFF)],
    23: [(0x0D00, 0x0D7F)],
    24: [(0x0E00, 0x0E7F)],
    25: [(0x0E80, 0x0EFF)],
    26: [(0x10A0, 0x10FF), (0x2D00, 0x2D2F)],
    27: [(0x1B00, 0x1B7F)],
    28: [(0x1100, 0x11FF)],
    29: [(0x1E00, 0x1EFF), (0x2E80, 0x2EFF), (0x2F00, 0x2FDF),
         (0x2FF0, 0x2FFF), (0x3000, 0x303F), (0x3190, 0x319F),
         (0x31C0, 0x31EF), (0x3300, 0x33FF), (0x4DC0, 0x4DFF),
         (0xA700, 0xA71F), (0xFE10, 0xFE1F), (0xFE30, 0xFE4F),
         (0xFE50, 0xFE6F), (0xFF00, 0xFFEF), (0xFFF0, 0xFFFD)],
    30: [(0x2070, 0x209F)],
    31: [(0x20A0, 0x20CF)],
    32: [(0x20D0, 0x20FF)],
    33: [(0x2100, 0x214F)],
    34: [(0x2150, 0x218F)],
    35: [(0x2190, 0x21FF), (0x27F0, 0x27FF), (0x2900, 0x297F), (0x2B00, 0x2BFF)],
    36: [(0x2200, 0x22FF), (0x27C0, 0x27EF), (0x2980, 0x29FF), (0x2A00, 0x2AFF)],
    37: [(0x2300, 0x23FF)],
    38: [(0x2400, 0x243F)],
    39: [(0x2440, 0x245F)],
    40: [(0x2460, 0x24FF)],
    41: [(0x2500, 0x257F)],
    42: [(0x2580, 0x259F)],
    43: [(0x25A0, 0x25FF)],
    44: [(0x2600, 0x26FF)],
    45: [(0x2700, 0x27BF)],
    46: [(0x3000, 0x303F), (0x2E80, 0x2EFF), (0x31C0, 0x31EF)],
    47: [(0x3100, 0x312F), (0x31A0, 0x31BF)],
    48: [(0x3000, 0x303F)],
    49: [(0x3040, 0x309F)],
    50: [(0x30A0, 0x30FF), (0x31F0, 0x31FF)],
    51: [(0x3100, 0x312F), (0x31A0, 0x31BF)],
    52: [(0x3130, 0x318F)],
    53: [(0xA840, 0xA87F)],
    54: [(0x3200, 0x32FF)],
    55: [(0x3300, 0x33FF)],
    56: [(0xAC00, 0xD7AF)],
    57: [(0x10000, 0x10FFFF)],
    58: [(0x10900, 0x1091F)],
    59: [(0x4E00, 0x9FFF), (0x2E80, 0x2EFF), (0x2F00, 0x2FDF), (0x3400, 0x4DBF)],
    60: [(0xE000, 0xF8FF)],
    61: [(0x31C0, 0x31EF)],
    62: [(0xFB00, 0xFB4F)],
    63: [(0xFB50, 0xFDFF)],
    64: [(0xFE20, 0xFE2F)],
    65: [(0xFE10, 0xFE1F), (0xFE30, 0xFE4F)],
    66: [(0xFE50, 0xFE6F)],
    67: [(0xFE70, 0xFEFF)],
    68: [(0xFE50, 0xFE6F)],
    69: [(0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    70: [(0xFF00, 0xFFEF)],
    71: [(0xFEFF, 0xFEFF), (0xFFF0, 0xFFFD)],
    72: [(0x0F00, 0x0FFF)],
    73: [(0x0700, 0x074F)],
    74: [(0x1F00, 0x1FFF)],
    75: [(0x1400, 0x167F)],
    76: [(0x1680, 0x169F)],
    77: [(0x16A0, 0x16FF)],
    78: [(0x1780, 0x17FF)],
    79: [(0x1900, 0x194F)],
    80: [(0x1950, 0x197F)],
    81: [(0x1980, 0x19DF)],
    82: [(0x1A00, 0x1A1F)],
    83: [(0x2C00, 0x2C5F)],
    84: [(0x2D30, 0x2D7F)],
    85: [(0xA800, 0xA82F)],
    86: [(0x4E00, 0x9FFF)],
    87: [(0xA000, 0xA48F)],
    88: [(0xA490, 0xA4CF)],
    89: [(0x2800, 0x28FF)],
    90: [(0xA000, 0xA48F)],
    91: [(0x1700, 0x171F)],
    92: [(0x1720, 0x173F)],
    93: [(0x1740, 0x175F)],
    94: [(0x1760, 0x177F)],
    95: [(0x10300, 0x1032F)],
    96: [(0x10330, 0x1034F)],
    97: [(0x10400, 0x1044F)],
    98: [(0x1D000, 0x1D0FF)],
    99: [(0x1D100, 0x1D1FF)],
    100: [(0x1D200, 0x1D24F)],
    101: [(0x1D300, 0x1D35F)],
    102: [(0x1D360, 0x1D37F)],
    103: [(0x1D400, 0x1D7FF)],
    104: [(0xF0000, 0xFFFFD)],
    105: [(0x100000, 0x10FFFD)],
}

CODEPAGE_RANGES = {
    0: 'Latin1_1252', 1: 'Latin2_1250', 2: 'Cyrillic_1251', 3: 'Greek_1253',
    4: 'Turkish_1254', 5: 'Hebrew_1255', 6: 'Arabic_1256', 7: 'Baltic_1257',
    8: 'Vietnamese_1258', 16: 'Latin1_alt', 17: 'Latin2_alt', 18: 'Cyrillic_alt',
    19: 'Greek_alt', 20: 'Turkish_alt', 21: 'Hebrew_alt', 22: 'Arabic_alt',
    23: 'Baltic_alt', 24: 'Vietnamese_alt', 29: 'Mac_Roman', 30: 'OEM',
    48: 'Thai_874', 49: 'Japanese_932', 50: 'Chinese_936',
    51: 'Korean_949', 52: 'Chinese_950', 53: 'Korean_1361',
    54: 'Macintosh', 55: 'OEM_alt', 56: 'Symbol', 57: 'IBM_Greek_869',
    58: 'MSDOS_Russian_866', 59: 'MSDOS_Nordic_865', 60: 'Arabic_864',
    61: 'Canadian_French_863', 62: 'Hebrew_862', 63: 'Icelandic_861',
    64: 'Portuguese_860', 65: 'Turkish_857', 66: 'Cyrillic_855',
    67: 'Latin2_852', 68: 'Baltic_775', 69: 'Greek_737', 70: 'Arabic_708',
    71: 'Latin1_850', 72: 'US_437',
}


def cp_in_ranges(cmset, ranges):
    for lo, hi in ranges:
        # 区间可能很大，用 min/max 快速判断后逐点检查
        if hi - lo > 20000:
            # 大区间（如 CJK），抽样判断
            for cp in range(lo, min(hi + 1, lo + 500)):
                if cp in cmset:
                    return True
            # 也检查区间末尾
            for cp in range(max(lo, hi - 500), hi + 1):
                if cp in cmset:
                    return True
            return False
        else:
            for cp in range(lo, hi + 1):
                if cp in cmset:
                    return True
    return False


def main():
    os.makedirs(OUTD, exist_ok=True)
    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        cm = set(f.getBestCmap().keys())
        os2 = f['OS/2']

        old1, old2, old3, old4 = (os2.ulUnicodeRange1, os2.ulUnicodeRange2,
                                  os2.ulUnicodeRange3, os2.ulUnicodeRange4)
        r = [0, 0, 0, 0]
        added = []
        for b in range(128):
            if b not in UNICODE_RANGES:
                continue
            if cp_in_ranges(cm, UNICODE_RANGES[b]):
                r[b // 32] |= (1 << (b % 32))
                # 检查是否是新置的位
                old = [old1, old2, old3, old4][b // 32]
                if not (old & (1 << (b % 32))):
                    added.append(b)

        os2.ulUnicodeRange1 = r[0]
        os2.ulUnicodeRange2 = r[1]
        os2.ulUnicodeRange3 = r[2]
        os2.ulUnicodeRange4 = r[3]

        # CodePageRange: 有对应字符集就置位
        cp_sets = {
            0: range(0x00, 0x100),           # Latin1
            1: range(0x00, 0x100),           # Latin2（近似）
            2: range(0x0400, 0x0500),        # Cyrillic
            48: range(0x0E00, 0x0E80),       # Thai
            49: range(0x3040, 0x3100),       # Japanese
            50: set(),                        # Chinese 936 — 见下
            51: range(0xAC00, 0xD7B0),       # Korean
            52: set(),                        # Chinese 950
            54: range(0x00, 0x100),          # Macintosh
        }
        # 中文特殊处理：有 CJK 统一表意文字即置位
        has_cjk = any(0x4E00 <= c <= 0x9FFF for c in list(cm)[:5000]) or \
                  cp_in_ranges(cm, [(0x4E00, 0x9FFF)])
        cp1, cp2 = os2.ulCodePageRange1, os2.ulCodePageRange2
        if has_cjk:
            cp1 |= (1 << 18)   # bit50 = 936 Chinese Simplified
            cp1 |= (1 << 20)   # bit52 = 950 Chinese Traditional
        os2.ulCodePageRange1 = cp1
        os2.ulCodePageRange2 = cp2

        print('  %s: 新增 %d 个 UnicodeRange 位 %s' % (tag, len(added), added), flush=True)
        print('      R1=0x%08X R2=0x%08X R3=0x%08X R4=0x%08X' % (
            r[0], r[1], r[2], r[3]), flush=True)
        print('      CodePage: 0x%08X 0x%08X' % (os2.ulCodePageRange1, os2.ulCodePageRange2), flush=True)

        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()


if __name__ == "__main__":
    main()
