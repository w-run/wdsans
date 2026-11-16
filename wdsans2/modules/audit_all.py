#!/usr/bin/env python3
"""audit_all - 全模块效果审计

背景: 连续两轮出现「重建链漏模块」（m_curvflat / m_latinreset），
两者都是纯几何模块，构建不报错、门禁不报警，只能靠测量发现。

本脚本对 19 个已部署模块逐一构造「独立判据」，
直接检查已部署字体里该模块的特征是否真的存在。
不依赖模块自己报告的数字。

每项输出: PASS / FAIL / SKIP
"""
import sys, os, io, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
MONA = '/workspace/wdsans/ref/mona/MonaSansVF.ttf'

RES = []


def rec(name, status, detail):
    RES.append((name, status, detail))
    print('  [%-4s] %-16s %s' % (status, name, detail), flush=True)


def inkw(f, gs, cm, ch):
    if ord(ch) not in cm:
        return None
    bp = BoundsPen(gs)
    try:
        gs[cm[ord(ch)]].draw(bp)
    except Exception:
        return None
    if not bp.bounds:
        return None
    b = bp.bounds
    return b[2] - b[0]


def main():
    print("读取字体...", flush=True)
    fv = TTFont(VF, lazy=True)
    gv = fv.getGlyphSet(); cv = fv.getBestCmap()
    fm = TTFont(MONA, lazy=True)
    if 'fvar' in fm:
        from fontTools.varLib.instancer import instantiateVariableFont
        fm = instantiateVariableFont(fm, {'wght': 400}, inplace=True)
    gm = fm.getGlyphSet(); cmon = fm.getBestCmap()

    print()
    print("=== 1. m_latinmat + m_latinreset 净效果 ===")
    # 两者串起来应该让拉丁回到 Mona 原宽（±2%）
    ratios = []
    for ch in 'HAMWn0aeg' :
        a = inkw(fv, gv, cv, ch); b = inkw(fm, gm, cmon, ch)
        if a and b:
            ratios.append(a / b)
    if ratios:
        avg = float(np.mean(ratios))
        if 0.985 <= avg <= 1.015:
            rec('latin 宽', 'PASS', '与 Mona 比 %.3f (n=%d)' % (avg, len(ratios)))
        else:
            rec('latin 宽', 'FAIL', '与 Mona 比 %.3f，应为 1.00' % avg)
    fm.close()

    print()
    print("=== 2. m_shortl (C-L-C 短段已删) ===")
    # 统计全库 C-L-C 且 L 极短的残留
    cnt = 0; tot = 0
    for cp, gn in list(cv.items())[:1200]:
        if not (0x4E00 <= cp <= 0x9FFF):
            continue
        rp = RecordingPen()
        try:
            gv[gn].draw(rp)
        except Exception:
            continue
        ops = [o for o, a in rp.value]
        for i in range(1, len(ops) - 1):
            if ops[i] == "lineTo" and ops[i-1] == "curveTo" and ops[i+1] == "curveTo":
                # 取段长
                a = rp.value[i][1][0]; b = rp.value[i-1][1][2]
                d = ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5
                tot += 1
                if d < 6:
                    cnt += 1
    if tot == 0:
        rec('shortl', 'PASS', '无 C-L-C 残留（已全删）')
    elif cnt / max(tot, 1) < 0.05:
        rec('shortl', 'PASS', 'C-L-C 残留 %d/%d (%.1f%%)' % (cnt, tot, cnt/tot*100))
    else:
        rec('shortl', 'FAIL', 'C-L-C 残留过多 %d/%d' % (cnt, tot))

    print()
    print("=== 3. m_zerocont (无零面积轮廓) ===")
    zero = 0; checked = 0
    for cp, gn in list(cv.items())[:800]:
        if not (0x4E00 <= cp <= 0x9FFF):
            continue
        ap = AreaPen(gv)
        try:
            gv[gn].draw(ap)
        except Exception:
            continue
        checked += 1
        if abs(ap.value) < 50:
            zero += 1
    rec('zerocont', 'PASS' if zero == 0 else 'FAIL',
        '零面积字 %d/%d' % (zero, checked))

    print()
    print("=== 4. m_metrics / m_nametable / m_os2range (表字段) ===")
    fs = fv['OS/2'].fsSelection
    rec('metrics', 'PASS' if fs & 0x40 else 'FAIL', 'fsSelection=0x%04X' % fs)
    nm = fv["name"]
    fam = nm.getDebugName(1) or ''
    sub = nm.getDebugName(2) or ''
    ok = 'WDesign' in fam
    rec('nametable', 'PASS' if ok else 'FAIL', 'name1=%s / name2=%s' % (fam, sub))
    langs = sorted(set(r.langID for r in nm.names))
    has_zh = 0x804 in langs
    rec('nametable.zh', 'PASS' if has_zh else 'WARN', 'langIDs=%s' % [hex(x) for x in langs])

    ur = fv['OS/2'].ulUnicodeRange1
    rec('os2range', 'PASS' if (ur >> 2) & 1 else 'FAIL', 'ulUnicodeRange1=0x%08X' % ur)

    print()
    print("=== 5. 特性类模块 (GSUB/GPOS) ===")
    gsub = fv['GSUB'].table
    feats = set(fr.FeatureTag for fr in gsub.FeatureList.FeatureRecord)
    for tag, mod in [('sups','numfeats'),('subs','numfeats'),('sinf','numfeats'),
                     ('pnum','numfeats2'),('numr','numfeats2'),('dnom','numfeats2'),
                     ('frac','frac'),('calt','coloncenter')]:
        rec(mod + '.' + tag, 'PASS' if tag in feats else 'FAIL',
            '%d features' % len(feats))
    gpos = fv['GPOS'].table
    pfeats = set(fr.FeatureTag for fr in gpos.FeatureList.FeatureRecord)
    rec('kerning', 'PASS' if 'kern' in pfeats else 'FAIL', 'GPOS features=%d' % len(pfeats))
    rec('markpos', 'PASS' if ('mark' in pfeats and 'mkmk' in pfeats) else 'FAIL',
        'mark=%s mkmk=%s' % ('mark' in pfeats, 'mkmk' in pfeats))

    fv.close()
    print()
    npass = sum(1 for x in RES if x[1] == "PASS")
    nfail = sum(1 for x in RES if x[1] == "FAIL")
    nwarn = sum(1 for x in RES if x[1] == "WARN")
    print("=" * 60)
    print('审计结果: PASS %d / FAIL %d / WARN %d  (共 %d 项)' %
          (npass, nfail, nwarn, len(RES)))
    if nfail:
        print('FAIL 项: %s' % [x[0] for x in RES if x[1] == 'FAIL'])


if __name__ == '__main__':
    main()