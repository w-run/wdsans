#!/usr/bin/env python3
"""从 TTF（二次曲线）直接提取字形模型。

二次 → 三次的精确转换（每段）：
    P0(on), P1(off), P2(on)
      C1 = P0 + 2/3 (P1 - P0)
      C2 = P2 + 2/3 (P1 - P2)
这样曲线数量不变、形状精确，能继续复用现有 GlyphModel（三次语义）。

TrueType 的 qCurveTo 里 `None` 表示隐含中点（两个控制点之间那个 on 点）。

用法:
    python3 wds_py/extract_models.py --weight Regular \
        --src ref/nsc/NotoSansSC-400.ttf \
        --out vendor/build-data/models/shs-sc/Regular --jobs 12
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'vendor', 'glow-src', 'src', 'cv'))

from fontTools.pens.recordingPen import RecordingPen  # noqa: E402
from fontTools.ttLib import TTFont                      # noqa: E402
from glyph_model import GlyphModel                      # noqa: E402

GID_DIR = os.path.join(ROOT, 'vendor', 'glow-src', 'encoding', 'gid', 'shs-sc-han')
_CACHE = {}


def _expand_qcurve(args, start):
    """把一次 qCurveTo 展开成若干段 (P0, ctrl, P2)，None 用中点补。"""
    pts = []
    cur_ctrl = None
    prev = start
    for a in args:
        if a is None:
            if cur_ctrl is not None:
                mid = ((prev[0] + cur_ctrl[0]) / 2, (prev[1] + cur_ctrl[1]) / 2)
                pts.append((prev, cur_ctrl, mid))
                prev = mid
                cur_ctrl = None
        else:
            if cur_ctrl is not None:
                mid = ((prev[0] + cur_ctrl[0]) / 2, (prev[1] + cur_ctrl[1]) / 2)
                pts.append((prev, cur_ctrl, mid))
                prev = mid
            cur_ctrl = a
    if cur_ctrl is not None:
        pts.append((prev, cur_ctrl, pts[-1][2] if pts else cur_ctrl))
    return pts


def to_contours(glyphset, gname):
    pen = RecordingPen()
    glyphset[gname].draw(pen)
    cs = []
    for op, args in pen.value:
        if op == 'moveTo':
            cs.append([{'x': args[0][0], 'y': args[0][1], 'on': True}])
        elif op == 'lineTo':
            cs[-1].append({'x': args[0][0], 'y': args[0][1], 'on': True})
        elif op == 'curveTo':
            for a in args[:2]:
                cs[-1].append({'x': a[0], 'y': a[1], 'on': False})
            cs[-1].append({'x': args[2][0], 'y': args[2][1], 'on': True})
        elif op == 'qCurveTo':
            p0 = (cs[-1][-1]['x'], cs[-1][-1]['y'])
            # 依次处理：最后一个是终点，前面都是控制点
            seq = list(args)
            end = seq[-1] if seq and seq[-1] is not None else p0
            ctrls = []
            prev = p0
            for a in seq[:-1]:
                if a is None:
                    if ctrls:
                        mid = ((prev[0] + ctrls[-1][0]) / 2,
                               (prev[1] + ctrls[-1][1]) / 2)
                        ctrls.append(mid)
                        prev = mid
                else:
                    ctrls.append(a)
            if not ctrls:
                cs[-1].append({'x': end[0], 'y': end[1], 'on': True})
                continue
            for c in ctrls:
                p1 = c
                p2 = end
                c1 = (p0[0] + 2 / 3 * (p1[0] - p0[0]),
                      p0[1] + 2 / 3 * (p1[1] - p0[1]))
                c2 = (p2[0] + 2 / 3 * (p1[0] - p2[0]),
                      p2[1] + 2 / 3 * (p1[1] - p2[1]))
                cs[-1].append({'x': c1[0], 'y': c1[1], 'on': False})
                cs[-1].append({'x': c2[0], 'y': c2[1], 'on': False})
                cs[-1].append({'x': p2[0], 'y': p2[1], 'on': True})
                p0 = p2
        elif op == 'closePath':
            pass
    return cs


def init(font_path):
    f = TTFont(font_path, lazy=True)
    _CACHE['gs'] = f.getGlyphSet()
    _CACHE['cm'] = f.getBestCmap()


def work(tsv):
    gs, cm = _CACHE['gs'], _CACHE['cm']
    rows = [l.split('\t') for l in open(tsv).read().split('\n') if l.strip()]
    out = {}
    err = 0
    for row in rows:
        gname, uni = row[0], (row[1] if len(row) > 1 else '')
        try:
            cp = int(uni[2:], 16)
        except (ValueError, IndexError):
            continue
        shs_name = cm.get(cp)
        if not shs_name or shs_name not in gs.keys():
            continue
        try:
            contours = to_contours(gs, shs_name)
            if not contours:
                continue
            out[gname] = GlyphModel(contours).get_model_object()
        except Exception:
            err += 1
    return os.path.basename(tsv).replace('.tsv', '.json'), out, err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--weight', required=True)
    ap.add_argument('--src', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--jobs', type=int, default=12)
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    tasks = sorted(os.path.join(GID_DIR, x) for x in os.listdir(GID_DIR)
                   if x.endswith('.tsv'))
    print(f'{a.weight}: {len(tasks)} 分片, {a.jobs} 进程', flush=True)

    t0 = time.time()
    total = 0
    errors = 0
    with mp.Pool(a.jobs, initializer=init, initargs=(a.src,)) as pool:
        for name, models, err in pool.imap_unordered(work, tasks):
            with open(os.path.join(a.out, name), 'w') as f:
                json.dump(models, f)
            total += len(models)
            errors += err
            if total % 5000 < 200:
                print(f'  累计 {total} 字形，{time.time()-t0:.0f}s', flush=True)
    print(f'{a.weight} 完成：{total} 字形（失败 {errors}），{time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
