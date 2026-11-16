#!/usr/bin/env python3
"""post_vf_name2 - VF 构建后补回中文 name 记录（路径可配置）

问题: varLib 构建 VF 时只保留 Windows en-US(0x409) 与 Mac(0x0)，
      zh-CN(0x804) 记录全部被丢弃。

修复: 从当前链尾 master 复制 zh-CN 的 nameID 1/2/4/16/17 到 VF。
      🔴 ID17 (Subfamily) 必须固定为 Regular —— master 里是 ExtraLight（250档）。
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._n_a_m_e import NameRecord

VF = sys.argv[1] if len(sys.argv) > 1 else '/workspace/static/wdsans/WDesignSans-VF.otf'
MASTER = os.environ.get('WDS_MASTER',
    '/workspace/wdsans2/build/masters_R25b/master-Regular-400.otf')

TARGET_LANGS = [0x0804]
TARGET_IDS = [1, 2, 4, 16, 17]


def main():
    if not os.path.exists(MASTER):
        print('master 不存在: %s' % MASTER); return 1
    vf = TTFont(VF)
    mf = TTFont(MASTER, lazy=True)
    mnm = mf["name"]
    vnm = vf["name"]

    added = 0
    for lang in TARGET_LANGS:
        for nid in TARGET_IDS:
            src = None
            for r in mnm.names:
                if r.nameID == nid and r.langID == lang and r.platformID == 3:
                    src = r
                    break
            if src is None:
                continue
            # 去掉已有同 (nid, lang) 记录
            vnm.names = [r for r in vnm.names
                         if not (r.nameID == nid and r.langID == lang)]
            txt = src.toUnicode()
            # 🔴 ID17 必须固定 Regular
            if nid == 17:
                txt = "Regular"
            rec = NameRecord()
            rec.nameID = nid
            rec.platformID = 3
            rec.platEncID = 1
            rec.langID = lang
            rec.string = txt.encode("utf-16-be")
            vnm.names.append(rec)
            added += 1

    vf['post'].formatType = 3.0
    vf['post'].glyphOrder = None
    vf.save(VF)
    vf.close(); mf.close()

    print('补回 %d 条 zh-CN 记录 -> %s' % (added, VF))
    g = TTFont(VF, lazy=True)
    langs = sorted(set(r.langID for r in g["name"].names))
    print('  最终 langIDs: %s' % [hex(x) for x in langs])
    for r in g["name"].names:
        if r.langID == 0x804 and r.nameID in (1, 2, 4, 17):
            try:
                print('    id%-2d = %s' % (r.nameID, r.toUnicode()))
            except Exception:
                pass
    g.close()
    return 0


sys.exit(main())