#!/usr/bin/env python3
"""fix_poster_claim - 修正 poster/index.html 的「顶横出头」虚报"""
P = "/workspace/static/wdsans/poster/index.html"
s = open(P, encoding="utf-8").read()
before = s

old = "<b>横竖等粗、折角归正、撇捺收锋、顶横出头</b>。"
new = "<b>横竖等粗、折角归正、撇捺收锋</b>。"
if old in s:
    s = s.replace(old, new)
    print("已去掉「顶横出头」")

if s != before:
    open(P, "w", encoding="utf-8").write(s)
    print("已保存")
else:
    print("未匹配")

# 核对
c = open(P, encoding="utf-8").read()
print("残留「顶横出头」:", "顶横出头" in c)
print("残留「横折出头」:", "横折出头" in c)
