#!/usr/bin/env python3
"""m_relabel_names - 字重命名（方案1: OpenType 标准命名）

坐标已由 m_relabel_weight 改为 100~900，本模块把名称对齐：

  wght  旧名          新名（方案1）
  100   ExtraLight    Thin
  200   Light         ExtraLight
  300   Normal        Light
  400   Regular       Regular
  500   Medium        Medium
  600   SemiBold      SemiBold
  700   Bold          Bold
  800   ExtraBold     ExtraBold
  900   Heavy         Black

## STAT 说明
  [0] Format=2 Nominal=400 nameID=261 是 ElidedFallbackName（VF 规范要求），
      不是重复项。其内容也应是 Regular，与 nameID 266 一致。
"""
import sys
from fontTools.ttLib import TTFont

NAME_MAP = {
    261: "Regular",
    263: "Thin",
    264: "ExtraLight",
    265: "Light",
    266: "Regular",
    267: "Medium",
    268: "SemiBold",
    269: "Bold",
    270: "ExtraBold",
    271: "Black",
}


def relabel_names(font, verbose=True):
    nm = font["name"]
    for nid, newname in NAME_MAP.items():
        # 收集已存在的 (platformID, platEncID, langID) 组合
        combos = set()
        for rec in nm.names:
            if rec.nameID == nid:
                combos.add((rec.platformID, rec.platEncID, rec.langID))
        if not combos:
            # 若无该 nameID，用 en-US 补一条
            combos.add((3, 1, 0x409))
        for pid, eid, lid in combos:
            nm.setName(newname, nid, pid, eid, lid)
    if verbose:
        for nid in sorted(NAME_MAP):
            print("    nameID %-4d -> %s" % (nid, NAME_MAP[nid]))
    return 1


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/workspace/wdsans2/build/WD_R60.ttf"
    dst = sys.argv[2] if len(sys.argv) > 2 else "/workspace/wdsans2/build/WD_R60_named.ttf"
    print("输入 %s" % src)
    f = TTFont(src)
    relabel_names(f, verbose=True)
    f.save(dst)
    f.close()
    print("输出 %s" % dst)


if __name__ == "__main__":
    main()

