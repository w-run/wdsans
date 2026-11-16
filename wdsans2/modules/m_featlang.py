#!/usr/bin/env python3
"""m_featlang - 把数字排版特性注册到所有语言系统

问题（2026-11-15 用户反馈「冒号特性啥的没有」）:
  我们新增的 7 个特性只注册在 DFLT 与 latn-DFLT 的 DefaultLangSys，
  没有注册到 hani/latn 的 ZHS/ZHH/ZHT/JAN/KOR LangSysRecord。

  一旦某脚本存在 LangSysRecord(HarfBuzz/Chrome) 就不会回退到 DefaultLangSys，
  所以中文环境下 sups/subs/sinf/numr/dnom/pnum/frac 全部失效。

实测:
  lang=en  (无 LangSysRecord) -> sups 123 = gid43272(241) 生效
  lang=zh-hans (ZHS)          -> sups 123 = gid18(390)   不生效

修复: 把上述 7 个 FeatureRecord 的索引追加到每个 LangSys 的 FeatureIndex。
只改 ScriptList，不动 FeatureList/LookupList -> 零风险。
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R18')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R19')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}

# 需要注册到所有语言系统的特性
WANT = {'sups', 'subs', 'sinf', 'numr', 'dnom', 'pnum', 'frac'}


def fix(f):
    g = f['GSUB'].table
    # 找出这些特性的 FeatureRecord 索引
    want_idx = set()
    for i, fr in enumerate(g.FeatureList.FeatureRecord):
        if fr.FeatureTag in WANT:
            want_idx.add(i)
    if not want_idx:
        return 0, 0

    added = 0
    for sr in g.ScriptList.ScriptRecord:
        lss = []
        if sr.Script.DefaultLangSys:
            lss.append(sr.Script.DefaultLangSys)
        for lr in (sr.Script.LangSysRecord or []):
            lss.append(lr.LangSys)
        for ls in lss:
            cur = set(ls.FeatureIndex or [])
            missing = sorted(want_idx - cur)
            if missing:
                ls.FeatureIndex = sorted(cur | want_idx)
                ls.FeatureCount = len(ls.FeatureIndex)
                added += len(missing)
    return len(want_idx), added


def main():
    os.makedirs(OUTD, exist_ok=True)
    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        nfeat, nadd = fix(f)
        print('  %s: %d 个特性, 新增 %d 处指向' % (tag, nfeat, nadd), flush=True)
        f.save(OUTD + '/' + FN[tag])
        f.close()
    print('完成 -> %s' % OUTD)


main()