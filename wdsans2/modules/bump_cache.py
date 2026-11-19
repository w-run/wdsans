#!/usr/bin/env python3
"""bump_cache - R35 部署后更新 cache-buster"""
import re, datetime

STAMP = "202611190836"   # R35 部署时间

# 1) index.html: wd-preview
P1 = "/workspace/static/wdsans/index.html"
s = open(P1, encoding="utf-8").read()
before = s
s = re.sub(r"wd-preview\.woff2\?v=\d+", "wd-preview.woff2?v=" + STAMP, s)
# 下载链接加版本（避免用户下到旧文件）
s = s.replace('href="WDesignSans-VF.otf" download', 'href="WDesignSans-VF.otf?v=' + STAMP + '" download')
if s != before:
    open(P1, "w", encoding="utf-8").write(s)
    print("index.html 已更新 cache-buster")

# 2) poster/index.html: wd-vf / wd-flat（原本无 v 参数）
P2 = "/workspace/static/wdsans/poster/index.html"
t = open(P2, encoding="utf-8").read()
t0 = t
t = re.sub(r"wd-vf\.woff2(?!\?v=)", "wd-vf.woff2?v=" + STAMP, t)
t = re.sub(r"wd-flat\.woff2(?!\?v=)", "wd-flat.woff2?v=" + STAMP, t)
if t != t0:
    open(P2, "w", encoding="utf-8").write(t)
    print("poster/index.html 已加 cache-buster")
else:
    print("poster/index.html 无变化（可能已带 v 参数）")

# 3) 核对
for p in (P1, P2):
    c = open(p, encoding="utf-8").read()
    vs = re.findall(r"\?v=(\d+)", c)
    print("  %-40s v=%s" % (p.split('/')[-2] + '/' + p.split('/')[-1], sorted(set(vs)) or "无"))
