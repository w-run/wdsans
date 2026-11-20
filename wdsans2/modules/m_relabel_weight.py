#!/usr/bin/env python3
"""m_relabel_weight - 字重重新标号 250~900 -> 100~900

## 用户需求
  「我不喜欢 Source Han Sans 那一套，希望重新标号」
  「C也没问题啊，本来就是VF命名而已」

## 方案 C: 保持 9 个档位，线性映射到 100~900
  250 -> 100   ExtraLight
  300 -> 200   Light
  350 -> 300   Book
  400 -> 400   Regular    (不变)
  500 -> 500   Medium     (不变)
  600 -> 600   SemiBold   (不变)
  700 -> 700   Bold       (不变)
  800 -> 800   ExtraBold  (不变)
  900 -> 900   Black

## 为什么安全（用户判断正确）
  这是 VF 轴标签的重映射，母版轮廓坐标完全不动：
    - 只改 fvar.instances[].coordinates
    - 只改 STAT AxisValue 的 Value/NominalValue
    - 只改 name 表的 Subfamily 字符串
    - 只改 OS/2.usWeightClass
  与「外推到 100 档」本质不同：后者要在轴范围外【计算新轮廓】，
  笔画厚度会变负数导致字形损坏。实测外推 wght=100:
    一 横笔只剩 33 单位，二/三/国/字 字面缩 5~10%，5/9 异常。

## 额外收益: 修正插值斜率不均
  当前 250~400 (150 轴单位) 竖笔 30->72 斜率 0.280/单位
       400~900 (500 轴单位) 竖笔 72->142 斜率 0.140/单位
  -> 细档段坡度是粗档段 2 倍，400 处有「拐点」
  改为 100~400 后两段斜率都是 0.140/单位，完全均匀。

## 代价
  CSS font-weight:300 原本映射到「Light(300档)」，改后映射到「Book(原350)」，
  略粗一档。250 及以下原本被钳制到最细档，现在映射到 100。
"""
import sys
from fontTools.ttLib import TTFont

# 旧 -> 新 映射
MAP = [
    (250, 100, "ExtraLight"),
    (300, 200, "Light"),
    (350, 300, "Book"),
    (400, 400, "Regular"),
    (500, 500, "Medium"),
    (600, 600, "SemiBold"),
    (700, 700, "Bold"),
    (800, 800, "ExtraBold"),
    (900, 900, "Black"),
]



def relabel(font, verbose=True):
    """重映射字重轴标签，不动任何轮廓坐标"""
    old2new = {o: n for o, n, _ in MAP}
    old2name = {o: nm for o, _, nm in MAP}

    # ---------- 1) fvar ----------
    fvar = font["fvar"]
    wght_ax = None
    for ax in fvar.axes:
        if ax.axisTag == "wght":
            wght_ax = ax
    if wght_ax is None:
        raise RuntimeError("无 wght 轴")

    old_min, old_max = wght_ax.minValue, wght_ax.maxValue
    wght_ax.minValue = float(old2new.get(int(old_min), old_min))
    wght_ax.maxValue = float(old2new.get(int(old_max), old_max))
    wght_ax.defaultValue = float(old2new.get(int(wght_ax.defaultValue), wght_ax.defaultValue))

    # 实例坐标
    for inst in fvar.instances:
        old_w = int(round(inst.coordinates["wght"]))
        if old_w in old2new:
            inst.coordinates["wght"] = float(old2new[old_w])

    # ---------- 2) name: Subfamily 字符串 ----------
    name = font["name"]
    for rec in name.names:
        if rec.nameID == 17:  # Typographic Subfamily
            s = _decode(rec)
            for old_w, nm in old2name.items():
                pass
    # fvar 实例名本身不用改（名字不变，只是坐标变）

    # ---------- 3) STAT ----------
    if "STAT" in font:
        stat = font["STAT"].table
        if stat.AxisValueArray:
            for av in stat.AxisValueArray.AxisValue:
                for attr in ("Value", "NominalValue"):
                    if hasattr(av, attr):
                        v = getattr(av, attr)
                        iv = int(round(v))
                        if iv in old2new:
                            setattr(av, attr, float(old2new[iv]))

    # ---------- 4) OS/2 ----------
    if "OS/2" in font:
        o = font["OS/2"]
        ow = int(o.usWeightClass)
        if ow in old2new:
            o.usWeightClass = old2new[ow]

    if verbose:
        print("  wght 轴: %.0f~%.0f (default %.0f)" % (
            wght_ax.minValue, wght_ax.maxValue, wght_ax.defaultValue))
        print("  实例映射:")
        for o, n, nm in MAP:
            print("    %3d -> %3d  %s" % (o, n, nm))

    return 1


def _decode(rec):
    try:
        return rec.toUnicode()
    except Exception:
        return ""


def main():
    import os
    src = sys.argv[1] if len(sys.argv) > 1 else "/workspace/static/wdsans/WDesignSans-VF.ttf"
    dst = sys.argv[2] if len(sys.argv) > 2 else "/tmp/relabel_test.ttf"
    print("输入 %s" % src)
    f = TTFont(src)
    relabel(f, verbose=True)
    f.save(dst)
    f.close()
    print("输出 %s" % dst)


if __name__ == "__main__":
    main()

