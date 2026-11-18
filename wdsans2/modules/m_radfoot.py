#!/usr/bin/env python3
"""m_radfoot - 左偏旁底部出脚修复

## 用户需求
「都」左下「日」字形底部右侧出脚还在、没被去掉。
偏旁「口」、「日」、以及带封闭囗的部首，在左右结构时做垂直居中（已由 m_boxrad 处理），
出脚是另一个独立问题。

## 实测 (「都」400档)
```
c6  LLLLLL  x[147,471] y[-16,374]   「日」外框
c7  LLL     x[442,514] y[-60,374]   「日」右竖 -> 底 -60 比外框 -16 低 44
```
OPPO 同字该处是完整闭合方框, 无出脚; SHS 同样有出脚(我们是继承 SHS)。

## 判据
1. 存在封闭方框轮廓 (段数>=5, 宽高比 0.35~2.8, 尺寸>=100)
2. 存在竖条 (LLL/LLLL, 高>=150, 宽<=高的0.6)
3. 竖条 x 与方框右缘重叠 (x0 <= box.x1-5 且 x1 >= box.x1-120)
4. 竖条顶端与方框顶齐 (方框底-5 <= 竖条顶 <= 方框顶+5)
5. 竖条底比方框底低 20~90 (出脚范围)

对照组验证: 仰/似/倒/假/做/修/代/件/住 (亻旁, 本来就到底) 全部 0 命中

## 修法
竖条下端 -> 方框底缘 (纯点移动, 段数不变, VF 安全)
三档各自用本档的方框底缘 -> 自动跟随字重
"""
import numpy as np

NAME = "radfoot"
DESC = "左偏旁(口/日/囗)底部出脚"

MIN_FOOT = 20.0
MAX_FOOT = 90.0


def allpts(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: P.append(np.array(q, float))
        elif s[0] == "C":
            P.extend([np.array(s[1], float), np.array(s[2], float), np.array(s[3], float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1], float), np.array(s[2], float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)


def find(C):
    """返回 [(box_idx, vert_idx, target_y, cur_y), ...]"""
    if len(C) < 2:
        return []
    ps = [allpts(c) for c in C]
    gx1 = max(p[:,0].max() for p in ps)
    gx0 = min(p[:,0].min() for p in ps)
    gw = gx1 - gx0
    if gw <= 0:
        return []

    boxes = []
    for i, c in enumerate(C):
        sig = "".join(s[0] for s in c["segs"])
        if len(sig) < 5:
            continue
        p = ps[i]
        x0, x1 = p[:,0].min(), p[:,0].max()
        y0, y1 = p[:,1].min(), p[:,1].max()
        w, h = x1 - x0, y1 - y0
        if w < 100 or h < 100:
            continue
        if not (0.35 < w / h < 2.8):
            continue
        # 必须在左侧 (右缘不超过字宽 55%)
        if x1 > gx0 + gw * 0.55:
            continue
        boxes.append((i, x0, x1, y0, y1))
    if not boxes:
        return []

    res = []
    for i, c in enumerate(C):
        sig = "".join(s[0] for s in c["segs"])
        if sig not in ("LLL", "LLLL"):
            continue
        p = ps[i]
        x0, x1 = p[:,0].min(), p[:,0].max()
        y0, y1 = p[:,1].min(), p[:,1].max()
        w, h = x1 - x0, y1 - y0
        if h < 150 or w > h * 0.6:
            continue
        for bi, bx0, bx1, by0, by1 in boxes:
            if bi == i:
                continue
            # 竖条 x 与方框右缘重叠
            if x0 > bx1 - 5 or x1 < bx1 - 120:
                continue
            # 竖条顶端与方框顶齐
            if not (by0 - 5 <= y1 <= by1 + 5):
                continue
            d = by0 - y0
            if MIN_FOOT < d < MAX_FOOT:
                res.append((bi, i, by0, y0))
                break
    return res


def apply(C, hits):
    NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
    for bi, vi, target_y, cur_y in hits:
        c = NEW[vi]
        # 竖条: 找最低的那个点, 抬到 target_y
        # 竖条 = LLL 三段: start -> (x1,y1) -> (x0,y0) -> (x1,y0)
        # 需要把底部的两个点(y=cur_y)都抬到 target_y
        st = c["start"]
        if abs(st[1] - cur_y) < 2:
            c["start"] = (st[0], target_y)
        for k, s in enumerate(c["segs"]):
            ns = list(s)
            if s[0] == "L":
                e = s[1]
                if abs(e[1] - cur_y) < 2:
                    ns[1] = (e[0], target_y)
            c["segs"][k] = ns
    return NEW