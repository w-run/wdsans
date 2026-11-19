#!/usr/bin/env python3
"""check_zhname - 核实中文 name 记录是否丢失"""
from fontTools.ttLib import TTFont

for lbl, p in (("R37 部署版", "/workspace/static/wdsans/WDesignSans-VF.otf"),
                ("R36 备份", "/workspace/wdsans2/build/VF_R36_backup.otf"),
                ("SHS 原版", "/workspace/wdsans/ref/shs/shs-400.otf")):
    f = TTFont(p, lazy=True)
    nm = f['name']
    langs = sorted(set((r.platformID, r.langID) for r in nm.names))
    print("%s:" % lbl)
    print("  (platform, langID): %s" % ["(%d,0x%03X)" % x for x in langs])
    zh = [r for r in nm.names if r.langID == 0x804]
    print("  zh-CN 记录: %d 条" % len(zh))
    if zh:
        print("    样例 nameID=%s -> %s" % (zh[0].nameID, nm.getDebugName(zh[0].nameID)))
    # 检查 family name
    for nid in (1, 4, 16):
        try:
            v = nm.getDebugName(nid)
            print("    nameID %d: %s" % (nid, v))
        except Exception:
            pass
    f.close()
    print()