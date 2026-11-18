#!/usr/bin/env python3
"""m_latinwidth - 拉丁字宽恢复为 Mona Sans 原始值

问题（用户反馈）: 「拉丁字体怎么窄了这么多？」「和MonaSans比宽了很多啊」

实测（400 档，墨宽/advance）:
  字   SHS          Mona          我们(线上)
  A    600/608      587/670       597/697
  H    527/728      544/754       550/764
  M    610/812      648/858       687/894
  W    825/878      867/979       858/994
  n    434/610      394/561       412/582

根因:
  m_latinmat 只对轮廓做横向缩放 0.943，**advance width 保持 SHS 体系**。
  而 46/62 个常用拉丁字形已从 Mona 注入（m_latinext），
  Mona 的 advance 是按它自己的轮廓设计的。

  结果: 轮廓被压窄 5.7% 但 advance 不变 -> 字距相对变宽 -> 混排显得松散。

修法:
  对已从 Mona 注入的拉丁字形，把 advance 恢复为 Mona 的值。
  只改 hmtx，不动轮廓（轮廓已经是正常宽度）。

🔴 判定"源自 Mona": 视觉上 46/62 字来自 Mona，
   但更可靠的是直接以 Mona 的 cmap+advance 为准，对全部拉丁区间统一设值。
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R16')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R17')
FN = {'250': 'master-ExtraLight-250.otf',
      '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}
MONA = '/workspace/wdsans/ref/mona/MonaSansVF.ttf'
WGHT = {'250': 250, '400': 400, '900': 900}

# 拉丁码位范围（与 m_latinmat 一致）
LATIN_RANGES = [
    (0x0020, 0x007E),   # Basic Latin
    (0x00A0, 0x024F),   # Latin-1 + Ext-A/B
    (0x0250, 0x02AF),   # IPA
    (0x1E00, 0x1EFF),   # Latin Ext Additional
    (0x2000, 0x206F),   # General Punctuation
    (0x20A0, 0x20CF),   # Currency Symbols
]


def in_latin(cp):
    for lo, hi in LATIN_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def main():
    os.makedirs(OUTD, exist_ok=True)

    for tag in ['250', '400', '900']:
        # 1) Mona 按目标字重实例化
        mv = TTFont(MONA)
        try:
            inst = instantiateVariableFont(mv, {'wght': WGHT[tag]}, inplace=False,
                                           updateFontNames=False)
        except Exception as e:
            print('  Mona 实例化失败 %s: %s' % (tag, e), flush=True)
            mv.close(); continue
        mcm = inst.getBestCmap()
        mhm = inst['hmtx']
        mona_adv = {}
        for cp in mcm:
            if not in_latin(cp):
                continue
            gn = mcm[cp]
            w = mhm[gn][0]
            if w > 0:
                mona_adv[cp] = w
        inst.close(); mv.close()

        # 2) 改目标字体 hmtx
        f = TTFont(SRC + '/' + FN[tag])
        cm = f.getBestCmap()
        hm = f['hmtx']
        n = 0
        for cp, target in mona_adv.items():
            if cp not in cm:
                continue
            gn = cm[cp]
            cur = hm[gn][0]
            if abs(cur - target) < 1:
                continue
            hm[gn] = (target, hm[gn][1])
            n += 1
        print('  %s: 调整 %d 个拉丁字形 advance' % (tag, n), flush=True)
        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()


if __name__ == "__main__":
    main()
