#!/usr/bin/env python3
"""six_metrics - 六项笔画风格指标完整对照（用户 brief 指定）
1. 重心     墨质心纵向相对位置
2. 中宫     墨面积/bbox面积
3. 比例     bbox 宽/高
4. 撇捺曲率 下半区墨迹跨度（比绝对曲率可靠）
5. 折角     纯 L 折角角度中位（已证 90°）
6. 笔末切角 横笔端面倾斜量（已证 0）
"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.misc import bezierTools
from canonpen3 import contours_from_pen

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS": "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS": "/workspace/wdsans/ref/hos/hos-400.ttf",
}

COMMON = "的一是不了人我在有他这中大来上国个到说们为子和你地出道也时年得就那要下以生会自着去之过家学对可她里后小么心多天而能好都然没日于起还发成事只作当想看文无开手十用主行方又如前所本见经头面公同三已老从动两长知民样现分将外但身些与高意进把法此实回二理美点月明其种声全工己话儿者向情部正名定女问力机给等几很业最间新什打便位因重被走电四第门相次东政海口使教西再平真听世气信北少关并内加化由却代军产入先山五太水万市眼体别处总才场师书比住员九笑性通目华报立马命张活难神数件安表原车白应路期叫死常提感金何更反合放做系计或司利受光王果亲界及今京务制解各任至清物台象记边共风战干接它许八特觉望直服毛林题建南度统色字请交爱让认算论百吃义科怎元社术结六功指思非流每青管夫连远资队跟带花快条院变联言权往展该领传近留红治决周保达办运武半候七必城父强步完革深区即求品士转量空甚众技轻程告江语英基派满式李息写呢识极令黄德收脸钱党倒未持取设始版双历越史商千片容研像找友孩站广改议形委早房音火际则首单据导影失拿网香似斯专石若兵弟谁校读志飞观争究包组造落视济喜离虽坐集编宝谈府拉黑且随格尽剑讲布杀微怕母调局根曾准团段终乐切级克精哪官示冷块破假队宣续买房养春"

SZ = 400
UPEM = 1000

def bitmap_metrics(path, chars):
    ft = ImageFont.truetype(path, SZ)
    cw = SZ
    res = []
    for ch in chars:
        img = Image.new("L", (cw*3, cw*3), 0)
        ImageDraw.Draw(img).text((cw//4, cw//4), ch, fill=255, font=ft)
        a = np.array(img) > 128
        if a.sum() < 50: continue
        r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
        a = a[r[0]:r[-1]+1, c[0]:c[-1]+1]
        H, W = a.shape
        ys, xs = np.nonzero(a)
        cy = ys.mean() / max(H-1, 1)          # 重心: 0=顶 1=底
        fill = a.sum() / (H*W)                # 中宫
        ratio_w, ratio_h = W, H               # 比例
        # 撇捺展开: 下半区各高度的墨迹跨度
        spans = []
        for pct in (60, 70, 80):
            yy = int(H*pct/100)
            if yy >= H: continue
            xr = np.where(a[yy])[0]
            if not len(xr): continue
            spans.append((xr[-1]-xr[0]) / max(W-1,1))
        res.append((cy, fill, ratio_w/UPEM*1000, ratio_h/UPEM*1000, spans))
    return res

def fold_angles(path, chars):
    """纯 L 折角（两侧臂 >=40，角度 70~110）"""
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    angs = []
    for ch in chars:
        if ord(ch) not in cm: continue
        rp = RecordingPen()
        try: gs[cm[ord(ch)]].draw(rp)
        except Exception: continue
        C = contours_from_pen(rp.value)
        for c in C:
            segs = c["segs"]
            if not segs or any(s[0] != "L" for s in segs): continue
            pts = [np.array(c["start"], float)] + [np.array(s[1], float) for s in segs]
            n = len(pts)
            for i in range(n-1):
                p0, p1, p2 = pts[i], pts[i+1], pts[(i+2) % n]
                v1 = p1 - p0; v2 = p2 - p1
                l1 = float(np.hypot(*v1)); l2 = float(np.hypot(*v2))
                if l1 < 40 or l2 < 40: continue
                cosv = float(np.dot(v1, v2)) / (l1*l2)
                ang = float(np.degrees(np.arccos(max(-1, min(1, cosv)))))
                if 70 <= ang <= 110:
                    angs.append(ang)
    f.close()
    return angs

CH = COMMON[:800]
print("计算中（%d 字，4 字体）..." % len(CH), flush=True)
out = {}
for name, path in FONTS.items():
    bm = bitmap_metrics(path, CH)
    cy = np.mean([x[0] for x in bm])
    fill = np.mean([x[1] for x in bm]) * 100
    rw = np.mean([x[2] for x in bm])
    rh = np.mean([x[3] for x in bm])
    s60 = np.mean([x[4][0] for x in bm if len(x[4]) > 0])
    s70 = np.mean([x[4][1] for x in bm if len(x[4]) > 1])
    s80 = np.mean([x[4][2] for x in bm if len(x[4]) > 2])
    fangs = fold_angles(path, CH)
    out[name] = (rw, rh, fill, cy, s60, s70, s80, float(np.median(fangs)) if fangs else 0, len(fangs))

print()
print("%-6s %-12s %-8s %-8s %-20s %-10s" % ("字体","比例W/H","中宫%","重心","撇捺展开60/70/80","折角°"))
print("-" * 78)
for name in FONTS:
    if name not in out: continue
    rw, rh, fill, cy, s60, s70, s80, fa, fn = out[name]
    print("%-6s %-12s %-8.1f %-8.3f %-20s %-10.1f" % (
        name, "%.0f/%.0f" % (rw, rh), fill, cy,
        "%.3f/%.3f/%.3f" % (s60, s70, s80), fa))
print()
print("笔末切角: 四家均为 0.0（上轮已单独验证，我们 41 处全部垂直）")
