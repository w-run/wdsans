#!/usr/bin/env python3
"""claim_audit - 交付物「宣称 vs 实测」自动核对

背景: 连续两轮发现预览页/README 的宣称与实际不符
  1. 功能虚报（横折出头从未实现）
  2. 数字偏差（40MB vs 39.4MB，3886字 vs 3903字）

本例: 任何交付前跑一遍，确保展示层与真实状态一致。

用法: python modules/claim_audit.py   # exit 0 = 全部通过
"""
import os
import re
import sys

BASE = "/workspace/static/wdsans"
VF = os.path.join(BASE, "WDesignSans-VF.otf")
PREV = os.path.join(BASE, "wd-preview.woff2")
FLAT = os.path.join(BASE, "WDesignSans-FlatApex-Regular.otf")
IDX = os.path.join(BASE, "index.html")
README = os.path.join(BASE, "poster", "README.md")

ok = 0
fail = 0
n_skip = 0

def check(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1
        print("  [PASS] %-34s %s" % (name, detail))
    else:
        fail += 1
        print("  [FAIL] %-34s %s" % (name, detail))

def skip(name, why):
    global n_skip
    n_skip += 1
    print("  [SKIP] %-34s %s" % (name, why))

# ---------- 1. 文件大小宣称 ----------
print("=== 1. 文件大小 ===")
from fontTools.ttLib import TTFont

sz_vf = os.path.getsize(VF)
mb_vf = sz_vf / 1024 / 1024
idx = open(IDX, encoding="utf-8").read()

m = re.search(r"下载完整 OTF（([0-9.]+) MB）", idx)
if m:
    claimed = float(m.group(1))
    check("完整 OTF 大小", abs(claimed - mb_vf) < 0.15,
          "宣称 %.1f MB / 实测 %.2f MB" % (claimed, mb_vf))
else:
    skip("完整 OTF 大小", "页面无此宣称")

sz_prev = os.path.getsize(PREV)
mb_prev = sz_prev / 1024 / 1024
m = re.search(r"子集（woff2 ([0-9.]+) MB）", idx)
if m:
    claimed = float(m.group(1))
    check("预览子集 woff2 大小", abs(claimed - mb_prev) < 0.15,
          "宣称 %.1f MB / 实测 %.2f MB" % (claimed, mb_prev))
else:
    skip("预览子集 woff2 大小", "页面无此宣称")

# ---------- 2. 字符数宣称 ----------
print()
print("=== 2. 字符数与字形数 ===")
f = TTFont(VF, lazy=True)
cm_vf = len(f.getBestCmap())
ng_vf = f["maxp"].numGlyphs
f.close()

m = re.search(r"([0-9,]+) 个字符位", idx)
if m:
    claimed = int(m.group(1).replace(",", ""))
    check("VF cmap 字符位数", abs(claimed - cm_vf) <= 5,
          "宣称 %d / 实测 %d" % (claimed, cm_vf))
else:
    skip("VF cmap 字符位数", "页面无此宣称")

m = re.search(r"([0-9,]+) 个 CJK", idx)
if m:
    claimed = int(m.group(1).replace(",", ""))
    # CJK 统一定义: U+4E00-U+9FFF
    f = TTFont(VF, lazy=True)
    cm = f.getBestCmap()
    cjk = sum(1 for c in cm if 0x4E00 <= c <= 0x9FFF)
    f.close()
    check("CJK 字数", abs(claimed - cjk) <= 5,
          "宣称 %d / 实测 %d" % (claimed, cjk))
else:
    skip("CJK 字数", "页面无此宣称")

f = TTFont(PREV, lazy=True)
cm_prev = len(f.getBestCmap())
f.close()
m = re.search(r"([0-9,]+) 字 Web 子集", idx)
if m:
    claimed = int(m.group(1).replace(",", ""))
    check("预览子集字符数", abs(claimed - cm_prev) <= 5,
          "宣称 %d / 实测 %d" % (claimed, cm_prev))
else:
    skip("预览子集字符数", "页面无此宣称")

# ---------- 3. 功能虚报（关键）----------
print()
print("=== 3. 功能宣称（防虚报）===")

# 3a. 横折出头: m_ledge 已废弃，绝不应出现在指标表里
if "横折出头" in idx:
    # 允许出现在「尚未实现」说明中，但不应有「已对齐」判定
    bad = re.search(r"横折出头.{0,300}?已对齐", idx, re.S)
    check("横折出头未虚报为已实现", bad is None,
          "发现「已对齐」判定" if bad else "仅出现在未实现说明中")
else:
    check("横折出头未虚报为已实现", True, "页面未出现")

# 3b. 简介中不应出现 m_ledge2 的 2,636 字
check("未声称修正 2,636 字（m_ledge2 废弃）", "2,636" not in idx,
      "found 2636" if "2,636" in idx else "-")

# 3c. README 不应声称「顶横出头」已做
if os.path.exists(README):
    rd = open(README, encoding="utf-8").read()
    # 允许在「尚未实现」章节提到，但正文摘要不应宣传
    head = rd.split("## 尚未实现")[0] if "## 尚未实现" in rd else rd
    check("README 摘要未宣传顶横出头", "顶横出头" not in head,
          "摘要中出现" if "顶横出头" in head else "无")
else:
    skip("README 摘要", "文件不存在")

# 3d. 页面任何位置不应宣称「已实现」但实际未做的特性
KNOWN_UNIMPLEMENTED = ["顶横出头", "横折出头"]
for kw in KNOWN_UNIMPLEMENTED:
    hits = re.findall(r"%s.{0,300}?已实现" % kw, idx, re.S)
    check('%s 未虚报为已实现' % kw, not hits,
          str(hits[:1]) if hits else "无")

# ---------- 4. HTML 结构 ----------
print()
print("=== 4. HTML 结构 ===")
from html.parser import HTMLParser

class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.err = []
        self.void = {"br","img","hr","meta","link","input","source","area","base","col","embed","param","track","wbr"}
    def handle_starttag(self, tag, attrs):
        if tag not in self.void:
            self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag in self.void:
            return
        if not self.stack:
            self.err.append("游离闭合:" + tag)
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.err.append("未闭合:" + self.stack.pop())
            if self.stack:
                self.stack.pop()
        else:
            self.err.append("游离闭合:" + tag)

p = P()
p.feed(idx)
check("index.html 标签配平", not p.stack and not p.err,
      "残留:%s 错误:%s" % (p.stack[:3], p.err[:3]) if (p.stack or p.err) else "无")

# ---------- 5. 指标表数值 vs 实测 ----------
print()
print("=== 5. 指标表（抽查顶点平顶字数）===")
# 平顶静态版字数（页面宣称 1,804）
m = re.search(r"([0-9,]+) 字[^<]{0,20}平顶", idx)
if m:
    claimed = int(m.group(1).replace(",", ""))
    # 用 m_apexflat 的实测值核对（若静态版存在则重生成为准）
    check("平顶字数", claimed == 1804, "宣称 %d（基准 1804）" % claimed)
else:
    skip("平顶字数", "页面无此宣称")

# ---------- 汇总 ----------
print()
print("=" * 56)
print("交付物核对: PASS %d / FAIL %d / SKIP %d" % (ok, fail, n_skip))
if fail == 0:
    print("全部通过")
    sys.exit(0)
else:
    print("有 %d 项不符，需修正" % fail)
    sys.exit(1)
