#!/usr/bin/env python3
"""m_digitnine - 把数字 9 换成 Mona 版本（与其他数字统一来源）

问题: 0-8 已从 Mona 注入，但 9 仍是 SHS 原版
  我们 9  面积 143766  adv 555   <- SHS
  Mona 9  面积 167141  adv 628
  -> 9 比相邻数字偏细偏窄 14%

🔴 关键坑: Mona 的 nine 是「six 上下翻转」的复合字形
  RecordingPen      -> 1 个 addComponent，contours_from_pen 得 0 个轮廓
  DecomposingRecordingPen -> 18 个真实操作，得 2 个轮廓
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R26')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R27')
MONA = '/workspace/wdsans/ref/mona/MonaSansVF.ttf'
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}


def mona_glyph(ch, wght):
    f = TTFont(MONA)
    f = instantiateVariableFont(f, {"wght": wght}, inplace=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    gn = cm[ord(ch)]
    rp = DecomposingRecordingPen(gs)
    gs[gn].draw(rp)
    adv = f["hmtx"][gn][0]
    f.close()
    return contours_from_pen(rp.value), adv


def main():
    os.makedirs(OUTD, exist_ok=True)
    for tag in ["250", "400", "900"]:
        w = int(tag)
        Cm, adv = mona_glyph("9", w)
        if not Cm:
            print("  %s档: 轮廓为空，跳过" % tag); continue
        src = os.path.join(SRC, FN[tag])
        f = TTFont(src)
        cm = f.getBestCmap()
        cff2 = f["CFF2"].cff
        td = cff2[cff2.fontNames[0]]
        csT = td.CharStrings
        hmtx = f["hmtx"]
        gn = cm[ord("9")]
        old = csT[gn]
        csT[gn] = make_charstring(Cm, old.private, old.globalSubrs)
        lsb = hmtx[gn][1]
        hmtx[gn] = (adv, lsb)
        f["post"].formatType = 3.0
        f["post"].glyphOrder = None
        f.save(os.path.join(OUTD, FN[tag]))
        f.close()
        print("  %s档: nine <- Mona  adv=%d  轮廓=%d" % (tag, adv, len(Cm)), flush=True)
    print("done")


if __name__ == "__main__":
    main()
