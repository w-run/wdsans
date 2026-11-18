#!/usr/bin/env python3
"""verify_header - 核对页面顶部宣称的文件大小与字数"""
import os
from fontTools.ttLib import TTFont

PREV = "/workspace/static/wdsans/wd-preview.woff2"
VF   = "/workspace/static/wdsans/WDesignSans-VF.otf"

for p in (PREV, VF):
    sz = os.path.getsize(p)
    print("%-30s %10d B  = %.2f MB" % (os.path.basename(p), sz, sz/1024/1024))

f = TTFont(PREV, lazy=True)
cm = f.getBestCmap()
ng = f["maxp"].numGlyphs
f.close()
print()
print("预览子集 cmap 字符数: %d" % len(cm))
print("预览子集 字形数:      %d" % ng)
