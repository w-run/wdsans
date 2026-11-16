#!/usr/bin/env python3
"""m_digitmono - 让中文等所有语言环境下的数字默认等宽

问题（2026-11-15 发现）:
  SHS 的 locl 只在 latn-DFLT 注册 lookup#42（数字等宽映射 zero->glyph63166）；
  一旦指定语言（ZHS/ZHH/ZHT/JAN/KOR），locl 只保留标点映射 lookup#43，
  数字变回比例宽度。

实测（中文环境）:
  12:34 数字中心间距 = 27,28,31,34,34,34,33,30,33  <- 不等宽
  one adv=390 / two adv=544 / zero adv=642          <- 比例

  而 DFLT 环境下 zero->glyph63166 (adv 555 统一)。

修复: 把 lookup#42 的数字等宽映射追加到每个 LangSys 的 locl 里。
新增 lookup（SingleSubst），再挂到各 LangSys 的 locl FeatureRecord。
不动机有 FeatureList 结构，只追加 lookup + 扩展 Feature 的 LookupListIndex。
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R19')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R20')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}

DIGITS = ['zero', 'one', 'two', 'three', 'four', 'five', 
          'six', 'seven', 'eight', 'nine']
SRC_LOOKUP = 42   # latn-DFLT 的数字等宽 lookup


def main():
    os.makedirs(OUTD, exist_ok=True)
    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        g = f['GSUB'].table
        go = f.getGlyphOrder()

        # 1) 从 lookup#42 取数字等宽映射
        src_map = None
        for st in g.LookupList.Lookup[SRC_LOOKUP].SubTable:
            t = st.ExtSubTable if hasattr(st, 'ExtSubTable') else st
            m = getattr(t, 'mapping', None)
            if m and any(d in m for d in DIGITS):
                src_map = m
                break
        if not src_map:
            print('  %s: 找不到数字等宽映射' % tag, flush=True)
            f.close()
            continue
        dig_map = {k: v for k, v in src_map.items() if k in DIGITS}

        # 2) 新建 SingleSubst lookup
        new_lk = ot.Lookup()
        new_lk.LookupType = 1
        new_lk.LookupFlag = 0
        st = ot.SingleSubst()
        st.mapping = dict(dig_map)
        new_lk.SubTable = [st]
        new_lk.SubTableCount = 1
        g.LookupList.Lookup.append(new_lk)
        g.LookupList.LookupCount = len(g.LookupList.Lookup)
        new_idx = len(g.LookupList.Lookup) - 1

        # 3) 把新 lookup 挂到每个 LangSys 的 locl FeatureRecord
        touched = 0
        for sr in g.ScriptList.ScriptRecord:
            entries = []
            if sr.Script.DefaultLangSys:
                entries.append(sr.Script.DefaultLangSys)
            for lr in (sr.Script.LangSysRecord or []):
                entries.append(lr.LangSys)
            for ls in entries:
                for fi in (ls.FeatureIndex or []):
                    fr = g.FeatureList.FeatureRecord[fi]
                    if fr.FeatureTag != 'locl':
                        continue
                    if new_idx not in fr.Feature.LookupListIndex:
                        fr.Feature.LookupListIndex.append(new_idx)
                        fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
                        touched += 1
                        break   # 每个 LangSys 只加一次

        print('  %s: 新增 lookup#%d (%d 条映射), 挂接 %d 处' %
              (tag, new_idx, len(dig_map), touched), flush=True)
        f.save(OUTD + '/' + FN[tag])
        f.close()
    print('完成 -> %s' % OUTD)


main()