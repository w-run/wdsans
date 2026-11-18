#!/usr/bin/env python3
# guard_modules - 给所有 m_*.py 模块加 __main__ 保护
#
# 事故背景: 2026-11-19 我 import m_by0align 时，其顶层代码立即执行，
#           把 masters_R32 的 250 档覆盖成了 R34 的内容。
#           全部 45 个模块都缺 __main__ 保护，这是系统性隐患。
#
# 做法: 找到模块末尾的「顶层执行」代码块，包进 if __name__ == "__main__":
#       保守起见只处理能被安全识别的模式，改完立即语法检查。
import os, re, ast, sys

D = "/workspace/wdsans2/modules"
SKIP = {"m_c2lift.py"}   # 已废弃，不用改

def find_main_start(src):
    """返回顶层「执行段」的起始行号（0-based），找不到返回 None。
    执行段的特征: 连续的顶层语句中，第一条形如 X = TTFont(...) / for ... / 函数调用
    """
    lines = src.split("\n")
    # 从后往前找最后一个 def/class 的结束位置
    last_def_end = 0
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)):
            last_def_end = max(last_def_end, node.end_lineno or 0)
    # 找第一个「非 import/非 assign/非 def」的顶层语句
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)):
            continue
        return node.lineno - 1
    return None

changed = []; skipped = []
for fn in sorted(os.listdir(D)):
    if not fn.startswith("m_") or not fn.endswith(".py"): continue
    if fn in SKIP: continue
    p = os.path.join(D, fn)
    src = open(p, encoding="utf-8").read()
    if "if __name__" in src:
        skipped.append((fn, "已有保护")); continue
    start = find_main_start(src)
    if start is None:
        skipped.append((fn, "无执行段")); continue
    lines = src.split("\n")
    head = lines[:start]
    body = lines[start:]
    # 去掉尾部空行
    while body and not body[-1].strip(): body.pop()
    if not body:
        skipped.append((fn, "执行段为空")); continue
    indented = ["    " + l if l.strip() else "" for l in body]
    new = head + ['if __name__ == "__main__":'] + indented + [""]
    out = "\n".join(new)
    try:
        ast.parse(out)
    except SyntaxError as e:
        skipped.append((fn, "改后语法错误 L%s" % e.lineno)); continue
    open(p, "w", encoding="utf-8").write(out)
    changed.append(fn)

print("已加 __main__ 保护: %d 个" % len(changed))
for c in changed: print("  ", c)
print()
print("跳过 %d 个:" % len(skipped))
for f, r in skipped: print("   %-24s %s" % (f, r))