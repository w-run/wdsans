"""重命名与元数据（合规交付的第一道门）。

法律依据（实测）：
  基座 nameID 0 写的是 "Reserved Font Name 'Source'" —— 保留名是 **Source**，不是 Noto。
  所以改名为 "WDesign Sans" 合法。但必须：
    1. 移除 nameID 0（保留字体名声明）
    2. 清除所有 "Noto"/"Source"/"Adobe" 品牌字样
    3. 改写 nameID 1/3/4/6/16/17 与 fvar 实例名
    4. 保留 OFL 版权与许可（nameID 13/14）与作者署名（nameID 9/10）

七档命名实例来自 docs/DESIGN.md / wds/base.py STOPS。
"""
from __future__ import annotations

from fontTools.ttLib import TTFont

FAMILY = "WDesign Sans"
FAMILY_SC = "WDesign Sans SC"
PS_PREFIX = "WDesignSansSC"
VENDOR = "WDGN"
VERSION = "Version 1.000"

# 七档：wght -> (子族名, 是否 RIBBI)
STOPS = [
    (250, "Thin"),
    (300, "Light"),
    (350, "Normal"),
    (400, "Regular"),
    (500, "Medium"),
    (700, "Bold"),
    (900, "Heavy"),
]


def _set(name_table, nameID, value, platforms=((3, 1, 1033), (3, 1, 2052), (1, 0, 0))):
    for pid, eid, lid in platforms:
        name_table.setName(value, nameID, pid, eid, lid)


def rename_family(font: TTFont, family: str = FAMILY, ps_prefix: str = PS_PREFIX) -> list:
    """改家族名 + 清理品牌字样。返回遗留的可疑字符串列表。"""
    nt = font["name"]

    # 1. 移除保留字体名声明（OFL 要求：改名后不得再声 reserved name）
    nt.removeNames(nameID=0)

    # 1b. 移除上游商标声明（ID7）；OFL 许可(13)与作者署名(9/10)保留
    nt.removeNames(nameID=7)

    # 2. 保留版权与许可，但清掉其中的品牌词
    for r in list(nt.names):
        if r.nameID in (0, 7, 8, 11):
            continue
        try:
            s = str(r)
        except Exception:
            continue
        if r.nameID in (1, 4, 6, 16, 17, 3, 269, 271, 273, 275, 277, 279):
            continue
        new = s
        for bad, good in (("Noto Sans CJK SC", family), ("NotoSansCJKsc", ps_prefix),
                          ("Noto Sans CJK", family), ("Noto", family)):
            new = new.replace(bad, good)
        if new != s:
            r.string = new

    # 2b. 删除旧 STAT 实例名（269..279 这类 NotoSansCJKsc-*）
    for r in list(nt.names):
        if r.nameID >= 256:
            try:
                sv = str(r)
            except Exception:
                continue
            if "NotoSansCJKsc" in sv or "Noto Sans" in sv:
                nt.removeNames(nameID=r.nameID)

    # 3. 家族 / 全名 / PostScript 名
    _set(nt, 1, family)
    _set(nt, 4, family)
    _set(nt, 6, f"{ps_prefix}-Regular")
    _set(nt, 16, family)
    _set(nt, 2, "Regular")
    _set(nt, 17, "Regular")
    _set(nt, 3, f"{VERSION};{VENDOR};{ps_prefix}-Regular;{VENDOR}")
    _set(nt, 5, VERSION)
    _set(nt, 8, "WDesign")   # 厂商名改为本项目（OFL 只要求保留版权/许可/作者署名）

    # 4. 扫残留
    leftovers = []
    for r in nt.names:
        try:
            s = str(r)
        except Exception:
            continue
        for bad in ("Noto", "Source Han", "Source is a trademark", "Adobe"):
            if bad in s:
                leftovers.append((r.nameID, r.platformID, r.langID, bad, s[:60]))
    return leftovers


def rebuild_instances(font: TTFont, family: str = FAMILY, ps_prefix: str = PS_PREFIX):
    """重建 fvar 命名实例为七档。"""
    nt = font["name"]
    fvar = font["fvar"]
    # 清掉旧实例与它们的 name 记录
    old_ids = set()
    for inst in fvar.instances:
        old_ids.add(inst.subfamilyNameID)
        old_ids.add(inst.postscriptNameID)
    for nid in old_ids:
        if nid >= 256:
            nt.removeNames(nameID=nid)
    fvar.instances = []

    next_id = max([r.nameID for r in nt.names] + [255]) + 1
    for wght, sub in STOPS:
        nid = next_id; next_id += 1
        nt.setName(sub, nid, 3, 1, 1033)
        nt.setName(sub, nid, 3, 1, 2052)
        nt.setName(sub, nid, 1, 0, 0)
        ps = next_id; next_id += 1
        nt.setName(f"{ps_prefix}-{sub}", ps, 3, 1, 1033)
        nt.setName(f"{ps_prefix}-{sub}", ps, 3, 1, 2052)
        inst = fontToolsInstance(wght, nid, ps)
        fvar.instances.append(inst)


def fontToolsInstance(wght, sub_id, ps_id):
    from fontTools.ttLib.tables._f_v_a_r import NamedInstance
    inst = NamedInstance()
    inst.coordinates = {"wght": float(wght)}
    inst.subfamilyNameID = sub_id
    inst.postscriptNameID = ps_id
    return inst


def fix_os2(font: TTFont):
    """OS/2 的 usWeightClass 与粗细命名对齐（取 Regular=400 为基准文件时需按实例改）。"""
    os2 = font["OS/2"]
    if "fvar" in font:
        os2.usWeightClass = int(font["fvar"].axes[0].defaultValue)
    return os2.usWeightClass


def apply(path_in: str, path_out: str, family: str = FAMILY) -> dict:
    f = TTFont(path_in)
    leftovers = rename_family(f, family)
    rebuild_instances(f, family)
    wc = fix_os2(f)
    f.save(path_out)
    info = {"leftovers": leftovers, "usWeightClass": wc,
            "instances": [s for _, s in STOPS]}
    f.close()
    return info
