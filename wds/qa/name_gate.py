# -*- coding: utf-8 -*-
"""命名唯一性闸门（P70）。

检查交付目录里所有字体的 ID6（PostScript 名）是否全局唯一。

## 为什么需要这个闸门

P67/P69 发现两类命名冲突：
  1. VF 与静态 Regular 的 ID6 完全相同（WDesignSansSC-Regular）
  2. 子集 12 个文件的 ID6 与全库相同，且 3755/6763 两档彼此也同名

后果：桌面安装时互相覆盖；字体管理工具只显示一个。

## 判定口径（关键）

**同一个字体的 TTF 与 WOFF2 必须同名**——它们是同一内容的不同封装。
所以唯一性按「内容实体」判断，而非按「文件」：
  - 忽略扩展名，同 basename 的 ttf/woff2 视为同一实体
  - 不同 basename 但 ID6 相同 → 冲突
"""
from __future__ import annotations
from .. import paths
import glob
import os
import re


def check(dist_dir, subset_dir=None, verbose=False):
    """返回冲突数量（0 = 通过）。"""
    from fontTools.ttLib import TTFont

    files = []
    for d in (dist_dir, subset_dir):
        if not d or not os.path.isdir(d):
            continue
        files += sorted(glob.glob(os.path.join(d, "*.ttf")))
        files += sorted(glob.glob(os.path.join(d, "*.woff2")))

    # ID6 -> [(basename无扩展, 路径)]
    owners = {}
    for p in files:
        try:
            f = TTFont(p, lazy=True)
            id6 = f["name"].getDebugName(6)
            f.close()
        except Exception:
            continue
        if not id6:
            continue
        stem = re.sub(r"\.(ttf|woff2)$", "", os.path.basename(p))
        owners.setdefault(id6, []).append((stem, p))

    conflicts = []
    for id6, items in owners.items():
        stems = {s for s, _ in items}
        if len(stems) > 1:
            conflicts.append((id6, sorted(stems)))

    for id6, stems in conflicts:
        print("  !! ID6 冲突: %s <- %s" % (id6, stems), flush=True)

    if verbose:
        print("  扫描文件 %d 个" % len(files), flush=True)
        print("  唯一 ID6 实体 %d 个" % len(owners), flush=True)
    return len(conflicts)


if __name__ == "__main__":
    import sys
    n = check(paths.DIST_DIR,
              paths.SUBSET_DIR, verbose=True)
    print("命名唯一性: %s" % ("通过" if n == 0 else "%d 个冲突" % n))
    sys.exit(0 if n == 0 else 1)