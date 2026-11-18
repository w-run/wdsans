#!/usr/bin/env python3
# feature_scan - 找与 OPPO 墨量分布差异最大的字
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json

SZ = 128

def grid(path, ch, n=4):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ, SZ), 0)
    ImageDraw.Draw(img).text((SZ//8, SZ//8), ch, fill=255, font=ft)
    a = np.array(img) > 100
    if a.sum() < 20: return None
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    a = a[r[0]:r[-1]+1, c[0]:c[-1]+1]
    a = np.array(Image.fromarray((a*255).astype(np.uint8)).resize((n*8,n*8))) > 100
    v = []
    for i in range(n):
        for j in range(n):
            v.append(float(a[i*8:(i+1)*8, j*8:(j+1)*8].mean()))
    return np.array(v)

OURS = "/workspace/static/wdsans/WDesignSans-VF.otf"
OPPO = "/workspace/wdsans/ref/ops/ops-400.ttf"

COMMON = "的一是不了人我在有他这中大来上国个到说们为子和你地出道也时年得就那要下以生会自着去之过家学对可她里后小么心多天而能好都然没日于起还发成事只作当想看文无开手十用主行方又如前所本见经头面公同三已老从动两长知民样现分将外但身些与高意进把法此实回二理美点月明其种声全工己话儿者向情部正名定女问力机给等几很业最间新什打便位因重被走电四第门相次东政海口使教西再平真听世气信北少关并内加化由却代军产入先山五太水万市眼体别处总才场师书比住员九笑性通目华报立马命张活难神数件安表原车白应路期叫死常提感金何更反合放做系计或司利受光王果亲界及今京务制解各任至清物台象记边共风战干接它许八特觉望直服毛林题建南度统色字请交爱让认算论百吃义科怎元社术结六功指思非流每青管夫连远资队跟带花快条院变联言权往展该领传近留红治决周保达办运武半候七必城父强步完革深区即求品士转量空甚众技轻程告江语英基派满式李息写呢识极令黄德收脸钱党倒未持取设始版双历越史商千片容研像找友孩站广改议形委早房音火际则首单据导影失拿网香似斯专石若兵弟谁校读志飞观争究包组造落视济喜离虽坐集编宝谈府拉黑且随格尽剑讲布杀微怕母调局根曾准团段终乐切级克精哪官示冷块破假队宣续买房养春"

print("扫描 %d 字..." % len(COMMON), flush=True)
res = []
for ch in COMMON:
    try:
        a = grid(OURS, ch); b = grid(OPPO, ch)
    except Exception:
        continue
    if a is None or b is None: continue
    d = float(np.abs(a-b).sum())
    res.append((d, ch))
res.sort(reverse=True)
print()
print("与 OPPO 墨量分布差异最大的 40 字:")
for d, ch in res[:40]:
    print("  %s %.2f" % (ch, d))
print()
vals = [x[0] for x in res]
print("差异分布: 中位 %.2f 均值 %.2f" % (float(np.median(vals)), float(np.mean(vals))))
json.dump(res, open("/workspace/wdsans2/build/feat_scan.json","w"), ensure_ascii=False)