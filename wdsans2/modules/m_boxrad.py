#!/usr/bin/env python3
"""m_boxrad - 闭口偏旁(口/日/囗/田/目)垂直调整

## 用户需求
1. 左右结构时, 闭口偏旁相对右侧主体垂直居中
2. 同时要「拉高一些」—— 偏旁本身被压扁了

## 实测 (400档, 位图归一化到 1000 upem)
```
字   R32左偏旁         SHS左偏旁        顶部差  底部差  高度差
叫   y[167,745] 578   y[ 79,749] 670    +88    -4    -92
叩   y[189,766] 577   y[ 96,766] 670    +93     0    -93
叮   y[167,749] 582   y[ 88,748] 660    +79    +1    -78
叱   y[182,737] 555   y[ 85,737] 652    +97     0    -97
昨   y[111,766] 655   y[ 30,762] 732    +81    +4    -77
晴   y[118,772] 654   y[ 36,771] 735    +82    +1    -81
暗   y[ 94,769] 675   y[ 28,767] 739    +66    +2    -72
```
规律: 底部基本不动, 顶部被压下 66~97 -> 偏旁偏矮且上移

## 切分方法 (已验证)
在 x 方向 28%~62% 找「无轮廓覆盖」的最大间隙切开, 得到左偏旁轮廓组。
x 范围与 SHS 误差 <=3 单位, 分组正确。

## 修法
对左偏旁轮廓组做垂直缩放:
  以底边为锚点, 顶部向上拉伸 HEIGHT_GAIN 比例
  然后整体平移, 使其垂直中心满足 CENTER_RATIO
只改动轮廓点坐标, 段数/操作符不变 -> VF 安全
"""
import numpy as np

NAME = "boxrad"
DESC = "闭口偏旁(口日囗田目)垂直居中+拉高"

# 垂直拉伸比例: 目标高度 = 当前高度 * (1 + GAIN)
#   实测高度差 -72~-97 (中位 -81), 当前高约 578~675
#   578 -> 670 需要 +16%,  655 -> 732 需要 +12%
# 底边下移量 (em 单位, 400档实测中位 85)
#   按字重等比缩放: 400档横笔厚 67, 故比例 = 85/67 = 1.27
BOTTOM_EXTEND = 80.0
BOTTOM_EXTEND_PER_SW = 1.27   # BOTTOM_EXTEND / 400档横笔厚

# 调整后的垂直中心相对右主体中心的偏移 (正=偏上)
#   OPPO 实测: 左偏旁中心比右主体中心高 15~36 (中位约 21)
CENTER_OFFSET = 0.0

# CENTER_OFFSET 权重: 0=完全不动(纯拉伸), 1=完全按偏移平移
# 实测底部与 SHS 已对齐(差 0~4), 故默认 0
CENTER_WEIGHT = 1.0


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


def bbox_of(c):
    P = allpts(c)
    return P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()


def split_lr(C):
    """切分左右部件

    方法: 轮廓 y 范围聚类 (主) + x 间隙 (辅)

    为什么不用纯 x 间隙: 「口/日」这类偏旁由 U形主体 + 左竖组成,
    两者在 x 投影上重叠 (如「叶」c2 x[115,373] / c3 x[75,145], 115<145),
    间隙法找不到切口。

    关键观察: 同一偏旁的多个轮廓 y 范围完全相同
      「叶」c2 y[173,734]  c3 y[173,734]   完全相同
      「昨」c5 y[111,765]  c7 y[111,766]   差 1

    做法:
      1) 按 (y0, y1) 在容差内聚类
      2) 取 x_min 最靠左、且并集宽高比合理的簇
      3) 该簇 = 左偏旁, 其余 = 右主体
    """
    ps = [allpts(c) for c in C]
    if len(ps) < 2:
        return None
    gx0 = min(p[:,0].min() for p in ps)
    gx1 = max(p[:,0].max() for p in ps)
    gw = gx1 - gx0
    if gw <= 0:
        return None

    boxes = []
    for i, p in enumerate(ps):
        boxes.append((i, p[:,0].min(), p[:,0].max(), p[:,1].min(), p[:,1].max()))

    # 1) y 范围聚类
    TOL = 4.0
    used = set()
    clusters = []
    order = sorted(boxes, key=lambda b: b[1])   # 按 x_min 左到右
    for b in order:
        if b[0] in used:
            continue
        grp = [b]
        used.add(b[0])
        for b2 in order:
            if b2[0] in used:
                continue
            if abs(b2[3] - b[3]) <= TOL and abs(b2[4] - b[4]) <= TOL:
                grp.append(b2)
                used.add(b2[0])
        clusters.append(grp)

    # 2) 选最靠左、并集合理的簇
    best = None
    for grp in clusters:
        if len(grp) < 2:
            continue
        ux0 = min(g[1] for g in grp); ux1 = max(g[2] for g in grp)
        uy0 = min(g[3] for g in grp); uy1 = max(g[4] for g in grp)
        w = ux1 - ux0; h = uy1 - uy0
        if w < 120 or h < 120:
            continue
        if not (0.30 < w / h < 2.5):
            continue
        # 必须在左侧: 并集右缘不超过字宽 52%
        if ux1 > gx0 + gw * 0.52:
            continue
        score = -ux0     # 越靠左优先
        if best is None or score > best[0]:
            best = (score, grp, ux0, ux1, uy0, uy1)

    if best is None:
        return None

    _, grp, ux0, ux1, uy0, uy1 = best
    left = sorted(g[0] for g in grp)
    right = [i for i in range(len(ps)) if i not in left]
    if not left or not right:
        return None

    # 3) 校验: 左簇并集必须有足够墨量(不是零散小笔画)
    #    用轮廓点数近似
    if len(left) > 8:
        return None
    return left, right


def find(C, target_cps=None):
    """返回需要调整的 (left_ids, right_ids) 列表; 目前只做检测, 调用方筛字表"""
    r = split_lr(C)
    if r is None:
        return []
    left, right = r
    ps = [allpts(c) for c in C]
    ly0 = min(ps[i][:,1].min() for i in left); ly1 = max(ps[i][:,1].max() for i in left)
    ry0 = min(ps[i][:,1].min() for i in right); ry1 = max(ps[i][:,1].max() for i in right)
    lh = ly1 - ly0; rh = ry1 - ry0
    if lh <= 0 or rh <= 0:
        return []
    # 偏旁高度应约为右主体的 65%~95% (方框偏旁通常较小)
    if not (0.10 < lh / rh < 0.95):
        return []
    return [(left, right, ly0, ly1, ry0, ry1)]


def apply(C, hits):
    NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
    for left, right, ly0, ly1, ry0, ry1 in hits:
        lh = ly1 - ly0
        # y 向上为正: ly0 = 底边, ly1 = 顶边
        # 轮廓级实测(400档, 左偏旁轮廓组):
        #   字   我们y[底,顶]     SHS y[底,顶]     底差(需下移)  顶差
        #   叫   y[167,745]     y[ 79,749]        +88        -4
        #   叩   y[189,766]     y[ 96,766]        +93         0
        #   叮   y[167,749]     y[ 88,748]        +79        +1
        #   叱   y[182,737]     y[ 85,737]        +97         0
        #   晴   y[118,772]     y[ 36,771]        +82        +1
        #   暗   y[ 94,769]     y[ 28,767]        +66        +2
        # 结论: 顶边几乎不动(差 0~2), 底边需下移 66~97 (中位 85)
        #       => 偏旁被压扁了, 需要「向下延伸」而非向上
        new_y1 = ly1                      # 顶边固定
        new_y0 = ly0 - BOTTOM_EXTEND      # 底边下移
        target_h = new_y1 - new_y0
        for i in left:
            c = C[i]
            def ty(v):
                return new_y0 + (v - ly0) / lh * target_h
            st = c["start"]
            NEW[i]["start"] = (st[0], ty(st[1]))
            for k, s in enumerate(c["segs"]):
                ns = list(s)
                if s[0] == "QM":
                    ns[1] = [(q[0], ty(q[1])) for q in s[1]]
                elif s[0] == "C":
                    ns[1] = (s[1][0], ty(s[1][1]))
                    ns[2] = (s[2][0], ty(s[2][1]))
                    ns[3] = (s[3][0], ty(s[3][1]))
                elif s[0] == "Q":
                    ns[1] = (s[1][0], ty(s[1][1]))
                    ns[2] = (s[2][0], ty(s[2][1]))
                else:
                    ns[1] = (s[1][0], ty(s[1][1]))
                NEW[i]["segs"][k] = ns
    return NEW