# measure 竖横比 (stem width ratio) on R31 to verify the 1.041 claim
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

P = '/workspace/wdsans2/build/masters_R31/master-Regular-400.otf'


def allpts(c):
    Q = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: Q.append(np.array(q, float))
        elif s[0] == "C":
            Q.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
        elif s[0] == "Q":
            Q.extend([np.array(s[1],float), np.array(s[2],float)])
        else:
            Q.append(np.array(s[1], float))
    return np.array(Q)


f = TTFont(P, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()

# 十 = 横 + 竖，可直接量两者的厚度
rp = RecordingPen(); gs[cm[ord("十")]].draw(rp)
C = contours_from_pen(rp.value)
hs = []  # 横笔厚度（y 方向）
vs = []  # 竖笔厚度（x 方向）
for c in C:
    Q = allpts(c)
    w = Q[:,0].max() - Q[:,0].min()
    h = Q[:,1].max() - Q[:,1].min()
    if w > h:
        hs.append(h)
    else:
        vs.append(w)
print("十: 横笔厚 %s  竖笔厚 %s" % ([round(x,1) for x in hs], [round(x,1) for x in vs]))
if hs and vs:
    print("  横/竖 = %.3f" % (np.mean(hs)/np.mean(vs)))

# 用「口」四边量
rp = RecordingPen(); gs[cm[ord("口")]].draw(rp)
C = contours_from_pen(rp.value)
Q = allpts(C[0])
w = Q[:,0].max()-Q[:,0].min(); h = Q[:,1].max()-Q[:,1].min()
pts_sorted = Q
print("口 外框 %dx%d" % (w, h))

# 更可靠: 沿 x 扫描「十」的竖笔宽，沿 y 扫描横笔厚
from PIL import Image, ImageDraw, ImageFont
SZ = 800
ft = ImageFont.truetype(P, SZ)
img = Image.new("L", (SZ*2, SZ*2), 0)
ImageDraw.Draw(img).text((SZ//3, SZ//3), "十", fill=255, font=ft)
a = np.array(img) > 128
rows = np.where(a.any(axis=1))[0]; cols = np.where(a.any(axis=0))[0]
sub = a[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1]
H, W = sub.shape
# 竖笔：中间行的墨段宽
mid = sub[H//2]
xs = np.where(mid)[0]
runs = []
if len(xs):
    st = xs[0]; pv = xs[0]
    for x in xs[1:]:
        if x - pv > 2:
            runs.append(pv-st+1); st = x
        pv = x
    runs.append(pv-st+1)
# 横笔：中间列的墨段高
midc = sub[:, W//2]
ys = np.where(midc)[0]
runs2 = []
if len(ys):
    st = ys[0]; pv = ys[0]
    for y in ys[1:]:
        if y - pv > 2:
            runs2.append(pv-st+1); st = y
        pv = y
    runs2.append(pv-st+1)
print("位图: 中部横行墨段 %s (竖笔宽)  中列纵向墨段 %s (横笔厚)" % (runs, runs2))
if runs and runs2:
    print("  竖/横 = %.3f   横/竖 = %.3f" % (runs[0]/runs2[0], runs2[0]/runs[0]))