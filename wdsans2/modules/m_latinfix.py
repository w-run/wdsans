#!/usr/bin/env python3
"""m_latinfix - 用 Mona 复合字形替换拉丁（i/j + 带音标）

## 问题
  Mona 的拉丁字形大量是复合字形(addComponent)：
    i  j  à  á  â  ì  ō  ǎ  é  ê ...
  当年 m_latinext/m_latinmat 注入时用 RecordingPen 拆解失败，
  这些字形退回了 SHS 版本，导致:
    1. i/j 笔画偏细（SHS 250档 i竖笔36 vs Mona 52）
    2. 带音标字形骨架与基础字母风格不一致（170个）

## 修法
  用 DecomposingRecordingPen 拆解 Mona 的复合字形，逐个注入。
  Mona 是二次曲线(Q)，需转成三次(C)以统一结构。

## 转换公式
  二次 -> 三次:
    C1 = P0 + 2/3*(Q - P0)
    C2 = P2 + 2/3*(Q - P2)
"""
import numpy as np

NAME = "latinfix"
DESC = "用 Mona 复合字形替换拉丁"


def quad_to_cubic(p0, q, p2):
    p0 = np.array(p0, float)
    q = np.array(q, float)
    p2 = np.array(p2, float)
    c1 = p0 + (q - p0) * 2.0 / 3.0
    c2 = p2 + (q - p2) * 2.0 / 3.0
    return (float(c1[0]), float(c1[1])), (float(c2[0]), float(c2[1])), (float(p2[0]), float(p2[1]))


def rp_to_C(value):
    """RecordingPen 的 value -> 统一 C 段结构
    支持 moveTo/lineTo/curveTo/qCurveTo/closePath
    qCurveTo 转为 curveTo 序列
    """
    C = []
    cur = None
    prev = None
    for op, a in value:
        if op == "moveTo":
            cur = {"start": tuple(a[0]), "segs": []}
            C.append(cur)
            prev = np.array(a[0], float)
        elif op == "lineTo":
            if cur is None:
                continue
            cur["segs"].append(("L", tuple(a[0])))
            prev = np.array(a[0], float)
        elif op == "curveTo":
            if cur is None:
                continue
            cur["segs"].append(("C", tuple(a[0]), tuple(a[1]), tuple(a[2])))
            prev = np.array(a[2], float)
        elif op == "qCurveTo":
            if cur is None:
                continue
            pts = [p for p in a if p is not None]
            if len(pts) >= 2:
                # 可能有多个 Q 点: qCurveTo(q1, q2, ..., end)
                start = prev
                for i in range(len(pts) - 1):
                    c1, c2, e = quad_to_cubic(start, pts[i], pts[i + 1])
                    cur["segs"].append(("C", c1, c2, e))
                    start = np.array(pts[i + 1], float)
                prev = start
        elif op in ("closePath", "endPath"):
            cur = None
    return [c for c in C if c["segs"]]


def instantiate_mona(wght):
    """取 Mona 指定字重的字形集"""
    from fontTools.ttLib import TTFont
    import os
    from fontTools.varLib.instancer import instantiateVariableFont
    MONA = "/workspace/wdsans/ref/mona/MonaSansVF.ttf"
    cache = "/workspace/wdsans2/tmpwork/mona_i%d.ttf" % int(wght)
    if not os.path.exists(cache):
        f = TTFont(MONA)
        inst = instantiateVariableFont(f, {"wght": wght}, inplace=False)
        inst.save(cache)
        inst.close()
        f.close()
    return cache
