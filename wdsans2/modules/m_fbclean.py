#!/usr/bin/env python3
"""m_fbclean - 修复 fontbakery 报告的真缺陷（R37）

来源: fontbakery 1.1.0 check-universal（专业工具，非自写脚本）

FAIL 1: opentype/font_version
  head.fontRevision = 2.00499（SHS 遗留），name ID5 = "Version 1.000"
  -> 两者不一致，不同应用会显示不同版本号
  修: head.fontRevision 改成 1.000

FAIL 2: base_has_width
  uni20DD / uni20DE advance=0，被当成零宽基底字符
  实际它们是 COMBINING ENCLOSING CIRCLE/SQUARE，advance 本来就该 0
  根因: GDEF GlyphClassDef 几乎为空（只有 4 个 mark），
        组合符号没被标为 mark -> fontbakery 按 base 检查
  修: 按 unicodedata 的 Mn/Mc/Me 分类补全 GDEF mark class（+28 个）
      实测无「组合字符与普通字符共用 glyph」的冲突

WARN gdef_mark_chars / base_has_width 由同一修复解决
"""
import os, sys
import unicodedata
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables

SRC = os.environ.get("WDS_SRC", "/workspace/wdsans2/build/masters_R36")
OUT = os.environ.get("WDS_OUT", "/workspace/wdsans2/build/masters_R37")
NEW_VERSION = 1.000

MASTERS = [
    "master-ExtraLight-250.otf",
    "master-Regular-400.otf",
    "master-Heavy-900.otf",
]


def fix(path, dst, dry=False):
    f = TTFont(path)
    name = os.path.basename(path)
    log = []

    # --- 修 1: head.fontRevision 与 name ID5 对齐 ---
    old_rev = f["head"].fontRevision
    old_n5 = f["name"].getDebugName(5)
    f["head"].fontRevision = NEW_VERSION
    log.append('version: head %.5f -> %.3f (name: %s)' % (old_rev, NEW_VERSION, old_n5))

    # --- 修 2: 补全 GDEF mark class ---
    cm = f.getBestCmap()
    gd = f["GDEF"].table
    if gd.GlyphClassDef is None:
        gd.GlyphClassDef = otTables.GlyphClassDef()
        gd.GlyphClassDef.classDefs = {}
    cd = gd.GlyphClassDef.classDefs
    before_mark = sum(1 for v in cd.values() if v == 3)

    # 反向映射，检查共用
    rev = {}
    for cp, gn in cm.items():
        rev.setdefault(gn, []).append(cp)

    added = 0
    skipped_shared = 0
    for cp, gn in cm.items():
        try:
            cat = unicodedata.category(chr(cp))
        except Exception:
            continue
        # 🔴 只标 Mn(非间距) 和 Me(包围)，不标 Mc(间距)
        # Mc 有 advance > 0，标进 mark class 会报 gdef_non_mark_chars
        # 实测 U+302E/302F 是 Mc，adv=250，SHS 原版也未分类
        if cat not in ('Mn', 'Me'):
            continue
        if cd.get(gn) == 3:
            continue
        # 安全检查: 同 glyph 不能同时映射到非组合字符
        shared = False
        for oc in rev.get(gn, []):
            if oc == cp: continue
            try:
                if unicodedata.category(chr(oc)) not in ('Mn','Mc','Me'):
                    shared = True; break
            except Exception:
                pass
        if shared:
            skipped_shared += 1
            continue
        cd[gn] = 3
        added += 1

    after_mark = sum(1 for v in cd.values() if v == 3)
    log.append('GDEF mark: %d -> %d (+%d, 跳过共用 %d)' % (
        before_mark, after_mark, added, skipped_shared))

    print('  %-30s %s' % (name, ' | '.join(log)))
    if dry:
        f.close(); return

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    f.save(dst)
    f.close()


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    print("m_fbclean: SRC=%s OUT=%s dry=%s" % (SRC, OUT, dry))
    for fn in MASTERS:
        p = os.path.join(SRC, fn)
        if not os.path.exists(p):
            print("  跳过 %s" % fn); continue
        fix(p, os.path.join(OUT, fn), dry)
    print("完成")