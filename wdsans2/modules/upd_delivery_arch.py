#!/usr/bin/env python3
P = "/workspace/wdsans/docs/DELIVERY.md"
s = open(P, encoding="utf-8").read()
before = s

# 1) 存档表加 v261120
old = "| v261119 | R34（+ m_radfoot）| 111 MB | static/wdsans/archive/v261119/ |"
new = ("| v261120 | R35（+ m_middotadv）| 111 MB | static/wdsans/archive/v261120/ |\n"
       "| v261119 | R34（+ m_radfoot）| 111 MB | static/wdsans/archive/v261119/ |")
if old in s:
    s = s.replace(old, new)
    print("存档表已加 v261120")

# 2) FlatApex 大小更新（17,915,632 -> 17,915,460）
s = s.replace("17,915,632 B (17.1 MB)", "17,915,460 B (17.1 MB)")
s = s.replace("2,247,784 B (2.1 MB)", "2,247,204 B (2.1 MB)")

# 3) 回滚命令改成 v261120
s = s.replace("cp archive/v261119/", "cp archive/v261120/")
s = s.replace("archive/v261119/WDesignSans-VF.otf", "archive/v261120/WDesignSans-VF.otf")

open(P, "w", encoding="utf-8").write(s)
print("改动:", s != before)

# 核对
c = open(P, encoding="utf-8").read()
print();
print("v261120 出现:", c.count("v261120"), "次")
print("v261119 残留（回滚段应无）:", c.count("archive/v261119"))