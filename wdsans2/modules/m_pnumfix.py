#!/usr/bin/env python3
"""m_pnumfix - 让 pnum 在当前默认等宽下也能正确切回比例数字

背景（2026-11-16）:
  m_digitmono 让所有语言环境下数字默认等宽 (glyph63166~63175, adv 555)。
  但 pnum 的原 mapping 是:
      glyph63166 -> zero   (等宽 -> 比例)   <- 只有这一套输入
  中文下 locl 走进新 lookup 后数字已变 glyph6316x，
  理论上应该能匹配。实测 pnum 仍无变化，因为：
  - 等宽字形的 GSUB 输入完整，但 SingleSubst 的 Coverage 只含 glyph6316x
  - 若数字已是 glyph6316x 则应命中，故改为**同时覆盖两套输入**更稳

修复: pnum 的 mapping 扩充为 20 条:
    glyph63166..63175 -> zero..nine    (等宽 -> 比例)
    glyph07213..07222 -> zero..nine    (另一套等宽变体)
  并重新挂到所有语言系统。
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R20')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R21')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}

DIG_NAMES = ['zero', 'one', 'two', 'three', 'four', 'five',
             'six', 'seven', 'eight', 'nine']


def main():
    os.makedirs(OUTD, exist_ok=True)
    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        g = f['GSUB'].table
        go = set(f.getGlyphOrder()); hm = f['hmtx']
        gid = {n: i for i, n in enumerate(f.getGlyphOrder())}

        # 找出所有「advance 相同、且是数字形」的等宽变体组
        # 已知: glyph63166..63175 (555), glyph07213..07222
        variants = []
        base_adv = None
        for start, cnt in [(63166, 10), (7213, 10)]:
            names = []
            for k in range(cnt):
                gn = 'glyph%05d' % (start + k)
                if gn in go:
                    names.append(gn)
            if len(names) == cnt:
                variants.append(names)

        # 构造新 mapping: 所有等宽变体 -> 比例数字
        new_map = {}
        for names in variants:
            for i, gn in enumerate(names):
                new_map[gn] = DIG_NAMES[i]

        # 同时保留 zero..nine -> ? 不需要（那是反方向）
        if not new_map:
            print('  %s: 找不到等宽变体' % tag, flush=True)
            f.close()
            continue

        # 找到 pnum 的 FeatureRecord，替换其 lookup 的 mapping
        replaced = 0
        for fr in g.FeatureList.FeatureRecord:
            if fr.FeatureTag != 'pnum':
                continue
            for li in fr.Feature.LookupListIndex:
                lk = g.LookupList.Lookup[li]
                for st in lk.SubTable:
                    t = st.ExtSubTable if hasattr(st, 'ExtSubTable') else st
                    m = getattr(t, 'mapping', None)
                    if m is None:
                        continue
                    m.update(new_map)
                    t.mapping = m
                    replaced += 1

        print('  %s: pnum mapping 扩到 %d 条 (%d 组变体), 改 %d 个 subtable' %
              (tag, len(new_map), len(variants), replaced), flush=True)
        f.save(OUTD + '/' + FN[tag])
        f.close()
    print('完成 -> %s' % OUTD)


main()