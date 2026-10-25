#!/usr/bin/env python3
"""多进程版构建：按分片分发到多个进程，主进程合并后保存。

单进程实测 144 ms/字形（iSH 的 Python 慢），31,962 字要 77 分钟；
6 进程并行后约 13 分钟。

用法:
    python3 wds_py/build_mp.py --weight Regular \
        --template build/v1/meta/WDesignSans-Regular.otf \
        --out build/py/WDesignSans-Regular.ttf [--jobs 6]
"""
import argparse
import glob
import json
import tempfile
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from glyph import restore, han_model_filter          # noqa: E402
from postfilters import (han_post_filter, round_glyph,  # noqa: E402
                         translation as pf_translation)
from build import (load_param, draw_to_pen, WEIGHT_SOURCE,  # noqa: E402
                   DATA, ROOT)

STATE = {}


def _init(param):
    STATE['filt'] = han_model_filter(param)
    STATE['post'] = han_post_filter(param)
    STATE['baseline'] = param['baseline']


def _work(args):
    """处理一个分片，返回 {模板字形名: contours}"""
    path, cp_of_bytes, tpl_cmap_bytes = args
    cp_of = json.loads(cp_of_bytes)
    tpl_cmap = {int(k): v for k, v in json.loads(tpl_cmap_bytes).items()}
    models = json.load(open(path))
    out = {}
    for gname, m in models.items():
        cp = cp_of.get(gname)
        if cp is None:
            continue
        tpl_g = tpl_cmap.get(cp)
        if tpl_g is None:
            continue
        c = restore(m, STATE['filt'])
        c = STATE['post'](c)
        out[tpl_g] = round_glyph(pf_translation(c, 0, -STATE['baseline']))
    return len(models), out


def _collect(tmpdir, idx, glyphs):
    path = os.path.join(tmpdir, f'{idx}.json')
    if not os.path.exists(path):
        return 0
    with open(path) as fp:
        d = json.load(fp)
    glyphs.update(d['out'])
    os.remove(path)
    return d['n']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--weight', default='Regular')
    ap.add_argument('--template', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--jobs', type=int, default=6)
    ap.add_argument('--shards', default='')
    a = ap.parse_args()

    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.t2CharStringPen import T2CharStringPen
    from fontTools.ttLib import TTFont

    param = load_param(a.weight)
    src = WEIGHT_SOURCE[a.weight]
    model_dir = os.path.join(DATA, 'models', 'shs-sc', src)
    files = sorted(glob.glob(os.path.join(model_dir, 'gid-*.json')))
    if a.shards:
        keep = {f'gid-{s}.json' for s in a.shards.split(',') if s.strip()}
        files = [f for f in files if os.path.basename(f) in keep]
    print(f'{a.weight}: {len(files)} 个分片, {a.jobs} 进程', flush=True)

    cmap_src = json.load(open(os.path.join(
        ROOT, 'vendor', 'glow-src', 'encoding', 'cmaps', 'shs-sc.json')))
    cp_of = {}
    for uni, g in cmap_src.items():
        try:
            cp_of[g] = int(uni[2:], 16)
        except ValueError:
            pass

    tpl = TTFont(a.template, lazy=True)
    tpl_cmap = tpl.getBestCmap()
    tpl_order = tpl.getGlyphOrder()
    tpl_hmtx = tpl['hmtx']
    tpl_os2 = tpl['OS/2']
    tpl_hhea = tpl['hhea']
    tpl_name = {r.nameID: r.toUnicode() for r in tpl['name'].names
                if r.platformID == 3 and r.langID == 0x409}

    cp_b = json.dumps(cp_of)
    cm_b = json.dumps({str(k): v for k, v in tpl_cmap.items()})
    tasks = [(f, cp_b, cm_b) for f in files]

    # iSH 的 /dev/shm 只有 64MB，multiprocessing 的 semaphore 用不了，
    # 这里手工 fork + 临时文件交换结果
    glyphs = {}
    t0 = time.time()
    done = 0
    tmpdir = tempfile.mkdtemp(prefix='wdsmp_')
    pending = []
    for i, task in enumerate(tasks):
        pid = os.fork()
        if pid == 0:
            try:
                _init(param)
                n, out = _work(task)
                with open(os.path.join(tmpdir, f'{i}.json'), 'w') as fp:
                    json.dump({'n': n, 'out': out}, fp)
            finally:
                os._exit(0)
        pending.append((i, pid))
        if len(pending) >= a.jobs:
            idx, ppid = pending.pop(0)
            os.waitpid(ppid, 0)
            done += _collect(tmpdir, idx, glyphs)
            print(f'  {done} 字形处理完, {time.time()-t0:.0f}s', flush=True)
    for idx, ppid in pending:
        os.waitpid(ppid, 0)
        done += _collect(tmpdir, idx, glyphs)
        print(f'  {done} 字形处理完, {time.time()-t0:.0f}s', flush=True)
    print(f'处理完成 {len(glyphs)} 个字形, {time.time()-t0:.0f}s', flush=True)

    use_ttf = a.out.lower().endswith('.ttf')
    order = ['.notdef'] + [g for g in tpl_order if g in glyphs]
    metrics = {'.notdef': (500, 0)}
    built = {}
    for g in order:
        if g == '.notdef':
            pen = TTGlyphPen(None) if use_ttf else T2CharStringPen(500, None)
            built[g] = pen.glyph() if use_ttf else pen.getCharString()
            continue
        adv = tpl_hmtx[g][0] if g in tpl_hmtx.metrics else 1000
        if use_ttf:
            tp = TTGlyphPen(None)
            draw_to_pen(Cu2QuPen(tp, max_err=1.0), glyphs[g])
            built[g] = tp.glyph()
        else:
            pen = T2CharStringPen(adv, None)
            draw_to_pen(pen, glyphs[g])
            built[g] = pen.getCharString()
        metrics[g] = (adv, 0)
    print(f'字形编译完成, {time.time()-t0:.0f}s', flush=True)

    fb = FontBuilder(1000, isTTF=use_ttf)
    fb.setupGlyphOrder(order)
    inv = {cp: g for cp, g in tpl_cmap.items() if g in glyphs}
    fb.setupCharacterMap(inv)
    if use_ttf:
        fb.setupGlyf(built)
    else:
        fb.setupCFF(tpl_name.get(6, 'WDesignSans'), {'FullName': tpl_name.get(4, '')},
                    built, {})
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=tpl_hhea.ascent, descent=tpl_hhea.descent,
                             lineGap=tpl_hhea.lineGap)
    fb.setupNameTable({n: tpl_name[n] for n in (1, 2, 4, 5, 6, 16, 17)
                       if n in tpl_name})
    fb.setupOS2(sTypoAscender=tpl_os2.sTypoAscender,
                sTypoDescender=tpl_os2.sTypoDescender,
                sTypoLineGap=tpl_os2.sTypoLineGap,
                usWinAscent=tpl_os2.usWinAscent,
                usWinDescent=tpl_os2.usWinDescent,
                sxHeight=tpl_os2.sxHeight, sCapHeight=tpl_os2.sCapHeight,
                usWeightClass=tpl_os2.usWeightClass, usWidthClass=5,
                fsSelection=tpl_os2.fsSelection)
    fb.setupPost()
    if len(files) == len(glob.glob(os.path.join(model_dir, 'gid-*.json'))):
        for tag in ('GSUB', 'GPOS', 'GDEF', 'BASE'):
            if tag in tpl:
                fb.font[tag] = tpl[tag]

    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    fb.save(a.out)
    print(f'-> {a.out}  {os.path.getsize(a.out)/1e6:.2f}MB  '
          f'总耗时 {time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
