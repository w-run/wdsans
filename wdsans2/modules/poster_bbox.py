#!/usr/bin/env python3
"""poster_bbox - 补充字形 bbox + 笔画级 radical 检测"""
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
FA = '/workspace/static/wdsans/WDesignSans-FlatApex-Regular.otf'
OUT = '/workspace/static/wdsans/poster'

f = TTFont(VF, lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()

# CJK 笔画 radical 范围检查
STROKE_CPS = list(range(0x31C0, 0x31E4)) + list(range(0x2E80, 0x2EF4)) + list(range(0x2F00, 0x2FD6))
have = [hex(c) for c in STROKE_CPS if c in cm]
print('笔画/部首字符可用数: %d' % len(have))

NEE = list("永口田王三人今合会含令全金余介企永字八法横竖撇捺折点提钩")
bbox = {}
for ch in NEE:
    cp = ord(ch)
    if cp not in cm:
        continue
    bp = BoundsPen(gs)
    gs[cm[cp]].draw(bp)
    if bp.bounds:
        b = bp.bounds
        bbox[ch] = [round(b[0],1), round(b[1],1), round(b[2],1), round(b[3],1)]
print('bbox 提取 %d 个' % len(bbox))

json.dump(bbox, open(OUT + '/bbox.json','w'), ensure_ascii=False)
f.close()

# 同时确认几个关键字的轮廓数（用于说明结构）
for ch in '永今合':
    cp = ord(ch)
    if cp in cm:
        from fontTools.pens.recordingPen import RecordingPen
        f2 = TTFont(VF, lazy=True); gs2 = f2.getGlyphSet()
        rp = RecordingPen(); gs2[cm[cp]].draw(rp); f2.close()
        n = sum(1 for op,a in rp.value if op=='moveTo')
        print('  %s 轮廓数=%d' % (ch, n))
print(json.dumps(bbox, ensure_ascii=False)[:300])