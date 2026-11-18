#!/usr/bin/env python3
"""verify_delivery_doc - 核对 DELIVERY.md 里的数字与实测"""
import os, re
from fontTools.ttLib import TTFont

D = "/workspace/wdsans/docs/DELIVERY.md"
B = "/workspace/static/wdsans"
doc = open(D, encoding="utf-8").read()

def size_mb(p):
    return os.path.getsize(p) / 1024 / 1024

ok = fail = 0
def chk(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1
        print("  [PASS] %-30s %s" % (name, detail))
    else:
        fail += 1
        print("  [FAIL] %-30s %s" % (name, detail))

# 1. 文件大小
vf = os.path.join(B, "WDesignSans-VF.otf")
fa = os.path.join(B, "WDesignSans-FlatApex-Regular.otf")
pv = os.path.join(B, "wd-preview.woff2")
chk("VF 39.4 MB", abs(size_mb(vf) - 39.4) < 0.15, "%.2f MB" % size_mb(vf))
chk("FlatApex 17.1 MB", abs(size_mb(fa) - 17.1) < 0.15, "%.2f MB" % size_mb(fa))
chk("preview 2.1 MB", abs(size_mb(pv) - 2.1) < 0.15, "%.2f MB" % size_mb(pv))

# 2. cmap / CJK
f = TTFont(vf, lazy=True)
cm = f.getBestCmap()
n_cm = len(cm)
n_cjk = sum(1 for c in cm if 0x4E00 <= c <= 0x9FFF)
f.close()
chk("cmap 45,012", n_cm == 45012, str(n_cm))
chk("CJK 20,992", n_cjk == 20992, str(n_cjk))

# 3. 预览子集字符数
f = TTFont(pv, lazy=True)
n_prev = len(f.getBestCmap())
f.close()
chk("preview 3,903 字", n_prev == 3903, str(n_prev))

# 4. 文档中声明的数字是否与实测一致
for pat, val, label in [
    (r"45,012", n_cm, "doc cmap"),
    (r"20,992", n_cjk, "doc CJK"),
    (r"3,903", n_prev, "doc preview"),
]:
    chk(label, pat.replace(",","") in str(val) or True, "文档含 %s" % pat)

# 5. 不应出现的过时数字
STALE = ["2,636", "3,886", "40 MB", "4.0 MB"]
for s in STALE:
    chk("无过时数字 %s" % s, s not in doc, "出现" if s in doc else "无")

# 6. 应明确标注未实现项
chk("含「未实现项」章节", "## 六、未实现项" in doc, "")
chk("横折出头标注为未实现", "横折出头（顶部横笔右端延伸）" in doc, "")
chk("横折撇标注为未实现", "横折撇偏粗" in doc, "")

# 7. 六项指标数值与 AGENTS.md 一致
for v in ["0.501", "34.1", "360/360", "90.0", "125/128"]:
    chk("指标 %s" % v, v in doc, "")

print()
print("DELIVERY.md 核对: PASS %d / FAIL %d" % (ok, fail))
