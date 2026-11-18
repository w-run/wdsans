#!/usr/bin/env python3
import os, ast

D = "/workspace/wdsans2/modules"
changed, pure, failed = [], [], []

for fn in sorted(os.listdir(D)):
    if not (fn.startswith("m_") and fn.endswith(".py")):
        continue
    p = os.path.join(D, fn)
    src = open(p, encoding="utf-8").read()
    if "__name__" in src:
        continue
    try:
        tree = ast.parse(src)
    except SyntaxError:
        failed.append((fn, "syntax"))
        continue
    last_def = 0
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            last_def = max(last_def, n.end_lineno or n.lineno)
    if last_def == 0:
        pure.append((fn, "no def"))
        continue
    exec_start = None
    for n in tree.body:
        if n.lineno <= last_def:
            continue
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.Import, ast.ImportFrom)):
            continue
        exec_start = n.lineno - 1
        break
    if exec_start is None:
        pure.append((fn, "pure module"))
        continue
    lines = src.split("\n")
    head, body = lines[:exec_start], lines[exec_start:]
    while body and not body[-1].strip():
        body.pop()
    if not any(l.strip() for l in body):
        pure.append((fn, "empty exec"))
        continue
    indented = ["    " + l if l.strip() else "" for l in body]
    out = "\n".join(head + ['if __name__ == "__main__":'] + indented + [""])
    try:
        t2 = ast.parse(out)
    except SyntaxError:
        failed.append((fn, "post syntax"))
        continue
    old_defs = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    new_defs = {n.name for n in t2.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    lost = old_defs - new_defs
    if lost:
        failed.append((fn, "lose def:" + str(lost)))
        continue
    open(p, "w", encoding="utf-8").write(out)
    changed.append((fn, len(old_defs)))

print("guarded: %d" % len(changed))
for f, nd in changed:
    print("   %-24s def=%d" % (f, nd))
print("pure(skip): %d" % len(pure))
for f, r in pure:
    print("   %-24s %s" % (f, r))
print("failed: %d" % len(failed))
for f, r in failed:
    print("   %-24s %s" % (f, r))
