#!/usr/bin/env python3
"""fix_preview_claims - 修正预览页的不实陈述

问题:
1. 指标表有「横折出头 右余 90 / 已对齐」，但 m_ledge 三轮失败已彻底移除，
   该特性从未实现。实测我们右余中位 143，与 SHS 同源。
2. 简介段写「修正了 2,636 个字」，那是有问题的 m_ledge2，已废弃。
"""
import re

P = "/workspace/static/wdsans/index.html"
s = open(P, encoding="utf-8").read()
orig = s

# 1) 删掉指标表里虚报的那一行
old_row = '    <tr><td>横折出头（顶部横笔）</td><td>右余 90</td><td>右余 122</td><td>右余 0</td><td class="ok">已对齐</td></tr>\n'
if old_row in s:
    s = s.replace(old_row, '')
    print("已删除虚报的「横折出头」行")

# 2) 修正简介段
old_p = "笔画风格经过逐项量化：重心、中宫、字面比例、撇捺曲率、折角角度、笔末切角六项均与参考字体对齐；横折出头通过顶部横笔右端延伸修正了 2,636 个字。"
new_p = "笔画风格经过逐项量化：重心、中宫、字面比例、撇捺曲率、折角角度、笔末切角六项均与参考字体对齐。"
if old_p in s:
    s = s.replace(old_p, new_p)
    print("已修正简介段（去掉虚报的 2,636 字）")

# 3) 在指标表 note 里诚实补充未实现项
old_note = "撇捺展开为下半区 60/70/80% 高度处的墨迹跨度。顶点平顶见下方专项对比。"
new_note = ("撇捺展开为下半区 60/70/80% 高度处的墨迹跨度。顶点平顶见下方专项对比。<br>"
            "尚未实现：横折出头（顶部横笔右端延伸）。三轮自动判据均误伤其他部件，已放弃自动方案，"
            "当前继承思源黑体原始形态。")
if old_note in s:
    s = s.replace(old_note, new_note)
    print("已在 note 中补充未实现项说明")

if s != orig:
    open(P, "w", encoding="utf-8").write(s)
    print("已保存", P)
else:
    print("未找到匹配，未改动")
