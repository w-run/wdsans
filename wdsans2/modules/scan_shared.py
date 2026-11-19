#!/usr/bin/env python3
"""scan_shared - 扫描「多个码位共用同一字形」的潜在问题

背景: U+00B7 · 和 U+2022 • 共用 periodcentered，导致项目符号墨迹过小。
      这是「共用字形」这一类问题的实例。本轮找全部同类。

判据: 同一 glyph 映射到 >=2 个码位，且这些码位在语义上应有不同尺寸/形态。
      重点看: 拉丁标点区 vs 中文标点区 的交叠。
"""
from fontTools.ttLib import TTFont
import collections

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
REFS = {
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS":  "/workspace/wdsans/ref/hos/hos-400.ttf",
}

f = TTFont(VF, lazy=True)
cm = f.getBestCmap()
hmtx = f["hmtx"]

# glyph -> [codepoints]
rev = collections.defaultdict(list)
for cp, gn in cm.items():
    rev[gn].append(cp)

# 只关注 >=2 个码位的，且都在 BMP 常用区（0x20-0x2FFF）
suspicious = []
for gn, cps in rev.items():
    if len(cps) < 2:
        continue
    # 全部码位都在常用符号区
    if not all(0x20 <= c <= 0x2FFF for c in cps):
        continue
    suspicious.append((gn, sorted(cps)))

print("=== 共用字形的码位组（全部在 0x20-0x2FFF）===")
print("共 %d 组" % len(suspicious))
print()

# 取参考字体的 advance 做对比
ref_adv = {}
for name, path in REFS.items():
    try:
        rf = TTFont(path, lazy=True)
        rcm = rf.getBestCmap(); rh = rf["hmtx"]
        d = {}
        for cp in cm:
            if cp in rcm:
                d[cp] = rh[rcm[cp]][0]
        ref_adv[name] = d
        rf.close()
    except Exception as e:
        print("  %s 读取失败" % name)
