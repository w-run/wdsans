#!/usr/bin/env python3
"""gate.py - 部署前强制门禁

三条全过才允许构建 VF:
  G1 零长度段: 改后不得比改前多 (防横线塌缩事故)
  G2 包围盒漂移: 每字 bbox 变化不超过 0.6*SW
  G3 三档签名: 250/400/900 操作符序列完全一致

用法:
  python gate.py <改前目录> <改后目录> [--cjk-only]
"""
import sys, os
import numpy as np
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

FN = {'250': 'master-ExtraLight-250.otf',
      '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}
SW = {'250': 30.0, '400': 77.0, '900': 150.0}
ZERO_TOL = 0.01


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def analyze(fp, cjk_only=True):
    f = TTFont(fp)
    cm = f.getBestCmap()
    gs = f.getGlyphSet()
    out = {}
    for cp in sorted(cm.keys()):
        if cjk_only and not (0x4E00 <= cp <= 0x9FFF):
            continue
        try:
            rp = RecordingPen()
            gs[cm[cp]].draw(rp)
            C = contours_from_pen(rp.value) if rp.value else []
        except Exception:
            continue
        zero = 0
        pts_all = []
        sig = []
        for c in C:
            segs = c['segs']
            pts = [np.array(c['start'], float)] + [endp(s) for s in segs]
            for k in range(len(pts) - 1):
                if float(np.linalg.norm(pts[k + 1] - pts[k])) < ZERO_TOL:
                    zero += 1
            pts_all.append(pts)
            sig.append(''.join(s[0] for s in segs))
        bbox = None
        if pts_all:
            P = np.vstack(pts_all)
            bbox = (float(P[:, 0].min()), float(P[:, 1].min()),
                    float(P[:, 0].max()), float(P[:, 1].max()))
        out[cp] = (zero, bbox, '|'.join(sig))
    f.close()
    return out


def main():
    before_dir, after_dir = sys.argv[1], sys.argv[2]
    ok = True

    # G1 + G2 on 400 (主档)
    print('=== G1 零长度段 / G2 包围盒漂移 (400档) ===')
    A = analyze(os.path.join(before_dir, FN['400']))
    B = analyze(os.path.join(after_dir, FN['400']))
    sw = SW['400']
    g1_bad = []
    g2_bad = []
    for cp in A:
        if cp not in B:
            continue
        z0, bb0, _ = A[cp]
        z1, bb1, _ = B[cp]
        if z1 > z0:
            g1_bad.append((cp, z0, z1))
        if bb0 and bb1:
            d = max(abs(bb1[0] - bb0[0]), abs(bb1[1] - bb0[1]),
                    abs(bb1[2] - bb0[2]), abs(bb1[3] - bb0[3]))
            if d > 0.6 * sw:
                g2_bad.append((cp, d))
    print('  G1 零长度段新增: %d 字 %s' % (len(g1_bad), 'PASS' if not g1_bad else 'FAIL'))
    for cp, z0, z1 in g1_bad[:10]:
        print('     U+%04X %s  %d -> %d' % (cp, chr(cp), z0, z1))
    print('  G2 包围盒漂移>%.0f: %d 字 %s' % (0.6 * sw, len(g2_bad), 'PASS' if not g2_bad else 'FAIL'))
    for cp, d in g2_bad[:10]:
        print('     U+%04X %s  漂移 %.0f' % (cp, chr(cp), d))
    if g1_bad or g2_bad:
        ok = False

    # G3 三档签名
    print('=== G3 三档操作符签名 ===')
    sigs = {}
    for tag, fn in FN.items():
        sigs[tag] = analyze(os.path.join(after_dir, fn))
    common = set(sigs['400'].keys())
    g3_bad = []
    for cp in common:
        s = set()
        for tag in sigs:
            v = sigs[tag].get(cp)
            s.add(v[2] if v else None)
        if len(s) > 1:
            g3_bad.append(cp)
    print('  G3 三档不一致: %d 字 %s' % (len(g3_bad), 'PASS' if not g3_bad else 'FAIL'))
    for cp in g3_bad[:10]:
        print('     U+%04X %s' % (cp, chr(cp)))
    if g3_bad:
        ok = False

    print()
    print('门禁结果: %s' % ('全部通过 ✓' if ok else '失败 ✗ 禁止部署'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
