"""构建入口。

  python -m wds.build --out /data/build-cache/wdsans-p0/wdsans-vf.ttf [--subset 67] [--gates]

流程：
  Noto VF → 重设轴 (250,400,900) → [可选子集] → 改 delta → 写盘 → 跑闸门
"""
from __future__ import annotations
import argparse
import os
import sys

from fontTools.ttLib import TTFont
from fontTools import subset

from .base import SRC, STOPS, rebase_axis
from . import delta as D

# P0 试验田：一批覆盖典型笔画角色的字（来自旧版 issue 与 DESIGN 样例）
TRIAL = (
    "永国口明湖烟电直骨次令的霞葭坝扒断川三王"
    "一日目田由甲申里重垂卓桌卜"
    "人入八乂义大天太夫矢失"
    "小少尔尘尖尚当常掌"
    "月用甩甫甬角解觸"
    "非韭悲辈排徘扉"
    "己已巳巴包句包也"
    "几九凡丸旭夙"
    "匚匸区匹巨匠匣"
    "家安宁定宝室"
)


def make_subset(font: TTFont, text: str) -> TTFont:
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.name_legacy = True
    opts.notdef_outline = True
    opts.recalc_bounds = False
    opts.drop_tables = []
    sub = subset.Subsetter(options=opts)
    sub.populate(text=text)
    sub.subset(font)
    return font


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--subset", action="store_true", help="只保留试验田字形")
    ap.add_argument("--lo", type=int, default=250)
    ap.add_argument("--def", dest="df", type=int, default=400)
    ap.add_argument("--hi", type=int, default=900)
    ap.add_argument("--gates", action="store_true")
    args = ap.parse_args(argv)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    print(f"[1/4] 载入基座 {SRC}")
    font = TTFont(SRC)

    print(f"[2/4] 重设 wght 轴 = ({args.lo}, {args.df}, {args.hi})")
    font = rebase_axis(font, args.lo, args.df, args.hi)
    for a in font["fvar"].axes:
        print(f"      axis {a.axisTag}: {a.minValue} / {a.defaultValue} / {a.maxValue}")

    if args.subset:
        print(f"[3/4] 子集化到试验田（{len(set(TRIAL))} 字）")
        font = make_subset(font, TRIAL)
        print(f"      numGlyphs = {font['maxp'].numGlyphs}")

    print("[4/4] 写盘")
    font.save(args.out)
    print(f"      -> {args.out} ({os.path.getsize(args.out)/1024/1024:.1f} MB)")

    if args.gates:
        from .qa import gates
        print("\n== QA 闸门 ==")
        print(gates.g4_cmap(args.out, min_entries=len(font.getBestCmap())))
        print("G1/G2/G5 见 qa 专项脚本")


if __name__ == "__main__":
    sys.exit(main())
