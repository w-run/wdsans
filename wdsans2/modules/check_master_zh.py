#!/usr/bin/env python3
"""check_master_zh - 确认 master 里有 zh-CN 记录"""
from fontTools.ttLib import TTFont

for p in ('/workspace/wdsans2/build/masters_R37/master-Regular-400.otf',
          '/workspace/wdsans2/build/masters_R36/master-Regular-400.otf'):
    f = TTFont(p, lazy=True)
    nm = f['name']
    zh = [r for r in nm.names if r.langID == 0x804]
    print("%s: zh-CN %d 条" % (p.split("/")[-2], len(zh)))
    for nid in (1, 2, 4, 16, 17):
        v = None
        for r in zh:
            if r.nameID == nid:
                v = str(r)
                break
        print("  nameID %-3d: %s" % (nid, v))
    f.close()
    print()