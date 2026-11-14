#!/usr/bin/env python3
"""run_module.py - 400 档驱动的通用模块执行器

VF 构建要求三档段数与操作符完全一致。若每档独立检测，粗档笔画宽会
让阈值失衡、命中集不同 -> VarLibCFFPointTypeMergeError。
所以一律: 在 400 档检测, 索引套用到三档。

用法:
  python run_module.py <模块> detect                     # 400档检测, 写索引json
  python run_module.py <模块> apply <tag> [index.json]   # 按索引改某一档
  python run_module.py <模块> all                        # detect + 三档 apply
  python run_module.py <模块> one <tag> <字>             # 单字调试(独立检测)

环境变量:
  WDS_BASE  基座目录 (默认 build/masters_T6)
  WDS_OUT   输出目录 (默认 build/masters_MOD)
"""
import sys
import os
import json
import importlib

sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SW = {'250': 30.0, '400': 77.0, '900': 150.0}
FN = {'250': 'master-ExtraLight-250.otf',
      '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}

BASE = os.environ.get('WDS_BASE', '/workspace/wdsans2/build/masters_T6')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD')
INDEX_PATH = os.environ.get('WDS_INDEX', '/workspace/wdsans2/build/index.json')


def load_font(tag):
    f = TTFont(BASE + '/' + FN[tag])
    cm = f.getBestCmap()
    gs = f.getGlyphSet()
    cff2 = f['CFF2'].cff
    td = cff2[cff2.fontNames[0]]
    return f, cm, gs, td.CharStrings


def get_contours(gs, cm, cp):
    gn = cm.get(cp)
    if not gn:
        return None, None
    rp = RecordingPen()
    gs[gn].draw(rp)
    if not rp.value:
        return gn, []
    return gn, contours_from_pen(rp.value)


def do_detect(mod):
    """在 400 档检测, 输出 {cp: hits_json}"""
    f, cm, gs, csT = load_font('400')
    cps = [cp for cp in sorted(cm.keys()) if 0x4E00 <= cp <= 0x9FFF]
    out = {}
    for cp in cps:
        gn, C = get_contours(gs, cm, cp)
        if not C or len(C) < 2:
            continue
        try:
            hits = mod.find(C, SW['400'])
        except Exception:
            continue
        if not hits:
            continue
        out[str(cp)] = [list(h) for h in hits]
    f.close()
    os.makedirs(os.path.dirname(INDEX_PATH) or '.', exist_ok=True)
    with open(INDEX_PATH, 'w') as fh:
        json.dump({'module': mod.NAME, 'sw': SW['400'], 'hits': out}, fh)
    print('%s detect: %d 字 -> %s' % (mod.NAME, len(out), INDEX_PATH), flush=True)
    return out


def do_apply(mod, tag, index):
    f, cm, gs, csT = load_font(tag)
    n = 0
    miss = 0
    for cp_s, hits in index.items():
        cp = int(cp_s)
        gn, C = get_contours(gs, cm, cp)
        if not C or len(C) < 2:
            miss += 1
            continue
        try:
            NEW = mod.apply(C, [tuple(h) for h in hits])
        except Exception:
            miss += 1
            continue
        if NEW is None:
            miss += 1
            continue
        old = csT[gn]
        csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
        n += 1
    f['post'].formatType = 3.0
    f['post'].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    out = OUTD + '/' + FN[tag]
    f.save(out)
    f.close()
    print('%-12s %s: 应用 %d 字 (miss %d) -> %s' % (mod.NAME, tag, n, miss, out), flush=True)


def do_one(mod, tag, ch):
    """单字调试: 该档独立检测, 只改该字"""
    f, cm, gs, csT = load_font(tag)
    cp = ord(ch)
    gn, C = get_contours(gs, cm, cp)
    if not C:
        print('%s 无字形' % ch)
        return
    hits = mod.find(C, SW[tag])
    print('%s hits=%s' % (ch, hits))
    if not hits:
        return
    NEW = mod.apply(C, hits)
    old = csT[gn]
    csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
    f['post'].formatType = 3.0
    f['post'].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    out = OUTD + '/' + FN[tag]
    f.save(out)
    f.close()
    print('saved -> %s' % out)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    mod = importlib.import_module(sys.argv[1])
    mode = sys.argv[2]

    if mode == 'detect':
        do_detect(mod)
    elif mode == 'apply':
        tag = sys.argv[3]
        path = sys.argv[4] if len(sys.argv) > 4 else INDEX_PATH
        with open(path) as fh:
            idx = json.load(fh)['hits']
        do_apply(mod, tag, idx)
    elif mode == 'all':
        idx = do_detect(mod)
        for tag in ['250', '400', '900']:
            do_apply(mod, tag, idx)
    elif mode == 'one':
        do_one(mod, sys.argv[3], sys.argv[4])
    else:
        print('unknown mode: ' + mode)


if __name__ == '__main__':
    main()
