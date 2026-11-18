#!/usr/bin/env python3
"""update_archive_readme - 给 v261119 存档补入后续验证结论"""
P = "/workspace/static/wdsans/archive/v261119/README.md"
s = open(P, encoding="utf-8").read()

add = open("/tmp/arch_add.md", encoding="utf-8").read()

if "## 后续验证" not in s:
    if "## 回滚方式" in s:
        s = s.replace("## 回滚方式", add.rstrip() + "\n\n---\n\n## 回滚方式")
    else:
        s = s + add
    open(P, "w", encoding="utf-8").write(s)
    print("已更新 v261119 README")
else:
    print("已存在，跳过")

print("新行数:", len(s.split("\n")))
print("章节:", [l for l in s.split("\n") if l.startswith("## ")])