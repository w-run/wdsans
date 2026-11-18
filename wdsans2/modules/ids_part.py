#!/usr/bin/env python3
# ids_part - 从 IDS 提取部件, 判断哪些字的横折撇属于同一部件
#
# 思路: 「多」= ⿱夕夕 -> 一个「夕」内部的横折撇是有意连接
#       「水」= ⿲㇇亅⿺乀丿 -> 笔画级分解, 横和撇是独立笔画
import re, json

IDS = "/workspace/wdsans2/ref_ids/ids.txt"

# 结构记号
OPS = set("\u2ff0\u2ff1\u2ff2\u2ff3\u2ff4\u2ff5\u2ff6\u2ff7\u2ff8\u2ff9\u2ffa\u2ffb")
# 笔画符号 (CJK 笔画区 U+31C0-U+31EF 及 ㇇ 等)
STROKE_BASE = 0x31C0

def is_stroke(ch):
    cp = ord(ch)
    return 0x31C0 <= cp <= 0x31EF or cp in (0x3005,)

data = {}
with open(IDS, encoding="utf-8") as f:
    for ln in f:
        if ln.startswith("#"): continue
        p = ln.rstrip("\n").split("\t")
        if len(p) < 3: continue
        code, ch, ids = p[0], p[1], p[2]
        if not code.startswith("U+"): continue
        try: cp = int(code[2:], 16)
        except: continue
        if not (0x4E00 <= cp <= 0x9FFF): continue
        data[cp] = (ch, ids)

print("IDS 收录 CJK: %d 字" % len(data))

# 分类: 含有笔划级分解 vs 部件级分解
stroke_level = []; part_level = []
for cp,(ch,ids) in data.items():
    n_stroke = sum(1 for c in ids if is_stroke(c))
    if n_stroke >= 2:
        stroke_level.append(cp)
    elif n_stroke == 0 and any(c in OPS for c in ids):
        part_level.append(cp)

print("笔画级分解(不能安全改横折撇): %d 字" % len(stroke_level))
print("  样例: " + "".join(chr(c) for c in stroke_level[:40]))
print()
print("部件级分解(可安全改): %d 字" % len(part_level))
print()
# 关键检验
print("关键检验:")
for ch in "多水及予了乃刀力永夕":
    cp = ord(ch)
    if cp in data:
        _, ids = data[cp]
        ns = sum(1 for c in ids if is_stroke(c))
        kind = "笔画级" if ns>=2 else ("部件级" if ns==0 else "混合")
        print("  %s  %-20s 笔画数=%d  %s" % (ch, ids, ns, kind))
    else:
        print("  %s  未收录" % ch)

json.dump({"stroke": stroke_level, "part": part_level}, open("/workspace/wdsans2/build/ids_kind.json","w"))