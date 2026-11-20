#!/usr/bin/env python3
"""make_release.py - WDesign Sans v3.0.261120 发行版

产物:
  WDesignSans-VF.ttf            完整可变 TTF      ~49.9 MB
  WDesignSans-VF.woff2          Web 常用子集      ~1.0 MB
  WDesignSans-VF-full.woff2     GB2312 全字库     ~3.5 MB
  WDesignSans-Latin.woff2       拉丁专用          ~120 KB
  WDesignSans-{Light,Regular,Bold}.ttf   静态版
"""
import sys, os, shutil
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
from fontTools.varLib.instancer import instantiateVariableFont

VF = "/workspace/static/wdsans/WDesignSans-VF.ttf"
OUT = "/workspace/static/wdsans/dist"
os.makedirs(OUT, exist_ok=True)

COMMON = set(open("/workspace/wdsans2/data/common3500.txt", encoding="utf-8").read().strip())
PUNCT = "，。、；：？！“”‘’（）【】《》〈〉…—～·「」『』〔〕％＋－×÷＝￥"


def latin_cps():
    cps = set(range(0x20, 0x7F))
    for lo, hi in ((0x00A0, 0x00FF), (0x0100, 0x017F), (0x0180, 0x024F), (0x1E00, 0x1EFF)):
        cps |= set(range(lo, hi + 1))
    return cps


def do_subset(src, dst, cps, flavor="woff2", label=""):
    """关键: layout_features 只保留必要特性，且 subsetter 会自动清理未用字形"""
    f = TTFont(src)
    cm = f.getBestCmap()
    text = "".join(chr(c) for c in sorted(cps) if c in cm)
    opt = Options()
    opt.flavor = flavor
    opt.desubroutinize = True
    opt.name_IDs = ["*"]
    opt.name_legacy = True
    opt.name_languages = ["*"]
    opt.notdef_outline = True
    opt.recalc_bounds = True
    opt.recalc_timestamp = False
    opt.canonical_order = True
    # 只保留这些特性（去掉韩文 ljmo/tjmo 等大表；保留排版必需）
    opt.layout_features = [
        "ccmp", "locl", "calt", "liga", "clig", "dlig",
        "kern", "mark", "mkmk", "vert", "vrt2", "vkrn",
        "frac", "numr", "dnom", "sups", "subs", "sinf", "pnum",
        "fwid", "hwid", "pwid", "chws", "vchw", "halt", "palt",
        "aalt", "hist", "ruby",
    ]
    opt.drop_tables = ["DSIG"]
    opt.ignore_missing_unicodes = True
    opt.hinting = False
    ss = Subsetter(options=opt)
    ss.populate(text=text)
    ss.subset(f)
    f.save(dst)
    f.close()
    sz = os.path.getsize(dst) / 1024.0 / 1024.0
    print("  %-34s %7.2f MB  %s" % (os.path.basename(dst), sz, label), flush=True)
    return sz


def do_static(src, dst, wght, subset_cps=None, label=""):
    f = TTFont(src)
    inst = instantiateVariableFont(f, {"wght": wght}, inplace=False, updateFontNames=True)
    if subset_cps is not None:
        cm = inst.getBestCmap()
        text = "".join(chr(c) for c in sorted(subset_cps) if c in cm)
        opt = Options()
        opt.desubroutinize = True
        opt.name_IDs = ["*"]
        opt.name_legacy = True
        opt.notdef_outline = True
        opt.layout_features = ["ccmp","locl","calt","liga","kern","mark","mkmk","vert","vrt2","frac","numr","dnom","sups","subs","pnum","chws","vchw"]
        opt.drop_tables = ["DSIG"]
        ss = Subsetter(options=opt)
        ss.populate(text=text)
        ss.subset(inst)
    inst.save(dst)
    inst.close()
    f.close()
    sz = os.path.getsize(dst) / 1024.0 / 1024.0
    print("  %-34s %7.2f MB  %s" % (os.path.basename(dst), sz, label), flush=True)
    return sz


print("=== WDesign Sans v3.0.261120 ===")
print()

dst = os.path.join(OUT, "WDesignSans-VF.ttf")
shutil.copy2(VF, dst)
print("  %-34s %7.2f MB  完整 45012 字符" % ("WDesignSans-VF.ttf", os.path.getsize(dst)/1024/1024), flush=True)

print()
web = set(ord(c) for c in COMMON) | set(ord(c) for c in PUNCT) | latin_cps()
do_subset(VF, os.path.join(OUT, "WDesignSans-VF.woff2"), web, "woff2", "常用3500+拉丁 100-900")

gb = set()
for hi in range(0xB0, 0xF8):
    for lo in range(0xA1, 0xFF):
        try: gb.add(ord(bytes([hi, lo]).decode("gb2312")))
        except Exception: pass
full = gb | latin_cps() | set(ord(c) for c in PUNCT)
do_subset(VF, os.path.join(OUT, "WDesignSans-VF-full.woff2"), full, "woff2", "GB2312+拉丁 100-900")

do_subset(VF, os.path.join(OUT, "WDesignSans-Latin.woff2"), latin_cps(), "woff2", "仅拉丁 100-900")

print()
print("=== 静态版（全字库）===")
for w, nm in ((300, "Light"), (400, "Regular"), (700, "Bold"), (100, "Thin"), (900, "Black")):
    do_static(VF, os.path.join(OUT, "WDesignSans-%s.ttf" % nm), w, None, "wght=%d 全字符" % w)

print()
print("=== 静态版（Web 子集）===")
for w, nm in ((400, "Regular"), (700, "Bold")):
    do_static(VF, os.path.join(OUT, "WDesignSans-%s-web.ttf" % nm), w, web, "wght=%d 常用子集" % w)

print()
print("done")

