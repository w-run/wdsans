#!/usr/bin/env python3
"""m_lineheight - 行高度量修正（R36）

问题: hhea/win = 1448 = 1.45em，比 OPPO(1.32) / HOS(1.18) 松 10-19%。
      实测 14px 下 7 行 UI 文本总高: 我们 154px vs HOS 119px（差 35px）。

方案: 启用 USE_TYPO_METRICS (fsSelection bit7)，把 sTypo 度量设为覆盖全字形的值。
      usWin 保持不变（1160/288），竖排符号仍完整可见。

为什么用 bit7 而不是直接压 hhea/win:
  - 直接压 hhea/win 会让 7 个竖排符号被裁切（上界 1325 / 下界 -549）
  - bit7 让 typo 独立于 usWin: usWin 保守不裁，typo 紧凑行高正确
  - 这是 OpenType 规范的设计意图

实测全库极端值（排除 7 个竖排专用符号）:
  最高 1069 (U+1EB2 Ẳ)  最低 -281 (U+FFE8 ￨)
  -> typo: asc=1070, desc=-282 -> 1352 = 1.35em（与 OPPO 1.32 接近）

🔴 必须先把 OS/2 从 v3 升到 v4（bit7 只在 v4+ 定义）
   实测 v3->v4 只改 version 字段，42 个字段其余不变，文件大小不变
"""
import os, sys
from fontTools.ttLib import TTFont

SRC = os.environ.get("WDS_SRC", "/workspace/wdsans2/build/masters_R35")
OUT = os.environ.get("WDS_OUT", "/workspace/wdsans2/build/masters_R36")

NEW_ASC = 1070
NEW_DESC = -282
NEW_GAP = 0

MASTERS = [
    "master-ExtraLight-250.otf",
    "master-Regular-400.otf",
    "master-Heavy-900.otf",
]


def fix(path, dst, dry=False):
    f = TTFont(path)
    o = f["OS/2"]
    old_ver = o.version
    old_typo = (o.sTypoAscender, o.sTypoDescender, o.sTypoLineGap)
    old_fs = o.fsSelection

    # 1) OS/2 v3 -> v4（bit7 需要 v4+）
    if o.version < 4:
        o.version = 4
        if not hasattr(o, 'usLowerOpticalPointSize'):
            o.usLowerOpticalPointSize = 0
        if not hasattr(o, 'usUpperOpticalPointSize'):
            o.usUpperOpticalPointSize = 0xFFFF

    # 2) 设 typo 度量
    o.sTypoAscender = NEW_ASC
    o.sTypoDescender = NEW_DESC
    o.sTypoLineGap = NEW_GAP

    # 3) 启用 USE_TYPO_METRICS
    o.fsSelection = old_fs | 0x80

    new_typo = (o.sTypoAscender, o.sTypoDescender, o.sTypoLineGap)
    lh = NEW_ASC - NEW_DESC + NEW_GAP
    print("  %-30s v%d->v%d  typo %s -> %s  行高 %d (%.2fem)  fsSel 0x%04X->0x%04X" % (
        os.path.basename(path), old_ver, o.version, old_typo, new_typo,
        lh, lh/1000.0, old_fs, o.fsSelection))

    if dry:
        f.close(); return

    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    f.save(dst)
    f.close()


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    print("m_lineheight: SRC=%s OUT=%s dry=%s" % (SRC, OUT, dry))
    for fn in MASTERS:
        p = os.path.join(SRC, fn)
        if not os.path.exists(p):
            print("  跳过 %s（不存在）" % fn); continue
        fix(p, os.path.join(OUT, fn), dry)
    print("完成")