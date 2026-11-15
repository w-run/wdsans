#!/usr/bin/env python3
"""post_vf_name.py - VF 构建后补回多语言 name 记录

问题:
  varLib 构建 VF 时只保留 master 的 Windows en-US(0x409) 与 Mac(0x0) 记录，
  zh-CN(0x804) 等其它语言记录会被丢弃。

  实测:
    masters_MOD18: 31 条, langIDs=[0x0,0x409,0x804]  zh-CN 5 条
    构建后 VF:     49 条, langIDs=[0x0,0x409]        zh-CN 0 条

修复:
  VF 构建完成后，直接从 master 复制 zh-CN 记录到 VF。
"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._n_a_m_e import NameRecord

VF = sys.argv[1] if len(sys.argv) > 1 else '/workspace/static/wdsans/WDesignSans-VF.otf'
MASTER = '/workspace/wdsans2/build/masters_MOD18/master-Regular-400.otf'

# 需要补回的语言
TARGET_LANGS = [0x0804]     # zh-CN
# 需要补回的 nameID（1=Family 2=Subfamily 4=FullName 16=TypoFamily 17=TypoSubfamily）
TARGET_IDS = [1, 2, 4, 16, 17]


def main():
    vf = TTFont(VF)
    ms = TTFont(MASTER)

    vf_nt = vf['name']
    ms_nt = ms['name']

    # 收集 master 里的目标记录
    add = []
    for r in ms_nt.names:
        if r.langID in TARGET_LANGS and r.nameID in TARGET_IDS:
            add.append(r)

    print('master 中找到 %d 条待补记录' % len(add))
    if not add:
        print('无需补入'); vf.close(); ms.close(); return

    # 删除 VF 中同 (nameID, platformID, platEncID, langID) 的旧记录
    keys = {(r.nameID, r.platformID, r.platEncID, r.langID) for r in add}
    vf_nt.names = [r for r in vf_nt.names
                   if (r.nameID, r.platformID, r.platEncID, r.langID) not in keys]

    # 加入（ID17 Subfamily 固定为 Regular，因为 VF 的实例名由 fvar 管理）
    for r in add:
        rec = NameRecord()
        rec.nameID = r.nameID
        rec.platformID = r.platformID
        rec.platEncID = r.platEncID
        rec.langID = r.langID
        if r.nameID == 17:
            rec.string = 'Regular'.encode('utf-16-be')
        else:
            rec.string = r.string
        vf_nt.names.append(rec)
        try:
            print('  + ID%-3d lang=0x%04X  %s' % (r.nameID, r.langID, r.toUnicode()))
        except Exception:
            print('  + ID%-3d lang=0x%04X' % (r.nameID, r.langID))

    vf['post'].formatType = 3.0
    vf['post'].glyphOrder = None
    vf.save(VF)
    vf.close()
    ms.close()

    # 验证
    chk = TTFont(VF, lazy=True)
    langs = sorted(set(r.langID for r in chk['name'].names))
    print()
    print('补入后 langIDs: %s' % [hex(l) for l in langs])
    print('总记录: %d' % len(chk['name'].names))
    chk.close()


main()
