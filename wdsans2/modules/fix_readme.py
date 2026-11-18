#!/usr/bin/env python3
"""fix_readme - 修正 poster/README.md 里「顶横出头」的不实表述"""
P = "/workspace/static/wdsans/poster/README.md"
s = open(P, encoding="utf-8").read()
orig = s

old = "以开源黑体为骨架，按国内主流手机系统字体的比例重做：横竖等粗、折角归正、撇捺收锋、顶横出头。"
new = "以开源黑体为骨架，按国内主流手机系统字体的比例重做：横竖等粗、折角归正、撇捺收锋。"
if old in s:
    s = s.replace(old, new)
    print("已修正：去掉「顶横出头」")

# 在「笔画」章节末尾补充诚实的未实现说明
old2 = "所有闭合部首的轮廓首末点做了对齐，全库 20,992 字无残留缝隙，\n放大到海报级字号也不出现台阶。"
new2 = ("所有闭合部首的轮廓首末点做了对齐，全库 20,992 字无残留缝隙，\n"
        "放大到海报级字号也不出现台阶。\n\n"
        "## 尚未实现\n\n"
        "- **顶横出头** 顶部横笔右端延伸。三轮自动判据（几何轮廓法）均误伤左侧偏旁的横笔，\n"
        "  最大一次误伤 1,456 字，已放弃自动方案。当前继承思源黑体的原始形态。\n"
        "  若重做需建立部件级分割，或改为逐字白名单。")
if old2 in s:
    s = s.replace(old2, new2)
    print("已补充「尚未实现」章节")

if s != orig:
    open(P, "w", encoding="utf-8").write(s)
    print("已保存")
else:
    print("未匹配")
