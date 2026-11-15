#!/usr/bin/env python3
"""m_latinext - 从 Mona Sans 补入 Latin Extended-A 字形

背景:
  我们字体 Latin Ext-A 只有 30/128 个，Mona 有 123 个。
  缺失的 95 个是捷克/波兰/匈牙利/土耳其等语言的必需字符。

关键约束:
  VF 已达 65,535 字形硬上限，无空余槽位。
  但有 21,189 个未映射字形（glyph#####），未被 GSUB/GPOS 引用，可安全复用。

方案:
  1. 从 Mona VF 按 250/400/900 字重实例化（wght 轴）
  2. 取缺失字符的轮廓，注入到我们字体的未映射槽位
  3. 添加 cmap 映射

注意: 用同一批槽位 → 三档结构自动一致
"""
import sys, os
import numpy as np
sys.path.insert(0,'/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from canonpen3 import contours_from_pen, make_charstring
from fontTools.varLib.instancer import instantiateVariableFont

MONA = '/workspace/wdsans/ref/mona/MonaSansVF.ttf'
UPM_SRC = None

def get_missing():
    """列出 Latin Ext-A 中我们缺失、Mona 有的码位"""
    F = '/workspace/wdsans2/build/masters_MOD12/master-Regular-400.otf'
    f = TTFont(F); cm = f.getBestCmap(); f.close()
    m = TTFont(MONA); cmm = m.getBestCmap(); m.close()
    miss = [c for c in range(0x0100, 0x0180) if c not in cm and c in cmm]
    return miss


def get_vacant_slots(n, fontpath):
    """取 n 个未映射且无 GSUB 引用的槽位"""
    f = TTFont(fontpath)
    cm = f.getBestCmap()
    mapped = set(cm.values())
    go = f.getGlyphOrder()
    vacant = [g for g in go if g not in mapped and g != '.notdef']
    f.close()
    return vacant[:n]


def glyph_contours(fontpath, gname):
    """读取字形轮廓"""
    f = TTFont(fontpath)
    gs = f.getGlyphSet()
    if gname not in gs:
        f.close(); return None
    rp = RecordingPen()
    gs[gname].draw(rp)
    C = contours_from_pen(rp.value) if rp.value else []
    w = gs[gname].width
    f.close()
    return C, w


def main():
    cps = get_missing()
    print('Latin Ext-A 待补: %d 个' % len(cps), flush=True)
    if not cps:
        return

    BASE = os.environ.get('WDS_BASE', '/workspace/wdsans2/build/masters_MOD12')
    OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD13')
    FN = {'250':'master-ExtraLight-250.otf', '400':'master-Regular-400.otf', '900':'master-Heavy-900.otf'}
    WGHT = {'250':200, '400':400, '900':900}
    os.makedirs(OUTD, exist_ok=True)

    # 预取槽位（用 400 档的顺序，三档必须相同）
    slots = get_vacant_slots(len(cps), BASE + '/' + FN['400'])
    print('复用槽位: %d 个, 例: %s' % (len(slots), slots[:3]), flush=True)

    for tag in ['250', '400', '900']:
        # 1) 实例化 Mona 到目标字重
        mv = TTFont(MONA)
        try:
            inst = instantiateVariableFont(mv, {'wght': WGHT[tag], 'wdth': 100, 'opsz': 0},
                                           inplace=False, updateFontNames=False)
        except Exception as e:
            print('  Mona 实例化失败 %s: %s' % (tag, e), flush=True)
            mv.close(); continue
        tmp = '/tmp/mona_%s.ttf' % tag
        inst.save(tmp); inst.close(); mv.close()

        mfont = TTFont(tmp)
        mcmap = mfont.getBestCmap()
        mgs = mfont.getGlyphSet()

        # 2) 打开目标字体
        f = TTFont(BASE + '/' + FN[tag])
        cm = f.getBestCmap()
        cff2 = f['CFF2'].cff
        td = cff2[cff2.fontNames[0]]
        csT = td.CharStrings
        hm = f['hmtx']

        n_ok = 0
        for cp, slot in zip(cps, slots):
            if cp not in mcmap: continue
            mgn = mcmap[cp]
            # 关键: 必须用 DecomposingRecordingPen 展开复合字形
            # RecordingPen 对复合字形只返回 1~2 个组件引用，拿不到真实轮廓
            rp = DecomposingRecordingPen(mgs)
            try:
                mgs[mgn].draw(rp)
            except Exception:
                continue
            if not rp.value: continue
            C = contours_from_pen(rp.value)
            if not C: continue
            # 3) 写入槽位
            old = csT[slot]
            csT[slot] = make_charstring(C, old.private, old.globalSubrs)
            # 4) advance width
            hm[slot] = (int(round(mgs[mgn].width)), 0)
            n_ok += 1

        # 5) 加 cmap 映射
        for table in f['cmap'].tables:
            if table.isUnicode():
                for cp, slot in zip(cps, slots):
                    if cp in mcmap:
                        table.cmap[cp] = slot

        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        out = OUTD + '/' + FN[tag]
        f.save(out)
        f.close()
        mfont.close()
        print('latinext %s: 补入 %d 字符' % (tag, n_ok), flush=True)


main()
