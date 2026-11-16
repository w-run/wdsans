#!/usr/bin/env python3
"""scan_struct - 全库结构异常扫描

性能关键: 字体只打开一次（原版每字重开 TTFont 极慢）。
找: 1) 轮廓数远多于 SHS  2) bbox 偏差 >15%
"""
import sys, json, time
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

OURS = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
OUT = '/workspace/wdsans2/build/scan_struct.json'


def collect(path, cps):
    """一次打开，批量取所有字形信息"""
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    res = {}
    for cp in cps:
        gn = cm.get(cp)
        if gn is None:
            continue
        rp = RecordingPen()
        try:
            gs[gn].draw(rp)
        except Exception:
            continue
        if not rp.value:
            continue
        n = sum(1 for op, a in rp.value if op == 'moveTo')
        xs = []; ys = []
        for op, args in rp.value:
            for pt in args:
                try:
                    xs.append(pt[0]); ys.append(pt[1])
                except Exception:
                    pass
        if not xs:
            continue
        res[cp] = {'n': n, 'w': max(xs) - min(xs), 'h': max(ys) - min(ys)}
    f.close()
    return res


def main():
    t0 = time.time()
    common = open('/workspace/wdsans2/data/common3500.txt', encoding='utf-8').read().strip()
    cps = [ord(c) for c in common]

    print('收集我们字体...', flush=True)
    A = collect(OURS, cps)
    print('  %d 字, %.1fs' % (len(A), time.time() - t0), flush=True)

    print('收集 SHS...', flush=True)
    B = collect(SHS, cps)
    print('  %d 字, %.1fs' % (len(B), time.time() - t0), flush=True)

    frag = []; boxdev = []
    for cp in cps:
        a = A.get(cp); b = B.get(cp)
        if not a or not b:
            continue
        if a['n'] > b['n'] + 2:
            frag.append((a['n'] - b['n'], chr(cp), a['n'], b['n']))
        if b['w'] > 100 and b['h'] > 100:
            dw = abs(a['w'] - b['w']) / b['w'] * 100
            dh = abs(a['h'] - b['h']) / b['h'] * 100
            if dw > 15 or dh > 15:
                boxdev.append((max(dw, dh), chr(cp), round(dw, 1), round(dh, 1)))

    frag.sort(reverse=True); boxdev.sort(reverse=True)
    print()
    print('=== 轮廓数比 SHS 多 3 个以上: %d 字 ===' % len(frag))
    for d, ch, an, bn in frag[:30]:
        print('  %s 我们%d SHS%d (+%d)' % (ch, an, bn, d))
    print()
    print('=== bbox 偏差 >15%%: %d 字 ===' % len(boxdev))
    for d, ch, dw, dh in boxdev[:30]:
        print('  %s 差%.1f%% (w差%.1f h差%.1f)' % (ch, d, dw, dh))
    json.dump({'frag': frag[:200], 'boxdev': boxdev[:200]}, open(OUT, 'w'))
    print()
    print('总耗时 %.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()