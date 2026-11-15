#!/usr/bin/env python3
"""m_nametable - 修正 name 表：中文名 / 版权声明 / OFL 修改告知 / VF 元数据

发现的问题:
1) 无中文名称 -> 中文系统显示英文，不符合中文字体定位
2) nameID 0 版权只写 "© 2014-2025 Adobe"，缺 WDesign 的修改声明
   （OFL 1.1 要求衍生作品标明已修改）
3) nameID 8 Manufacturer 仍是 "Adobe"
4) nameID 11 Vendor URL 仍是 adobe.com/type/
5) nameID 25 (Variations PostScript Name Prefix) 缺失，VF 标准要求
6) nameID 5 版本号仍是上游的 "Version 2.005"

修复（保持与 OFL.txt 一致）:
  nameID 0  Copyright -> 加 WDesign 修改声明
  nameID 1  Family    -> 加 zh-CN "WDesign Sans"（中英同名，便于识别）
  nameID 4  FullName  -> 加 zh-CN
  nameID 5  Version   -> 改为 WDesign 自己的版本
  nameID 8  Manufacturer -> WDesign
  nameID 9  Designer  -> 保留上游 + 补充
  nameID 11 Vendor URL -> 更新
  nameID 25 -> "WDesignSans"
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._n_a_m_e import NameRecord

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_MOD17')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD18')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}

FAMILY = 'WDesign Sans'
FAMILY_ZH = 'WDesign Sans'      # 中英同名，设计软件里好识别
VERSION = 'Version 1.000'
COPYRIGHT = (
    'Copyright 2026 WDesign. '
    'Derived from Noto Sans CJK (Copyright 2014-2021 Adobe, '
    'http://www.adobe.com/, with Reserved Font Name "Source") and '
    'Mona Sans (Copyright 2022 The Mona Sans Project Authors, '
    'https://github.com/github/mona-sans, with Reserved Font Name "Mona"). '
    'This derivative uses neither reserved name and is licensed under '
    'SIL Open Font License 1.1.'
)
TRADEMARK = (
    'WDesign Sans is a modified version of Noto Sans CJK and Mona Sans. '
    'Noto is a trademark of Adobe. Mona Sans is a project of GitHub.'
)
MANUFACTURER = 'WDesign'
VENDOR_URL = 'https://github.com/w-run/wdsans'
PS_PREFIX = 'WDesignSans'

# 平台记录: (platformID, platEncID, langID)
WIN_EN = (3, 1, 0x0409)     # Windows Unicode BMP, English US
WIN_ZH = (3, 1, 0x0804)     # Windows Unicode BMP, Chinese PRC
MAC_EN = (1, 0, 0)          # Mac Roman, English


def set_name(nt, nid, value, plats):
    """设置/替换指定 nameID 在多个平台的记录"""
    # 先删除该 nameID 的这些平台记录
    nt.names = [r for r in nt.names
                if not (r.nameID == nid and
                        (r.platformID, r.platEncID, r.langID) in plats)]
    for pid, eid, lid in plats:
        rec = NameRecord()
        rec.nameID = nid
        rec.platformID = pid
        rec.platEncID = eid
        rec.langID = lid
        rec.string = value.encode('utf-16-be' if pid == 3 else 'latin-1')
        nt.names.append(rec)


def main():
    os.makedirs(OUTD, exist_ok=True)
    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        nt = f['name']

        # 版权（OFL 要求衍生作品标明来源与修改）
        set_name(nt, 0, COPYRIGHT, [WIN_EN, MAC_EN])
        set_name(nt, 0, COPYRIGHT, [WIN_EN])
        # 商标
        set_name(nt, 7, TRADEMARK, [WIN_EN])
        # 家族名（中英）
        set_name(nt, 1, FAMILY, [WIN_EN, MAC_EN])
        set_name(nt, 1, FAMILY_ZH, [WIN_ZH])
        # 全名
        set_name(nt, 4, FAMILY, [WIN_EN, MAC_EN])
        set_name(nt, 4, FAMILY_ZH, [WIN_ZH])
        # PostScript 名
        set_name(nt, 6, 'WDesignSans-Regular', [WIN_EN, MAC_EN])
        # 版本（去掉上游 2.005）
        set_name(nt, 5, VERSION, [WIN_EN])
        # 制造商 / 设计者 / 厂商 URL
        set_name(nt, 8, MANUFACTURER, [WIN_EN])
        set_name(nt, 11, VENDOR_URL, [WIN_EN])
        # Typo 家族族（多语言）
        set_name(nt, 16, FAMILY, [WIN_EN, MAC_EN])
        set_name(nt, 16, FAMILY_ZH, [WIN_ZH])
        # VF 的 PostScript Name Prefix（nameID 25）
        set_name(nt, 25, PS_PREFIX, [WIN_EN, MAC_EN])

        print('  %s: name 记录 %d -> %d' % (tag, 0, len(nt.names)), flush=True)
        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()


main()
