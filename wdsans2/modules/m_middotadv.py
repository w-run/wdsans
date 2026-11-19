#!/usr/bin/env python3
"""m_middotadv - 修正三个中点类标点的 advance（R35）

问题: periodcentered 的 advance 从 Mona 继承为 205u，导致中文 UI 中
      「设置·消息」的间隔号两侧几乎无留白。

实测:
  字符       我们   SHS   OPPO  HOS
  U+00B7 ·   205   1000   500   500
  U+2022 •   205   1000   500  1000
  U+30FB ・  205   1000    -   1000

修正策略（取参考最低值，保守）:
  U+00B7 ·   -> 500u（OPPO/HOS 都是 500，最保守）
  U+30FB ・  -> 500u（同 U+00B7，日文窄间隔号）
  U+2022 •   -> 500u（OPPO 500，HOS/SHS 1000；取 500 保守）

为什么不动 U+2022 的墨迹大小:
  项目符号墨迹 118 vs 参考 229 确实偏小，但这是风格选择。
  本轮只修 advance（纯排版度量，零视觉风险），不动字形轮廓。
  字形改动需要新字形（占槽位），留待确认必要后再做。

三档同步: 各档按 400 档比例缩放（198/205/221 -> 同比例）
"""
import os
import sys
from fontTools.ttLib import TTFont

SRC = os.environ.get("WDS_SRC", "/workspace/wdsans2/build/masters_R34")
OUT = os.environ.get("WDS_OUT", "/workspace/wdsans2/build/masters_R35")

MASTERS = [
    ("master-ExtraLight-250.otf", 250),
    ("master-Regular-400.otf", 400),
    ("master-Heavy-900.otf", 900),
]

# 目标 advance（400 档基准）
TARGET_400 = {0x00B7: 500, 0x2022: 500, 0x30FB: 500}


def fix(path, weight, dry=False):
    f = TTFont(path)
    cm = f.getBestCmap()
    hmtx = f["hmtx"]

    # 收集需要改的 glyph
    todo = {}
    for cp, tgt in TARGET_400.items():
        if cp not in cm:
            continue
        gn = cm[cp]
        cur = hmtx[gn][0]
        # 按字重缩放：以 400 档目标为准，其他档按自身/400 比例
        if weight == 400:
            new = tgt
        else:
            ratio = weight / 400.0
            new = int(round(tgt * (0.94 + 0.06 * ratio)))
        todo[gn] = (cp, cur, new)

    if not todo:
        print("  [%d] 无匹配字符" % weight)
        f.close()
        return 0

    n = 0
    for gn, (cp, cur, new) in sorted(todo.items()):
        if dry:
            print("  [%d] U+%04X %-16s %d -> %d" % (weight, cp, gn, cur, new))
        else:
            w, lsb = hmtx[gn]
            hmtx[gn] = (new, lsb)
        n += 1

    if not dry:
        os.makedirs(OUT, exist_ok=True);
        dst = os.path.join(OUT, os.path.basename(path))
        f.save(dst)
        print("  [%d] 改 %d 个字形 -> %s" % (weight, n, dst))
    f.close()
    return n


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    print("m_middotadv: SRC=%s OUT=%s dry=%s" % (SRC, OUT, dry))
    total = 0
    for fn, w in MASTERS:
        p = os.path.join(SRC, fn)
        if not os.path.exists(p):
            print("  [%d] 文件不存在: %s" % (w, p));
            continue
        total += fix(p, w, dry)
    print("合计 %d 个字形" % total)