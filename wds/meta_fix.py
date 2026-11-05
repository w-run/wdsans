"""Metadata fixes for the two REAL fontbakery findings.

KEYS CORRECTION after inspecting the fail list:
 - zero-advance width (uni20DD etc.) is NOT a bug for this font.  All 13
   zero-width glyphs are COMBINING MARKS (gravecomb, acutecomb, uni302A/B/C/D,
   uni3099/309A, uni20DD/20DE).  Combining marks are supposed to have zero
   advance - the Noto base has exactly the same 13 at zero.  fontbakery's
   base_has_width heuristic does not know about CJK combining classes.
   => left as is, documented as an accepted deviation.

 - head.fontRevision 2.004 vs name ID5 "Version 1.000": REAL mismatch,
   inherited from Source Han Sans.  Fixed.

 - OS/2.fsSelection == 0b0: REAL.  Even for the Regular weight neither the
   REGULAR bit (6) nor the BOLD bit (5) is set, so Windows cannot tell this
   is the regular face.  Fixed per style.

Accepted, not fixed:
 - massive-font (21 MB > 9 MB): inherent to 65k CJK glyphs.
 - mac-names: fontbakery wants Mac platform name records removed; keeping
   them is harmless.
"""
from __future__ import annotations

from fontTools.ttLib import TTFont

VERSION_STR = "Version 1.000"


def fix_version(font):
    f = font["head"]
    major, minor = VERSION_STR.replace("Version ", "").split(".")
    f.fontRevision = float(f"{major}.{minor}")
    return f.fontRevision


def fix_fsselection(font, style):
    """Set OS/2.fsSelection bits 5 (bold) / 6 (regular) per style.

    P39 修正：非 RIBBI 档位（Thin/Light/Normal/Medium/Heavy）不能只清 bit6，
    因为 nameID 2 仍写着 "Regular"，两者矛盾 —— fontbakery 会据此判定
    该字体「应该是 Regular」，于是要求 bit6=1，报 bad-REGULAR。

    正确做法（OpenType 规范）：非 RIBBI 档位的 nameID 2 用描述性 style 名，
    fsSelection 的 bold/regular 位都清零（Windows 只看 weight class）。
    """
    os2 = font["OS/2"]
    sel = os2.fsSelection & ~((1 << 0) | (1 << 5) | (1 << 6))
    if style == "Bold":
        sel |= (1 << 5)
        font["head"].macStyle = (font["head"].macStyle | 0x1)
    elif style == "Regular":
        sel |= (1 << 6)
        font["head"].macStyle = (font["head"].macStyle & ~0x1)
    else:
        font["head"].macStyle = (font["head"].macStyle & ~0x1)
        # nameID 2 改为描述性 style 名，与 fsSelection 保持一致
        set_style_name(font, style)
    os2.fsSelection = sel
    return bin(sel)


def set_style_name(font, style):
    """把 nameID 2 设为描述性 style 名（非 RIBBI 档位应为 Thin/Light/...）。"""
    nm = font["name"]
    changed = 0
    for rec in nm.names:
        if rec.nameID == 2:
            if rec.platformID == 3 and rec.platEncID in (1, 10):
                rec.string = style.encode("utf-16-be")
                changed += 1
            elif rec.platformID == 0:
                rec.string = style.encode("utf-16-be")
                changed += 1
            elif rec.platformID == 1 and rec.platEncID == 0:
                rec.string = style.encode("mac_roman", errors="replace")
                changed += 1
    # 同时改 nameID 17（typographic subfamily）
    for rec in nm.names:
        if rec.nameID == 17:
            if rec.platformID in (0, 3):
                rec.string = style.encode("utf-16-be")
            elif rec.platformID == 1 and rec.platEncID == 0:
                rec.string = style.encode("mac_roman", errors="replace")
    return changed
