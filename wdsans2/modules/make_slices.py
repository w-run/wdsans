#!/usr/bin/env python3
"""make_slices.py - 分片 Web 字体（unicode-range 按需加载）

按【码位连续区间】切分，保证每片的 unicode-range 紧凑，
浏览器只会下载页面实际用到的分片。

策略:
  拉丁 5 片（基础/1Suppl/ExtA/ExtB/ExtAdd）
  标点 1 片
  中文按 400 码位一片（约 400 字，~550 KB）
"""
import sys, os, json
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options

VF = "/workspace/static/wdsans/WDesignSans-VF.ttf"
OUT = "/workspace/static/wdsans/dist/slices"
os.makedirs(OUT, exist_ok=True)

PUNCT = "\uff0c\u3002\u3001\uff1b\uff1a\uff1f\uff01\u201c\u201d\u2018\u2019\uff08\uff09\u3010\u3011\u300a\u300b\u3008\u3009\u2026\u2014\uff5e\u00b7\u300c\u300d\u300e\u300f\u3014\u3015\uff05\uff0b\uff0d\u00d7\u00f7\uff1d\uffe5"

LATIN = [
    ("latin-basic", 0x20, 0x7F),
    ("latin-1-supp", 0xA0, 0x100),
    ("latin-ext-a", 0x100, 0x180),
    ("latin-ext-b", 0x180, 0x250),
    ("latin-ext-add", 0x1E00, 0x1F00),
]

CJK_SPAN = 400


def mk(src_path, name, cps, outdir):
    f = TTFont(src_path)
    cm = f.getBestCmap()
    keep = [c for c in cps if c in cm]
    if not keep:
        f.close()
        return None, []
    text = "".join(chr(c) for c in keep)
    opt = Options()
    opt.flavor = "woff2"
    opt.desubroutinize = True
    opt.name_IDs = ["*"]
    opt.name_legacy = True
    opt.notdef_outline = True
    opt.recalc_bounds = True
    opt.recalc_timestamp = False
    opt.layout_features = ["ccmp","locl","calt","liga","kern","mark","mkmk",
                           "vert","vrt2","frac","numr","dnom","sups","subs","pnum","chws","vchw"]
    opt.drop_tables = ["DSIG"]
    opt.ignore_missing_unicodes = True
    ss = Subsetter(options=opt)
    ss.populate(text=text)
    ss.subset(f)
    dst = os.path.join(outdir, name + ".woff2")
    f.save(dst)
    f.close()
    return os.path.getsize(dst), sorted(keep)


def rangestr(cps):
    """把码位列表压缩成 unicode-range 字符串"""
    if not cps:
        return ""
    parts = []
    start = cps[0]
    prev = cps[0]
    for c in cps[1:]:
        if c != prev + 1:
            parts.append((start, prev))
            start = c
        prev = c
    parts.append((start, prev))
    out = []
    for a, b in parts:
        if a == b:
            out.append("U+%04X" % a)
        else:
            out.append("U+%04X-%04X" % (a, b))
    return ",".join(out)


print("=== generate slices ===", flush=True)
f0 = TTFont(VF, lazy=True)
cm0 = f0.getBestCmap()
f0.close()

manifest = []
total = 0

print("")
print("--- latin ---")
for name, lo, hi in LATIN:
    cps = list(range(lo, hi))
    sz, keep = mk(VF, name, cps, OUT)
    if sz:
        manifest.append({"file": name + ".woff2", "range": rangestr(keep), "bytes": sz})
        total += sz
        print("  %-16s %7.1f KB  %d chars" % (name, sz/1024, len(keep)), flush=True)

print("")
print("--- punct ---")
sz, keep = mk(VF, "punct-cjk", [ord(c) for c in PUNCT], OUT)
if sz:
    manifest.append({"file": "punct-cjk.woff2", "range": rangestr(keep), "bytes": sz})
    total += sz
    print("  %-16s %7.1f KB  %d chars" % ("punct-cjk", sz/1024, len(keep)), flush=True)

print("")
print("--- cjk (by codepoint span) ---")
cjk = sorted(c for c in cm0 if 0x4E00 <= c <= 0x9FFF)
lo = cjk[0]
idx = 0
while lo <= cjk[-1]:
    hi = min(lo + CJK_SPAN - 1, cjk[-1])
    chunk = [c for c in cjk if lo <= c <= hi]
    if chunk:
        name = "cjk-%03d" % idx
        sz, keep = mk(VF, name, chunk, OUT)
        if sz:
            manifest.append({"file": name + ".woff2", "range": rangestr(keep), "bytes": sz})
            total += sz
            if idx < 8 or idx % 10 == 0:
                print("  %-16s %7.1f KB  U+%04X-%04X  %d" % (name, sz/1024, min(keep), max(keep), len(keep)), flush=True)
        idx += 1
    lo = hi + 1

with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fp:
    json.dump(manifest, fp, ensure_ascii=False, indent=1)

print("")
print("=== summary ===")
print("  slices: %d" % len(manifest))
print("  total: %.2f MB" % (total/1024/1024))
print("  avg: %.1f KB" % (total/len(manifest)/1024))

