#!/usr/bin/env python3
# patch_ca7 - audit 增加：存档表行指向自校验 + 存档完整性
P = "/workspace/wdsans2/modules/claim_audit.py"
lines = open(P, encoding="utf-8").read().split("\n")

if any("存档表每行指向" in l for l in lines):
    print("已存在")
else:
    idx = None
    for i, l in enumerate(lines):
        if l.strip() == 'print("=" * 56)':
            j = i - 1
            while j >= 0 and lines[j].strip() == "":
                j -= 1
            idx = j
            break
    if idx is None:
        print("未找到汇总行")
    else:
        blk = [
            '# ---------- 10. 存档表自校验 ----------',
            'print()',
            'print("=== 10. 存档表 ===")',
            'DEL = "/workspace/wdsans/docs/DELIVERY.md"',
            'if os.path.exists(DEL):',
            '    dd = open(DEL, encoding="utf-8").read()',
            '    import re as _re2',
            '    rows = _re2.findall(r"\\| (v\\d{6}) \\|[^|]*\\|[^|]*\\| ([^|]+) \\|", dd)',
            '    bad = [(v, loc.strip()) for v, loc in rows if v not in loc]',
            '    check("存档表每行指向自己的目录", not bad,',
            '          ("错误: %s" % bad) if bad else "%d 行全部正确" % len(rows))',
            '    # 存档目录与 MD5 校验',
            '    ARC = "/workspace/static/wdsans/archive"',
            '    vers = sorted(d for d in os.listdir(ARC) if d.startswith("v")) if os.path.exists(ARC) else []',
            '    n_ok = 0',
            '    for v in vers:',
            '        md5f = os.path.join(ARC, v, "MD5SUMS.txt")',
            '        if not os.path.exists(md5f):',
            '            continue',
            '        n_ok += 1',
            '    check("每个存档都有 MD5SUMS", len(vers) == n_ok,',
            '          "%d/%d" % (n_ok, len(vers)))',
            '    check("存档数 >= 3", len(vers) >= 3, str(vers))',
            'else:',
            '    skip("DELIVERY.md", "不存在")',
            '',
        ]
        lines = lines[:idx] + blk + lines[idx:]
        open(P, "w", encoding="utf-8").write("\n".join(lines))
        print("已插入 %d 行" % len(blk))

import ast
try:
    ast.parse(open(P, encoding="utf-8").read()); print("语法 OK")
except SyntaxError as e:
    print("语法错误:", e)