#!/usr/bin/env python3
"""make_slice_css.py - 根据 manifest.json 生成 @font-face CSS"""
import json, os

SL = "/workspace/static/wdsans/dist/slices"
man = json.load(open(os.path.join(SL, "manifest.json"), encoding="utf-8"))

lines = []
lines.append("/* WDesign Sans v3.0.261120 - sliced web font")
lines.append(" * 按 unicode-range 分片，浏览器仅下载实际用到的分片")
lines.append(" * 用法: @import 本文件，然后 font-family: 'WDesign Sans'")
lines.append(" */")
lines.append("")
for m in man:
    lines.append("@font-face{")
    lines.append("  font-family:'WDesign Sans';")
    lines.append("  font-style:normal;")
    lines.append("  font-weight:100 900;")
    lines.append("  font-display:swap;")
    lines.append("  src:url('slices/%s') format('woff2');" % m["file"])
    lines.append("  unicode-range:%s;" % m["range"])
    lines.append("}")
    lines.append("")

css = "\n".join(lines)
out = "/workspace/static/wdsans/dist/wdesign-sans.css"
open(out, "w", encoding="utf-8").write(css)
print("wrote %s (%d bytes, %d faces)" % (out, len(css), len(man)))
print("")
print("sample (first 2):")
print("\n".join(lines[:16]))

