#!/usr/bin/env python3
"""m_boxrad2 - 闭口偏旁拉高（修正 m_boxrad 的内横遗漏 bug）

## m_boxrad 的两个缺陷

### 缺陷1（致命）：内横轮廓被漏掉，从不移动
split_lr 按 y 范围聚类切分左右部件:
  时 的 c0 外框 y[106,756] 与 c2 左竖 y[106,756] 同簇 -> left=[0,2]
  内横 c1 y[402,469] 范围不同 -> 被归到 right=[1,3,4,5]
结果: 外框底部下移 79，内横完全没动（实测只动 1 单位）
     -> 日/目旁的格位严重不均

实测格位比例（下格/上格）:
  字    SHS    R32(改前)   R37(m_boxrad后)
  时   1.03     1.03        1.32
  明   1.03     1.04        1.36
  昭   1.03     1.04        1.32
  晴   1.16     1.17        1.47

### 缺陷2：即使内横被包含，线性拉伸也会放大横笔厚度
ty(v) = new_y0 + (v-ly0)/lh*target_h
内横自身厚度 67 会被拉成 67*(730/650)=75

## 修正做法
1. 切分后修补: 与左簇 x 范围相交的轮廓补回左簇（解决缺陷1）
2. 区分外框/内横:
     外框: y 范围最大的轮廓（顶边/底边/左右竖）
     内横: y 跨度 < BAR_MAX_H 且宽度 > 外框宽 * BAR_MIN_W_RATIO
3. 外框: 线性拉伸（顶边固定，底边下移）
   内横: 只平移中心，厚度不变（保持横笔粗细）
4. 内横的新位置按「等分格位」计算，保证格位比例与改前一致
"""
import numpy as np
import sys
sys.path.insert(0, "/workspace/wdsans2/modules")
import m_boxrad as _base

NAME = "boxrad2"
DESC = "闭口偏旁拉高（补回内横 + 保厚度）"

BOTTOM_EXTEND = 80.0
BOTTOM_EXTEND_PER_SW = 1.27
BAR_MAX_H = 130
BAR_MIN_W_RATIO = 0.45


def allpts(c):
    return _base.allpts(c)


def bbox_of(c):
    return _base.bbox_of(c)


def _patch_left(C, left, right):
    """修补 split_lr 的遗漏: 与左簇 x 范围相交的轮廓补回左簇"""
    ps = [allpts(c) for c in C]
    lx0 = min(ps[i][:,0].min() for i in left)
    lx1 = max(ps[i][:,0].max() for i in left)
    add = []
    for j in right:
        x0 = ps[j][:,0].min(); x1 = ps[j][:,0].max()
        # 完全落在左簇 x 范围内 -> 是偏旁内部笔画
        if x0 >= lx0 - 5 and x1 <= lx1 + 5:
            add.append(j)
    if not add:
        return left, right
    new_left = sorted(left + add)
    new_right = [j for j in right if j not in set(add)]
    return new_left, new_right


def split_lr(C):
    r = _base.split_lr(C)
    if r is None:
        return None
    left, right = r
    return _patch_left(C, left, right)


def find(C, target_cps=None):
    r = _base.find(C, target_cps)
    if not r:
        return []
    out = []
    for left, right, ly0, ly1, ry0, ry1 in r:
        l2, r2 = _patch_left(C, left, right)
        out.append((l2, r2, ly0, ly1, ry0, ry1))
    return out


def _map_c(c, ty):
    """对单个轮廓的所有点施加 ty"""
    nc = {"start": (c["start"][0], ty(c["start"][1])), "segs": []}
    for s in c["segs"]:
        if s[0] == "QM":
            nc["segs"].append(("QM", [(q[0], ty(q[1])) for q in s[1]]))
        elif s[0] == "C":
            nc["segs"].append(("C",
                (s[1][0], ty(s[1][1])),
                (s[2][0], ty(s[2][1])),
                (s[3][0], ty(s[3][1]))))
        elif s[0] == "Q":
            nc["segs"].append(("Q", (s[1][0], ty(s[1][1])), (s[2][0], ty(s[2][1]))))
        else:
            nc["segs"].append(("L", (s[1][0], ty(s[1][1]))))
    return nc


def apply(C, hits):
    NEW = [{"start": c["start"], "segs": list(c["segs"])} for c in C]

    for left, right, ly0, ly1, ry0, ry1 in hits:
        lh = ly1 - ly0
        if lh <= 0:
            continue
        new_y1 = ly1
        new_y0 = ly0 - BOTTOM_EXTEND
        target_h = new_y1 - new_y0

        # 找外框
        # 🔴 不能只按高度: 左竖(y 范围最大但很窄)会被误选。
        #    「时」实测 c2 左竖 h=730 w=71，c0 真外框 h=729 w=277。
        #    按包围盒面积选正确。
        boxes = []
        for i in left:
            x0, x1, y0, y1 = bbox_of(C[i])
            boxes.append((i, x0, x1, y0, y1, y1 - y0, x1 - x0))
        outer = max(boxes, key=lambda t: t[5] * t[6])
        outer_w = outer[6]

        # 内横
        bar_ids = set()
        for i, x0, x1, y0, y1, h, w in boxes:
            if i == outer[0]:
                continue
            if h < BAR_MAX_H and w > outer_w * BAR_MIN_W_RATIO:
                bar_ids.add(i)

        # 外框: 线性拉伸
        for i in left:
            if i in bar_ids:
                continue
            def ty(v):
                return new_y0 + (v - ly0) / lh * target_h
            NEW[i] = _map_c(C[i], ty)

        # 内横: 保持「相对位置比例」+ 保持厚度
        #
        # 🔴 关键发现（实测 R32/R37 对比）:
        #   时  R32: 外框 H=650, 内横相对位置 0.507（居中）
        #       R37: 外框 H=730, 内横相对位置 0.561（偏上）
        #   m_boxrad 只拉外框，内横绝对位置不变 -> 相对位置漂移
        #   -> 下格变大，日/目旁失衡
        #
        # ✅ 正确: 内横保持「相对位置比例」(bar_c-ly0)/lh，
        #   这样外框拉伸后内横按同比例跟随，格位比例严格不变。
        if bar_ids:
            for i in bar_ids:
                x0, x1, by0, by1 = bbox_of(C[i])
                bar_h = by1 - by0
                bar_c = (by0 + by1) / 2.0
                # 原相对位置（相对旧外框）
                rel = (bar_c - ly0) / lh
                # 新位置 = 新外框底部 + rel * 新高度
                new_c = new_y0 + rel * target_h
                shift = new_c - bar_c
                def ty2(val, s=shift):
                    return val + s
                NEW[i] = _map_c(C[i], ty2)

    return NEW
