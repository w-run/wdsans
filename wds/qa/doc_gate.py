# -*- coding: utf-8 -*-
"""文档一致性闸门（P89）。

## 为什么需要

P79 / P86 / P87 三次更正了自己的历史结论：
  - P79 更正 P78（槽位可回收性）
  - P86 更正 P67（子集丢 GDEF/mark/vkrn）
  - P87 更正 P67（子集 format 12/14）

P88 用手工把这三次更正回填到旧文档与索引里。但文档已达 93 份，
手工核对开始吃力，且以后每次更正都要重做一遍。

## 做法

维护一份「已推翻结论」登记表（OVERTURNED），每项含：
  - 被推翻的说法（关键词）
  - 更正出处（哪份文档）
  - 允许出现该关键词的文档（即更正文档本身）

扫描 docs/*.md，若某文档含被推翻关键词、却未在文中标注更正，则报警。
"""
from __future__ import annotations
import glob
import os
import re

# 已推翻的结论登记表
# (关键词正则, 说明, 更正出处, 允许出现的文件名前缀)
OVERTURNED = [
    (r"\u5b50\u96c6\u4e22\u4e86\s*GDEF",
     "子集丢失 GDEF（实为无组合标记时的正常闭包裁减）",
     "P86", ("P67", "P86", "P87", "P88")),
    (r"GPOS[^\n]{0,20}(\u4e22\u5931|8\u21926)",
     "子集 GPOS 丢 mark/vkrn（实为特性数恒定 5，未丢失）",
     "P86", ("P67", "P86", "P87", "P88")),
    (r"format 14[^\n]{0,10}\u4e22\u5931",
     "子集 format 14 丢失（实为需变体选择符在字符集内）",
     "P87", ("P67", "P86", "P87", "P88")),
    (r"\u5b57\u5f62\u69fd\u4f4d\u4e3a\s*0",
     "字形槽位为 0（实为有 10037 个未引用槽位，但均不可回收）",
     "P79", ("P78", "P79", "P88")),
]

# 出现这些词的文档视为「已标注更正」
MARKERS = ("\u66f4\u6b63", "\u5df2\u63a8\u7ffb", "\u89c2\u5bdf\u5c5e\u5b9e", "P86/P87", "P79")


def check(docs_dir=None, verbose=False):
    """返回问题数（0 = 通过）。"""
    d = docs_dir or os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "docs")
    problems = []
    for p in sorted(glob.glob(os.path.join(d, "P*.md"))):
        base = os.path.basename(p)
        stem = base.split("-")[0]
        text = open(p, encoding="utf-8").read()
        has_marker = any(m in text for m in MARKERS)
        for pat, desc, src, allowed in OVERTURNED:
            if stem in allowed:
                continue
            if re.search(pat, text):
                if not has_marker:
                    problems.append("%s \u542b\u5df2\u63a8\u7ffb\u7ed3\u8bba\u300c%s\u300d\u4f46\u672a\u6807\u6ce8\u66f4\u6b63\uff08\u89c1 %s\uff09" % (base, desc, src))
                elif verbose:
                    problems.append("[\u5df2\u6807\u6ce8] %s: %s" % (base, desc))
    for x in problems:
        print("  !! " + x)
    if not [x for x in problems if not x.startswith("[")]:
        print("  \u6587\u6863\u4e00\u81f4\u6027: \u901a\u8fc7")
    return len([x for x in problems if not x.startswith("[")])


if __name__ == "__main__":
    import sys
    n = check(verbose=("--verbose" in sys.argv))
    print("\u95ee\u9898\u6570: %d" % n)
    sys.exit(0 if n == 0 else 1)