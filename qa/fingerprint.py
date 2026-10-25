#!/usr/bin/env python3
"""字形拓扑指纹与退化检测。

核心思路：**视觉感受必须翻译成可计算量**。
每个字形算一份指纹（轮廓数、段类型计数、bbox、面积、绕向），
与参考字体逐码位比对，任何变化都必须能被解释。

用法:
    python3 qa/fingerprint.py --ref ref/shs/shs-400.otf \
                              --cur build/v1/meta/WDesignSans-Regular.otf \
                              --report build/qa/regular.json [--limit 3000]

指纹字段全部与渲染无关，只依赖轮廓数据本身。
"""
import argparse
import json
import os
import sys
from collections import Counter

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen


def fingerprint(glyphSet, gname):
    """返回单个字形的拓扑指纹。任一环节失败返回 None。"""
    pen = RecordingPen()
    try:
        glyphSet[gname].draw(pen)
    except Exception:
        return None

    lines = curves = qcurves = 0
    sharp = 0          # 明显弯曲的曲线（控制点偏离弦 > 5 单位）
    last = None
    for op, args in pen.value:
        if op in ('moveTo', 'lineTo') and args:
            last = args[-1]
        elif op == 'curveTo' and args:
            curves += 1
            p0, p1, p2, p3 = last, args[0], args[1], args[2]
            if p0:
                dx, dy = p3[0] - p0[0], p3[1] - p0[1]
                L = (dx * dx + dy * dy) ** 0.5 or 1.0
                d1 = abs((p1[0] - p0[0]) * dy - (p1[1] - p0[1]) * dx) / L
                d2 = abs((p2[0] - p0[0]) * dy - (p2[1] - p0[1]) * dx) / L
                if max(d1, d2) > 5:
                    sharp += 1
            last = p3
        elif op == 'qCurveTo' and args:
            qcurves += 1
            last = args[-1]
    contours = sum(1 for op, _ in pen.value if op == 'moveTo')

    bp = BoundsPen(glyphSet)
    try:
        glyphSet[gname].draw(bp)
    except Exception:
        return None
    ap = AreaPen(glyphSet)
    try:
        glyphSet[gname].draw(ap)
    except Exception:
        return None

    bbox = list(bp.bounds) if bp.bounds else [0, 0, 0, 0]
    return {
        'contours': contours,
        'lines': lines,
        'curves': curves + qcurves,
        'sharp': sharp,
        'area': round(abs(ap.value), 1),
        'winding': 'cw' if ap.value < 0 else ('ccw' if ap.value > 0 else 'flat'),
        'bbox': [round(v, 1) for v in bbox],
        'w': round(bbox[2] - bbox[0], 1),
        'h': round(bbox[3] - bbox[1], 1),
    }


def compare(ref, cur):
    """返回 (级别, [问题描述])。级别: critical / warn / ok"""
    issues = []
    if cur['contours'] != ref['contours']:
        issues.append(f"轮廓数 {ref['contours']}->{cur['contours']}")

    # 只有"明显弯曲的曲线"被拉直才算真实退化；近直线被优化掉是无损的
    loss = ref['sharp'] - cur['sharp']
    if loss >= 3:
        issues.append(f'显著曲线丢失 {loss} 条（{ref["sharp"]}->{cur["sharp"]}）')
    elif loss > 0:
        issues.append(f'显著曲线丢失 {loss} 条')

    if ref['area'] > 0:
        d = abs(cur['area'] - ref['area']) / ref['area'] * 100
        if d > 8:
            issues.append(f'面积差 {d:.1f}%')
        elif d > 4:
            issues.append(f'面积差 {d:.1f}%')

    dw = abs(cur['w'] - ref['w'])
    dh = abs(cur['h'] - ref['h'])
    if dw > 12 or dh > 12:
        issues.append(f'bbox 偏差 w{dw:.0f} h{dh:.0f}')

    if cur['contours'] == ref['contours'] and cur['winding'] != ref['winding']:
        issues.append(f'绕向 {ref["winding"]}->{cur["winding"]}')

    if any('轮廓数' in i or '绕向' in i or
           (i.startswith('显著曲线丢失') and int(i.split()[1]) >= 3) for i in issues):
        return 'critical', issues
    return ('warn', issues) if issues else ('ok', [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', required=True)
    ap.add_argument('--cur', required=True)
    ap.add_argument('--report')
    ap.add_argument('--limit', type=int, default=0, help='只测前 N 个码位（0=全量）')
    ap.add_argument('--range', default='0x4E00-0x9FA5', help='码位范围')
    args = ap.parse_args()

    lo, _, hi = args.range.partition('-')
    lo = int(lo, 0)
    hi = int(hi, 0) if hi else lo

    ref_font = TTFont(args.ref, lazy=True)
    cur_font = TTFont(args.cur, lazy=True)
    ref_gs, cur_gs = ref_font.getGlyphSet(), cur_font.getGlyphSet()
    ref_cm, cur_cm = ref_font.getBestCmap(), cur_font.getBestCmap()

    cps = [c for c in range(lo, hi + 1) if c in ref_cm and c in cur_cm]
    if args.limit:
        cps = cps[:args.limit]

    stats = Counter()
    by_kind = Counter()
    worst = []
    total = 0
    for cp in cps:
        fr = fingerprint(ref_gs, ref_cm[cp])
        fc = fingerprint(cur_gs, cur_cm[cp])
        if fr is None or fc is None:
            stats['unreadable'] += 1
            continue
        total += 1
        level, issues = compare(fr, fc)
        stats[level] += 1
        for i in issues:
            by_kind[i.split()[0]] += 1
        if level != 'ok':
            worst.append({
                'cp': f'U+{cp:04X}', 'char': chr(cp),
                'level': level, 'issues': issues,
                'ref': fr, 'cur': fc,
            })

    worst.sort(key=lambda x: (x['level'] != 'critical', len(x['issues'])))
    summary = {
        'ref': args.ref, 'cur': args.cur,
        'total': total,
        'critical': stats['critical'],
        'warn': stats['warn'],
        'ok': stats['ok'],
        'unreadable': stats['unreadable'],
        'pct_problem': round((stats['critical'] + stats['warn']) / max(total, 1) * 100, 2),
        'kinds': dict(by_kind.most_common(12)),
        'worst': worst[:60],
    }
    print(json.dumps({k: v for k, v in summary.items() if k != 'worst'},
                     ensure_ascii=False, indent=2))
    print(f"\n最严重的前 10 个：")
    for w in worst[:10]:
        print(f"  {w['cp']} {w['char']}  [{w['level']}]  {'; '.join(w['issues'])}")

    if args.report:
        os.makedirs(os.path.dirname(args.report), exist_ok=True)
        with open(args.report, 'w') as f:
            json.dump(summary, f, ensure_ascii=False, indent=1)
        print(f'\n报告 -> {args.report}')


if __name__ == '__main__':
    main()
