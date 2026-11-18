#!/usr/bin/env python3
"""fix_header_numbers - 核准页面头部的文件大小与字数

实测:
  WDesignSans-VF.otf   41,335,432 B = 39.4 MB
  wd-preview.woff2      2,247,784 B =  2.14 MB
  子集 cmap 字符数      3,903
页面原写: 40 MB / 3,886 字 / 4.0 MB（4.0 是解压后大小，浏览器实际下载 2.14 MB）
"""
P = "/workspace/static/wdsans/index.html"
s = open(P, encoding="utf-8").read()
orig = s

old = ("  <a href=\"WDesignSans-VF.otf\" download>下载完整 OTF（40 MB）</a> ·\n"
       "  本页使用 3,886 字 Web 子集（4.0 MB）实时渲染")
new = ("  <a href=\"WDesignSans-VF.otf\" download>下载完整 OTF（39.4 MB）</a> ·\n"
       "  本页使用 3,903 字 Web 子集（woff2 2.1 MB）实时渲染")

if old in s:
    s = s.replace(old, new)
    print("已修正头部数字")
else:
    print("未精确匹配，尝试逐段替换")
    s = s.replace("下载完整 OTF（40 MB）", "下载完整 OTF（39.4 MB）")
    s = s.replace("本页使用 3,886 字 Web 子集（4.0 MB）", "本页使用 3,903 字 Web 子集（woff2 2.1 MB）")

if s != orig:
    open(P, "w", encoding="utf-8").write(s)
    print("已保存")
else:
    print("无改动")
