#!/usr/bin/env python3
"""m_vertend - 撇/捺末端垂直平切（R41）

问题: 用户反馈「笔末平切好像没有了」。
实测: 端面凸包比 我们 1.027 / SHS 1.028 / OPPO 1.002 / HOS 1.001
      我们与 SHS 同样内凹，OPPO/HOS 是平切的垂直端面。

根因: 我们/SHS 的捺末端是一段斜向 C 曲线收尾:
  大 轮廓1: [2] C (903,-77) -> (960,-8)   dx=57 dy=69
  OPPO   : [2] L (910,-101)                dx=0  dy=66

改法: 端面段 C/Q -> 垂直 L:
  new_end = (p0.x, e.y)   保留终点 y，x 对齐起点 x

判据（严格）:
  1. 轮廓 xmax > 700        只看右侧撇/捺
  2. 段类型 C 或 Q
  3. 段长 40 <= L <= 160
  4. 方向向上 dy > 0
  5. |dx| >= 20            已经足够垂直的不改
  6. |dx| <= |dy| * 0.85   排除横笔斜切
  7. 前后段长度 >= 100      确保是端面不是中间小段

实测: 命中 7,646 字 / 8,102 段（36.4%）
      对照组 21 字（口回十中申甲田日国目一二三工王土士干平正生）0 命中
      曲线占比 34.51% -> 33.77%（-0.74pp，SHS 32.02%，仍在门禁内）

🔴 三档一致性: C->L 改变段类型签名，三档必须用同一 (轮廓索引,段索引)。
   400 档检测 -> 索引 JSON -> 三档应用。
"""
import os, sys, json
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import numpy as np

SRC = os.environ.get("WDS_SRC", "/workspace/wdsans2/build/masters_R37")
OUT = os.environ.get("WDS_OUT", "/workspace/wdsans2/build/masters_R41")
IDX = os.environ.get("WDS_IDX", "/workspace/wdsans2/build/vertend_idx.json")

MASTERS = [
    ("master-ExtraLight-250.otf", 250),
    ("master-Regular-400.otf", 400),
    ("master-Heavy-900.otf", 900),
]

MAXR = 0.85
MIN_DX = 20
MINLEN = 40
MAXLEN = 160
MIN_NEIGHBOR = 100


def seg_starts(c):
    segs = c["segs"]; st = [c["start"]]
    for s in segs[:-1]:
        if s[0] == "L": st.append(s[1])
        elif s[0] == "C": st.append(s[3])
        elif s[0] == "Q": st.append(s[2])
        elif s[0] == "QM": st.append(s[1][-1])
    return st


def slen(segs, st, j):
    s = segs[j]
    if s[0] == "L": e = s[1]
    elif s[0] == "C": e = s[3]
    elif s[0] == "Q": e = s[2]
    else: return 0.0
    return float(np.linalg.norm(np.array(e, dtype=float) - np.array(st[j], dtype=float)))


def detect(C):
    """返回 [(ci, j)] 端面段位置"""
    hits = []
    for ci, c in enumerate(C):
        segs = c["segs"]; N = len(segs)
        if N < 3: continue
        st = seg_starts(c)
        pts = [tuple(c["start"])]
        for s in segs:
            if s[0] == "L": pts.append(tuple(s[1]))
            elif s[0] == "C": pts.append(tuple(s[3]))
            elif s[0] == "Q": pts.append(tuple(s[2]))
            elif s[0] == "QM": pts.append(tuple(s[1][-1]))
        if max(p[0] for p in pts) < 700: continue
        for j, s in enumerate(segs):
            if s[0] not in ("C", "Q"): continue
            e = np.array(s[-1], dtype=float); p0 = np.array(st[j], dtype=float)
            v = e - p0; L = float(np.linalg.norm(v))
            if L < MINLEN or L > MAXLEN: continue
            if v[1] <= 0: continue
            if abs(v[0]) < MIN_DX: continue
            if abs(v[0]) > abs(v[1]) * MAXR: continue
            if slen(segs, st, (j-1) % N) < MIN_NEIGHBOR: continue
            if slen(segs, st, (j+1) % N) < MIN_NEIGHBOR: continue
            hits.append((ci, j))
    return hits


def build_index():
    """400 档检测，输出索引"""
    p = os.path.join(SRC, "master-Regular-400.otf")
    f = TTFont(p, lazy=True)
    cm = f.getBestCmap(); gs = f.getGlyphSet()
    idx = {}
    n_seg = 0
    for cp in cm:
        if not (0x4E00 <= cp <= 0x9FFF): continue
        gn = cm[cp]
        rp = RecordingPen()
        try: gs[gn].draw(rp)
        except Exception: continue
        C = contours_from_pen(rp.value)
        h = detect(C)
        if h:
            idx[gn] = h
            n_seg += len(h)
    f.close()
    json.dump(idx, open(IDX, "w"))
    print("索引: %d 字 / %d 段 -> %s" % (len(idx), n_seg, IDX))
    return idx


def apply_one(f, idx, dry=False):
    cm = f.getBestCmap(); gs = f.getGlyphSet()
    csT = f["CFF2"].cff.topDictIndex[0].CharStrings
    n_glyph = 0; n_seg = 0; skipped = 0
    for gn, hits in idx.items():
        if gn not in csT.keys() and gn not in cm.values():
            skipped += 1; continue
        rp = RecordingPen()
        try: gs[gn].draw(rp)
        except Exception:
            skipped += 1; continue
        C = contours_from_pen(rp.value)
        ok = True
        for ci, j in hits:
            if ci >= len(C) or j >= len(C[ci]["segs"]):
                ok = False; break
            segs = C[ci]["segs"]
            if segs[j][0] not in ("C", "Q"):
                ok = False; break
        if not ok:
            skipped += 1; continue
        for ci, j in hits:
            segs = C[ci]["segs"]
            st = seg_starts(C[ci])
            p0 = np.array(st[j], dtype=float)
            e = np.array(segs[j][-1], dtype=float)
            # 🔴 关键: 保持终点 y，x 对齐起点 x
            C[ci]["segs"][j] = ["L", (float(p0[0]), float(e[1]))]
            n_seg += 1
        if not dry:
            old = csT[gn]
            csT[gn] = make_charstring(C, old.private, old.globalSubrs)
        n_glyph += 1
    print("  应用: %d 字 / %d 段  跳过 %d" % (n_glyph, n_seg, skipped))
    return n_glyph, n_seg


def main(dry=False):
    print("m_vertend: SRC=%s OUT=%s dry=%s" % (SRC, OUT, dry))
    idx = build_index()
    if dry:
        return
    os.makedirs(OUT, exist_ok=True)
    for fn, w in MASTERS:
        p = os.path.join(SRC, fn)
        if not os.path.exists(p):
            print("  跳过 %s" % fn); continue
        f = TTFont(p)
        print("  [%d] %s" % (w, fn))
        apply_one(f, idx, dry)
        f["post"].formatType = 3.0
        f["post"].glyphOrder = None
        f.save(os.path.join(OUT, fn))
        f.close()
        print("    已保存")


if __name__ == "__main__":
    main("--dry" in sys.argv)
