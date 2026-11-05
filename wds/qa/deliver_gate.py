# -*- coding: utf-8 -*-
"""交付包完整性闸门（P50）。

检查交付目录里：
  1. README 中 `反引号` 引用的文件名是否真实存在
  2. 必需文件是否齐全（OFL.txt / README.md / 字体文件数量）
  3. 每个字体文件是否含 name ID 0（版权，OFL 1.1 要求）

起因：P49 在 README 写了「许可证全文见 OFL.txt」，但文件根本没建。

## mode 参数（P74）

交付目录分两种形态，检查项不同：

  mode="build"  —— 构建产物目录（只有字体文件）。
                   跳过 README/OFL 检查，避免每次构建刷出噪音。
  mode="package"—— 最终交付包（字体 + README + OFL）。
                   检查全部项（默认）。
"""
from __future__ import annotations
from .. import paths
import glob
import os
import re

REQUIRED = ["README.md", "OFL.txt"]

# README 中提到这些扩展名的 `xxx` 将被当作文件名校验
FILE_EXT = (".ttf", ".woff2", ".txt", ".md")


def check(dist_dir, subset_dir=None, verbose=False, mode="package"):
    """返回问题数量（0 = 通过）。"""
    problems = []

    # 0. 两种模式都要求：至少存在一个字体文件
    #    （P74 修复：build 模式曾因跳过必需文件检查而漏判空目录）
    fonts_here = sorted(glob.glob(os.path.join(dist_dir, "*.ttf"))) +                  sorted(glob.glob(os.path.join(dist_dir, "*.woff2")))
    if not fonts_here:
        problems.append("目录内没有任何字体文件: %s" % dist_dir)

    # 1. 必需文件（仅 package 模式检查）
    if mode == "package":
        for name in REQUIRED:
            if not os.path.exists(os.path.join(dist_dir, name)):
                problems.append("缺少必需文件: %s" % name)

    # 2. README 引用的文件是否真实存在
    readme = os.path.join(dist_dir, "README.md")
    if os.path.exists(readme):
        text = open(readme, encoding="utf-8").read()
        refs = set(re.findall(r"`([A-Za-z0-9_\-./]+\.(?:ttf|woff2|txt|md))`", text))
        for r in sorted(refs):
            if "/" in r or "\\" in r:
                continue          # 带路径的跳过（可能是示意）
            if not r.endswith(FILE_EXT):
                continue
            found = os.path.exists(os.path.join(dist_dir, r))
            if not found and subset_dir:
                found = os.path.exists(os.path.join(subset_dir, r))
            if not found:
                problems.append("README 引用了不存在的文件: %s" % r)
            elif verbose:
                print("  引用存在: %s" % r, flush=True)

    # 3. 字体版权声明
    try:
        from fontTools.ttLib import TTFont
        fonts = sorted(glob.glob(os.path.join(dist_dir, "*.ttf")))
        fonts += sorted(glob.glob(os.path.join(dist_dir, "*.woff2")))
        for p in fonts:
            try:
                f = TTFont(p, lazy=True)
                ids = {r.nameID for r in f["name"].names if r.platformID == 3}
                f.close()
                if 0 not in ids:
                    problems.append("缺少版权声明 ID0: %s" % os.path.basename(p))
            except Exception as e:
                problems.append("无法读取 %s: %s" % (os.path.basename(p), e))
    except ImportError:
        pass

    for msg in problems:
        print("  !! %s" % msg, flush=True)
    return len(problems)


if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mode = "build" if "--build" in sys.argv else "package"
    d = args[0] if args else paths.DIST_DIR
    sd = paths.SUBSET_DIR
    print("模式:", mode)
    n = check(d, sd, verbose=True, mode=mode)
    print("交付完整性: %s" % ("通过" if n == 0 else "%d 个问题" % n))
    sys.exit(0 if n == 0 else 1)
