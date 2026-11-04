"""交付流水线：VF 源 → 七档静态实例 TTF + WOFF2。

命名规则（遵循 OpenType 大家庭惯例）：
  同一家族的 7 档共享 family name "WDesign Sans"，靠 subfamily 区分。
  但 Windows 只认 4 个 RIBBI 子族（Regular/Italic/Bold/BoldItalic），
  所以非 RIBBI 档（Thin/Light/Normal/Medium/Heavy）必须用 nameID 16/17
  做「排版族名 + 样式链接」，nameID 1 写成 "WDesign Sans Light" 这类，
  否则 Windows 会把它们全塞进同一个 "WDesign Sans" 里、无法单独选择。

这是 fontbakery / Google Fonts 的标准做法（Style Linking）：
  RIBBI 档：nameID1 = family, nameID2 = Regular|Bold
  非 RIBBI 档：nameID1 = family + " " + style, nameID2 = Regular
  所有档：nameID16 = family（排版族名）, nameID17 = style
"""
from __future__ import annotations
import os
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

from .rename import STOPS, FAMILY, PS_PREFIX, VENDOR, VERSION

RIBBI = {"Regular", "Bold"}


def set_names(f: TTFont, style: str, wght: int):
    nt = f["name"]
    is_ribbi = style in RIBBI
    family_1 = FAMILY if is_ribbi else f"{FAMILY} {style}"
    subfamily_2 = "Bold" if style == "Bold" else "Regular"
    ps = f"{PS_PREFIX}-{style}"

    def _s(nid, val):
        for pid, eid, lid in ((3, 1, 1033), (3, 1, 2052), (1, 0, 0)):
            nt.setName(val, nid, pid, eid, lid)

    _s(1, family_1)
    _s(2, subfamily_2)
    _s(4, family_1 + " " + subfamily_2 if not is_ribbi else FAMILY)
    _s(6, ps)
    _s(16, FAMILY)
    _s(17, style)
    _s(3, f"{VERSION};{VENDOR};{ps};{VENDOR}")
    _s(5, VERSION)
    f["OS/2"].usWeightClass = wght
    if "head" in f:
        f["head"].macStyle = 0x1 if style == "Bold" else 0x0


def build_static(src_path: str, out_dir: str, woff2: bool = True) -> list:
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for wght, style in STOPS:
        f = TTFont(src_path)
        inst = instancer.instantiateVariableFont(
            f, {"wght": wght}, inplace=True, updateFontNames=False, optimize=False
        )
        # 去掉可变表
        for tbl in ("fvar", "gvar", "avar", "STAT", "HVAR"):
            if tbl in inst:
                del inst[tbl]
        set_names(inst, style, wght)
        p = os.path.join(out_dir, f"{PS_PREFIX}-{style}.ttf")
        inst.save(p)
        inst.close()
        results.append((p, os.path.getsize(p)))
        if woff2:
            try:
                from fontTools.ttLib import TTFont as TT
                g = TT(p)
                g.flavor = "woff2"
                wp = p.replace(".ttf", ".woff2")
                g.save(wp)
                g.close()
                results.append((wp, os.path.getsize(wp)))
            except Exception as e:
                results.append((p.replace(".ttf", ".woff2"), -1))
    return results


def build_vf_woff2(vf_path: str, out_path: str) -> int:
    g = TTFont(vf_path)
    g.flavor = "woff2"
    g.save(out_path)
    g.close()
    return os.path.getsize(out_path)