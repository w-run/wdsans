#!/usr/bin/env python3
P = "/workspace/wdsans/docs/DELIVERY.md"
s = open(P, encoding="utf-8").read()

old = """cp archive/v261120/WDesignSans-VF.otf /workspace/static/wdsans/
cp archive/v261120/wd-preview.woff2  /workspace/static/wdsans/
cp archive/v261120/masters/*.otf     /workspace/wdsans2/build/masters_R34/"""

new = """cd /workspace/static/wdsans
cp archive/v261120/WDesignSans-VF.otf .
cp archive/v261120/WDesignSans-FlatApex-Regular.otf .
cp archive/v261120/wd-preview.woff2 .
cp archive/v261120/wd-poster-vf.woff2 poster/wd-vf.woff2
cp archive/v261120/wd-poster-flat.woff2 poster/wd-flat.woff2
cp archive/v261120/masters/*.otf /workspace/wdsans2/build/masters_R35/"""

if old in s:
    s = s.replace(old, new)
    open(P, "w", encoding="utf-8").write(s)
    print("回滚命令已修正（含 FlatApex + 海报子集 + R35）")
else:
    print("未匹配");
    i = s.find("回滚：")
    print(repr(s[i:i+400]))