#!/usr/bin/env python3
"""m_barend - 横笔右端与斜边收口（消除缺口）

## 问题（用户反馈: 「多」「及」横笔右端有缺口）

「多」的结构:
  c2 横笔矩形: (770,752) (385,752) (385,685) (770,685)
  c1 外斜边:   start (734,752) -> ... -> end (770,685)

c1 的起点 (734,752) 落在 c2 上边缘 y=752 上，x=734。
c1 的终点 (770,685) 与 c2 右下角重合。
说明设计意图: 横笔上边缘只到 x=734，然后斜边从 (734,752) 出发向下到 (770,685)。

但 c2 的右上角是 (770,752)，比 734 多 36 单位。
这一段 x=734~770, y=685~752 与 c1 的斜边之间形成三角形缺口。

## 判据（已验证不误伤 大/天/夫/文/父）
1. 横笔: 4 点矩形, 宽 >= 200, 高 20~120
2. 另一轮廓 P 的「端点」与横笔的某个角点重合（容差 8）
3. P 的另一端 y 落在横笔的上边缘或下边缘（容差 8）
4. 该端 x 与横笔对应角的 x 相差 10~120（有内收空间）

## 修法
把横笔那个超出的角点，内收到 P 端点在该 y 的 x 位置。
只移动一个点 -> VF 安全。
"""
import numpy as np

NAME = "barend"
DESC = "横笔右端与斜边收口"

TOL = 8.0
MIN_W = 200
MAX_H = 120
MIN_DX = 10
MAX_DX = 120


def allpts(c):
    P=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: P.append(np.array(q,float))
        elif s[0]=="C":
            P.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q":
            P.extend([np.array(s[1],float),np.array(s[2],float)])
        else:
            P.append(np.array(s[1],float))
    return np.array(P)


def bbox_of(c):
    P=allpts(c)
    return P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()


def is_rect_bar(c):
    if len(c["segs"])!=3: return False
    if any(s[0]!="L" for s in c["segs"]): return False
    x0,x1,y0,y1=bbox_of(c)
    w=x1-x0; h=y1-y0
    return w>=MIN_W and 20<=h<=MAX_H


def verts_of(c):
    """横笔的 4 个顶点（按 segs 顺序）"""
    return [np.array(c["start"],float)]+[np.array(s[1],float) for s in c["segs"]]


def find(C):
    """返回 [(bar_id, vert_idx, new_x, new_y)]"""
    out=[]
    boxes=[bbox_of(c) for c in C]
    for i,c in enumerate(C):
        if not is_rect_bar(c): continue
        bx0,bx1,by0,by1=boxes[i]
        vs=verts_of(c)
        for j,d in enumerate(C):
            if j==i or is_rect_bar(d): continue
            Pd=allpts(d)
            if len(Pd)<3: continue
            p_s=Pd[0]; p_e=Pd[-1]
            # 两个端点里，一个与横笔角点重合，另一个在横笔边上
            for anchor,other in ((p_e,p_s),(p_s,p_e)):
                # anchor 与横笔哪个顶点重合
                hit_v=None
                for vi,v in enumerate(vs):
                    if abs(anchor[0]-v[0])<=TOL and abs(anchor[1]-v[1])<=TOL:
                        hit_v=vi; break
                if hit_v is None: continue
                # 必须是右侧顶点（x 靠近 bx1）
                if abs(vs[hit_v][0]-bx1)>TOL: continue
                # other 必须落在横笔的上/下边缘
                on_top = abs(other[1]-by1)<=TOL
                on_bot = abs(other[1]-by0)<=TOL
                if not (on_top or on_bot): continue
                # 要修改的顶点: 与 other 同一条边、且在右侧（x 靠近 bx1）
                target_y = by1 if on_top else by0
                if abs(vs[hit_v][1]-target_y)<=TOL:
                    continue   # 同一条边，无缺口
                # 找该边上右侧的顶点
                tv=None
                for vi2,v2 in enumerate(vs):
                    if abs(v2[1]-target_y)>TOL: continue
                    if abs(v2[0]-bx1)>TOL: continue
                    tv=vi2; break
                if tv is None: continue
                dx=vs[tv][0]-other[0]
                if not (MIN_DX <= dx <= MAX_DX): continue
                out.append((i, int(tv), float(other[0]), float(target_y)))
                break
    return out


def apply(C, hits):
    NEW=[]
    for c in C:
        NEW.append({"start":c["start"],"segs":[list(s) for s in c["segs"]]})
    for bar_id, vi, nx, ny in hits:
        c=NEW[bar_id]
        if vi==0:
            c["start"]=(nx,ny)
        else:
            s=list(c["segs"][vi-1])
            s[1]=(nx,ny)
            c["segs"][vi-1]=s
    return NEW
