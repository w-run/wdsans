# -*- coding: utf-8 -*-
"""交付 README 的事实部分生成器（P81）。

## 为什么需要

P80 审 README 时发现 7 处事实过时（文件数 16->29、体积 220.4->247.6MB、
文档 28->84 份）。

根因：**「总数」类字段依赖全局统计，而每次改动都是局部的**。

## 做法

把「文件清单 + 大小 + 合计」交给脚本生成，人只写说明性文字。

用法：
  python -m wds.gen_readme_facts            # 打印事实块
  python -m wds.gen_readme_facts --check    # 与现有 README 比对
"""
from __future__ import annotations
import glob
import os
import re
import sys

from . import paths

WEIGHTS = [("Thin", 250), ("Light", 300), ("Normal", 350), ("Regular", 400),
           ("Medium", 500), ("Bold", 700), ("Heavy", 900)]


def _mb(p):
    return os.path.getsize(p) / 1048576.0


def static_table(dist_dir=None):
    d = dist_dir or paths.DIST_DIR
    lines = ["| 文件 | 字重 | usWeightClass | 大小 |", "|---|---|---|---|"]
    for name, w in WEIGHTS:
        p = os.path.join(d, "WDesignSansSC-%s.ttf" % name)
        if os.path.exists(p):
            lines.append("| WDesignSansSC-%s.ttf | %s | %d | %.2f MB |"
                         % (name, name, w, _mb(p)))
    return chr(10).join(lines)


def web_table(dist_dir=None):
    d = dist_dir or paths.DIST_DIR
    sizes = []
    for name, _ in WEIGHTS:
        p = os.path.join(d, "WDesignSansSC-%s.woff2" % name)
        if os.path.exists(p):
            sizes.append(_mb(p))
    lines = ["| 文件 | 说明 |", "|---|---|"]
    if sizes:
        lines.append("| WDesignSansSC-{7档}.woff2 | 对应静态实例，%.2f-%.2f MB |"
                     % (min(sizes), max(sizes)))
    vf = os.path.join(d, "WDesignSansSC-VF.woff2")
    if os.path.exists(vf):
        lines.append("| **WDesignSansSC-VF.woff2** | 可变字体，单文件覆盖 250-900，%.2f MB |"
                     % _mb(vf))
    return chr(10).join(lines)


def totals(dist_dir=None, subset_dir=None):
    d = dist_dir or paths.DIST_DIR
    s = subset_dir or paths.SUBSET_DIR
    n = 0
    total = 0
    for base in (d, s):
        if not os.path.isdir(base):
            continue
        for f in glob.glob(os.path.join(base, "*")):
            if os.path.isfile(f):
                n += 1
                total += os.path.getsize(f)
    return n, total / 1048576.0


def doc_count(docs_dir=None):
    d = docs_dir or os.path.join(paths.ROOT, "docs")
    return len(glob.glob(os.path.join(d, "P*.md")))


def fact_block(dist_dir=None, subset_dir=None):
    n, mb = totals(dist_dir, subset_dir)
    docs = doc_count()
    sep = chr(10) + chr(10)
    return sep.join([
        "### 静态实例",
        static_table(dist_dir),
        "### 网页用",
        web_table(dist_dir),
        "### 合计",
        "文件数 %d（含子集与文档）  总体积 %.1f MB  编号文档 %d 份" % (n, mb, docs),
    ])


def check(dist_dir=None, readme=None):
    d = dist_dir or paths.DIST_DIR
    rp = readme or os.path.join(d, "README.md")
    if not os.path.exists(rp):
        print("!! README 不存在: %s" % rp)
        return 1
    text = open(rp, encoding="utf-8").read()
    problems = []

    for name, w in WEIGHTS:
        p = os.path.join(d, "WDesignSansSC-%s.ttf" % name)
        if not os.path.exists(p):
            continue
        actual = "%.2f MB" % _mb(p)
        pat = r"\|\s*WDesignSansSC-" + name + r"\.ttf\s*\|[^|]*\|[^|]*\|\s*([0-9.]+ MB)"
        m = re.search(pat, text)
        if m and m.group(1) != actual:
            problems.append("%s.ttf 大小: README %s != 实际 %s" % (name, m.group(1), actual))

    n, mb = totals(d)
    m = re.search(r"文件数\s+(\d+)", text)
    if m and int(m.group(1)) != n:
        problems.append("文件数: README %s != 实际 %d" % (m.group(1), n))
    m = re.search(r"总体积\s+([0-9.]+) MB", text)
    if m and abs(float(m.group(1)) - mb) > 0.15:
        problems.append("总体积: README %s != 实际 %.1f MB" % (m.group(1), mb))

    vf = os.path.join(d, "WDesignSansSC-VF.woff2")
    if os.path.exists(vf):
        m = re.search(r"WDesignSansSC-VF\.woff2\*\*[^|]*\|\s*([0-9.]+ MB)", text)
        if m and m.group(1) != "%.2f MB" % _mb(vf):
            problems.append("VF.woff2: README %s != 实际 %.2f MB" % (m.group(1), _mb(vf)))

    docs = doc_count()
    m = re.search(r"（(\d+) 份", text)
    if m and int(m.group(1)) != docs:
        problems.append("文档份数: README %s != 实际 %d" % (m.group(1), docs))

    for p in problems:
        print("  !! " + p)
    if not problems:
        print("  README 事实部分与实际一致 OK")
    return len(problems)


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(0 if check() == 0 else 1)
    else:
        print(fact_block())
