#!/usr/bin/env python3
"""topbar_right - 实测顶部横笔右余（验证预览页的「右余 90」是否真实）"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS": "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS": "/workspace/wdsans/ref/hos/hos-400.ttf",
}

def allpts(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: P.append(np.array(q, float))
        elif s[0] == "C":
            P.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1],float), np.array(s[2],float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)

def topbar_right(C):
    """找顶部横笔（纯L、宽高比>=2.8、宽>=300），返回其右端到字面右界的余量"""
    if not C: return None
    allP = np.vstack([allpts(c) for c in C])
    gx1 = allP[:,0].max()
    for c in C:
        if any(s[0] != "L" for s in c["segs"]): continue
        P = allpts(c)
        w = P[:,0].max() - P[:,0].min()
        h = P[:,1].max() - P[:,1].min()
        if h <= 0 or w/h < 2.8 or w < 300: continue
        return gx1 - P[:,0].max()
    return None

CHARS = "各冬到理夏麦玫玖永今亨"
print("%-6s %-6s %-8s %-8s %-8s %s" % ("字","我们","SHS","OPPO","HOS","说明"))
rows = {k: [] for k in FONTS}
for ch in CHARS:
    line = [ch]
    for name, path in FONTS.items():
        f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
        v = None
        if ord(ch) in cm:
            rp = RecordingPen()
            try: gs[cm[ord(ch)]].draw(rp)
            except Exception: pass
            if rp.value:
                v = topbar_right(contours_from_pen(rp.value))
        f.close()
        rows[name].append(v)
        line.append("%.0f" % v if v is not None else "-")
    # 若我们 == SHS，说明没改
    same = (rows["我们"][-1] is not None and rows["SHS"][-1] is not None
            and abs(rows["我们"][-1] - rows["SHS"][-1]) < 2)
    line.append("与SHS相同(未改)" if same else "")
    print("%-6s %-8s %-8s %-8s %-8s %s" % (line[0], line[1], line[2], line[3], line[4], line[5]))
print()
for name in FONTS:
    vals = [v for v in rows[name] if v is not None]
    if vals:
        print("%-5s 有顶部横笔的字: 右余中位 %.0f  n=%d" % (name, float(np.median(vals)), len(vals)))
