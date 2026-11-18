#!/usr/bin/env python3
# ids_select - 用 Unicode IDS 筛「⿰(封闭方框部首)X」的字
#
# IDS 记号: ⿰ = 左右结构
# 封闭方框部首: 口日囗田目白甘曰四罒
import sys, re, json
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont

IDS = "/workspace/wdsans2/ref_ids/ids.txt"

# 封闭方框类部首 (作为左偏旁时)
BOX_RADICALS = set("口日囗田目白甘曰四罒申甲由电")
LR = "\u2ff0"   # ⿰ 左右
TB = "\u2ff1"   # ⿱ 上下

def parse_ids(s):
    """把 IDS 解析成树: (op, [children]) 或 单个字符"""
    s = s.strip()
    if not s: return None
    if s[0] in (LR, TB, "\u2ff2", "\u2ff3", "\u2ff4", "\u2ff5",
                "\u2ff6", "\u2ff7", "\u2ff8", "\u2ff9", "\u2ffa", "\u2ffb"):
        op = s[0]
        rest = s[1:]
        kids = []; i = 0
        while i < len(rest) and len(kids) < 3:
            ch = rest[i]
            if ch in (LR, TB, "\u2ff2", "\u2ff3", "\u2ff4", "\u2ff5",
                     "\u2ff6", "\u2ff7", "\u2ff8", "\u2ff9", "\u2ffa", "\u2ffb"):
                # 嵌套: 取到能配平的子串 (简化: 递归1层)
                sub, used = parse_ids_prefix(rest[i:])
                if sub is None: break
                kids.append(sub); i += used
            else:
                kids.append(ch); i += 1
        return (op, kids)
    return s

def parse_ids_prefix(s):
    """返回 (tree, 消耗字符数)"""
    if not s: return None, 0
    ch = s[0]
    OPS = (LR, TB, "\u2ff2", "\u2ff3", "\u2ff4", "\u2ff5",
           "\u2ff6", "\u2ff7", "\u2ff8", "\u2ff9", "\u2ffa", "\u2ffb")
    if ch in OPS:
        need = 2 if ch in (LR, TB, "\u2ff2", "\u2ff3", "\u2ff4") else 3
        kids = []; i = 1
        while len(kids) < need and i < len(s):
            sub, used = parse_ids_prefix(s[i:])
            if sub is None: break
            kids.append(sub); i += used
        return (ch, kids), i
    return ch, 1

def left_radical(tree):
    """若是 ⿰ 结构, 返回左子树最外层字符集; 否则 None"""
    if isinstance(tree, tuple) and tree[0] == LR and len(tree[1]) >= 2:
        return tree[1][0]
    return None

def outer_char(node):
    """取子树最外层那个（唯一可见）部件字符"""
    if isinstance(node, str):
        return node
    return None

sel = []
n_lr = 0
seen = set()
with open(IDS, encoding="utf-8") as f:
    for ln in f:
        if ln.startswith("#"): continue
        parts = ln.rstrip("\n").split("\t")
        if len(parts) < 3: continue
        code, char, ids = parts[0], parts[1], parts[2]
        if not code.startswith("U+"): continue
        try:
            cp = int(code[2:], 16)
        except:
            continue
        if not (0x4E00 <= cp <= 0x9FFF): continue
        if cp in seen: continue
        seen.add(cp)
        t = parse_ids(ids)
        L = left_radical(t)
        if L is None: continue
        n_lr += 1
        oc = outer_char(L)
        if oc and oc in BOX_RADICALS:
            sel.append((cp, char, ids))

print("IDS 中 ⿰ 左右结构: %d 字" % n_lr)
print("其中左偏旁为封闭方框: %d 字" % len(sel))
print("  " + "".join(s[1] for s in sel[:100]))

json.dump([s[0] for s in sel], open("/workspace/wdsans2/build/box_lr.json","w"))
print()
print("已保存 -> build/box_lr.json")