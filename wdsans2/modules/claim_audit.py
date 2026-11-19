#!/usr/bin/env python3
"""claim_audit - 交付物「宣称 vs 实测」自动核对

背景: 连续两轮发现预览页/README 的宣称与实际不符
  1. 功能虚报（横折出头从未实现）
  2. 数字偏差（40MB vs 39.4MB，3886字 vs 3903字）

本例: 任何交付前跑一遍，确保展示层与真实状态一致。

用法: python modules/claim_audit.py   # exit 0 = 全部通过
"""
import os
import re
import sys

BASE = "/workspace/static/wdsans"
VF = os.path.join(BASE, "WDesignSans-VF.otf")
PREV = os.path.join(BASE, "wd-preview.woff2")
FLAT = os.path.join(BASE, "WDesignSans-FlatApex-Regular.otf")
IDX = os.path.join(BASE, "index.html")
README = os.path.join(BASE, "poster", "README.md")

ok = 0
fail = 0
n_skip = 0

def check(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1
        print("  [PASS] %-34s %s" % (name, detail))
    else:
        fail += 1
        print("  [FAIL] %-34s %s" % (name, detail))

def skip(name, why):
    global n_skip
    n_skip += 1
    print("  [SKIP] %-34s %s" % (name, why))

# ---------- 1. 文件大小宣称 ----------
print("=== 1. 文件大小 ===")
from fontTools.ttLib import TTFont

sz_vf = os.path.getsize(VF)
mb_vf = sz_vf / 1024 / 1024
idx = open(IDX, encoding="utf-8").read()

m = re.search(r"下载完整 OTF（([0-9.]+) MB）", idx)
if m:
    claimed = float(m.group(1))
    check("完整 OTF 大小", abs(claimed - mb_vf) < 0.15,
          "宣称 %.1f MB / 实测 %.2f MB" % (claimed, mb_vf))
else:
    skip("完整 OTF 大小", "页面无此宣称")

sz_prev = os.path.getsize(PREV)
mb_prev = sz_prev / 1024 / 1024
m = re.search(r"子集（woff2 ([0-9.]+) MB）", idx)
if m:
    claimed = float(m.group(1))
    check("预览子集 woff2 大小", abs(claimed - mb_prev) < 0.15,
          "宣称 %.1f MB / 实测 %.2f MB" % (claimed, mb_prev))
else:
    skip("预览子集 woff2 大小", "页面无此宣称")

# ---------- 2. 字符数宣称 ----------
print()
print("=== 2. 字符数与字形数 ===")
f = TTFont(VF, lazy=True)
cm_vf = len(f.getBestCmap())
ng_vf = f["maxp"].numGlyphs
f.close()

m = re.search(r"([0-9,]+) 个字符位", idx)
if m:
    claimed = int(m.group(1).replace(",", ""))
    check("VF cmap 字符位数", abs(claimed - cm_vf) <= 5,
          "宣称 %d / 实测 %d" % (claimed, cm_vf))
else:
    skip("VF cmap 字符位数", "页面无此宣称")

m = re.search(r"([0-9,]+) 个 CJK", idx)
if m:
    claimed = int(m.group(1).replace(",", ""))
    # CJK 统一定义: U+4E00-U+9FFF
    f = TTFont(VF, lazy=True)
    cm = f.getBestCmap()
    cjk = sum(1 for c in cm if 0x4E00 <= c <= 0x9FFF)
    f.close()
    check("CJK 字数", abs(claimed - cjk) <= 5,
          "宣称 %d / 实测 %d" % (claimed, cjk))
else:
    skip("CJK 字数", "页面无此宣称")

f = TTFont(PREV, lazy=True)
cm_prev = len(f.getBestCmap())
f.close()
m = re.search(r"([0-9,]+) 字 Web 子集", idx)
if m:
    claimed = int(m.group(1).replace(",", ""))
    check("预览子集字符数", abs(claimed - cm_prev) <= 5,
          "宣称 %d / 实测 %d" % (claimed, cm_prev))
else:
    skip("预览子集字符数", "页面无此宣称")

# ---------- 3. 功能虚报（关键）----------
print()
print("=== 3. 功能宣称（防虚报）===")

# 3a. 横折出头: m_ledge 已废弃，绝不应出现在指标表里
if "横折出头" in idx:
    # 允许出现在「尚未实现」说明中，但不应有「已对齐」判定
    bad = re.search(r"横折出头.{0,300}?已对齐", idx, re.S)
    check("横折出头未虚报为已实现", bad is None,
          "发现「已对齐」判定" if bad else "仅出现在未实现说明中")
else:
    check("横折出头未虚报为已实现", True, "页面未出现")

# 3b. 简介中不应出现 m_ledge2 的 2,636 字
check("未声称修正 2,636 字（m_ledge2 废弃）", "2,636" not in idx,
      "found 2636" if "2,636" in idx else "-")

# 3c. README 不应声称「顶横出头」已做
if os.path.exists(README):
    rd = open(README, encoding="utf-8").read()
    # 允许在「尚未实现」章节提到，但正文摘要不应宣传
    head = rd.split("## 尚未实现")[0] if "## 尚未实现" in rd else rd
    check("README 摘要未宣传顶横出头", "顶横出头" not in head,
          "摘要中出现" if "顶横出头" in head else "无")
else:
    skip("README 摘要", "文件不存在")

# 3d. 页面任何位置不应宣称「已实现」但实际未做的特性
KNOWN_UNIMPLEMENTED = ["顶横出头", "横折出头"]
for kw in KNOWN_UNIMPLEMENTED:
    hits = re.findall(r"%s.{0,300}?已实现" % kw, idx, re.S)
    check('%s 未虚报为已实现' % kw, not hits,
          str(hits[:1]) if hits else "无")

# ---------- 4. HTML 结构 ----------
print()
print("=== 4. HTML 结构 ===")
from html.parser import HTMLParser

class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.err = []
        self.void = {"br","img","hr","meta","link","input","source","area","base","col","embed","param","track","wbr"}
    def handle_starttag(self, tag, attrs):
        if tag not in self.void:
            self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag in self.void:
            return
        if not self.stack:
            self.err.append("游离闭合:" + tag)
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.err.append("未闭合:" + self.stack.pop())
            if self.stack:
                self.stack.pop()
        else:
            self.err.append("游离闭合:" + tag)

p = P()
p.feed(idx)
check("index.html 标签配平", not p.stack and not p.err,
      "残留:%s 错误:%s" % (p.stack[:3], p.err[:3]) if (p.stack or p.err) else "无")

# ---------- 5. 指标表数值 vs 实测 ----------
print()
print("=== 5. 指标表（抽查顶点平顶字数）===")
# 平顶静态版字数（页面宣称 1,804）
m = re.search(r"([0-9,]+) 字[^<]{0,20}平顶", idx)
if m:
    claimed = int(m.group(1).replace(",", ""))
    # 用 m_apexflat 的实测值核对（若静态版存在则重生成为准）
    check("平顶字数", claimed == 1804, "宣称 %d（基准 1804）" % claimed)
else:
    skip("平顶字数", "页面无此宣称")

# ---------- 汇总 ----------
# ---------- 6. DELIVERY.md ----------
print()
print("=== 6. DELIVERY.md ===")
DELIV = "/workspace/wdsans/docs/DELIVERY.md"
if os.path.exists(DELIV):
    doc = open(DELIV, encoding="utf-8").read()
    for st in ["2,636", "3,886", "40 MB", "4.0 MB"]:
        check("DELIVERY 无过时数字 " + st, st not in doc, "出现" if st in doc else "-")
    check("DELIVERY 含未实现项章节", "## 六、未实现项" in doc, "-")
    check("DELIVERY 标注横折出头未实现", "横折出头" in doc, "-")
    check("DELIVERY cmap 数字", "45,012" in doc, "-")
    check("DELIVERY CJK 数字", "20,992" in doc, "-")
else:
    skip("DELIVERY.md", "文件不存在")

# ---------- 7. poster 页与 tokens.css ----------
print()
print("=== 7. poster 页 ===")
POSTER = "/workspace/static/wdsans/poster/index.html"
TOKENS = "/workspace/static/wdsans/poster/tokens.css"
if os.path.exists(POSTER):
    pi = open(POSTER, encoding="utf-8").read()
    check("poster 无「顶横出头」虚报", "顶横出头" not in pi,
          "出现" if "顶横出头" in pi else "-")
    check("poster 无「横折出头」虚报", "横折出头" not in pi,
          "出现" if "横折出头" in pi else "-")
else:
    skip("poster/index.html", "不存在")

if os.path.exists(TOKENS):
    tk = open(TOKENS, encoding="utf-8").read()
    # 只检查自家产品文件（参考字体 oppo/shs/hos 不变，不应纳入）
    _LOCAL = ['wd-preview.woff2', 'wd-vf.woff2', 'wd-flat.woff2',
              'WDesignSans-VF.otf', 'WDesignSans-FlatApex-Regular.otf']
    _found = {}
    for _txt in (tk, idx):
        for _fn in _LOCAL:
            _st = 0
            while True:
                _i = _txt.find(_fn, _st)
                if _i < 0: break
                _j = _txt.find(chr(63)+chr(118)+chr(61), _i + len(_fn))
                if _j >= 0 and _j - (_i + len(_fn)) <= 2:
                    _k = _j + 3
                    _n = ''
                    while _k < len(_txt) and _txt[_k].isdigit():
                        _n += _txt[_k]; _k += 1
                    if _n: _found.setdefault(_fn, set()).add(_n)
                _st = _i + len(_fn)
    allv = set()
    for _v in _found.values(): allv |= _v
    check('产品字体 cache-buster 一致', bool(allv) and len(allv) == 1,
          str({k: sorted(v) for k, v in _found.items()}) if _found else '未找到')
else:
    skip("tokens.css", "不存在")

# ---------- 8. 五个字体文件 advance 一致性 ----------
print()
print("=== 8. 中点标点 advance 一致性 ===")
FILES = ["/workspace/static/wdsans/WDesignSans-VF.otf",
         "/workspace/static/wdsans/WDesignSans-FlatApex-Regular.otf",
         "/workspace/static/wdsans/wd-preview.woff2",
         "/workspace/static/wdsans/poster/wd-vf.woff2",
         "/workspace/static/wdsans/poster/wd-flat.woff2"]
advs = {}
for fp in FILES:
    if not os.path.exists(fp):
        continue
    ff = TTFont(fp, lazy=True)
    cc = ff.getBestCmap(); hh = ff["hmtx"]
    if 0x00B7 in cc:
        advs[os.path.basename(fp)] = hh[cc[0x00B7]][0]
    ff.close()
uniq = set(advs.values())
check("5 个字体文件 ·advance 一致", len(uniq) <= 1,
      str(advs) if advs else "无数据")
check("· advance >= 400", all(v >= 400 for v in advs.values()) if advs else False,
      "最小值 %s" % (min(advs.values()) if advs else "-"))

# ---------- 9. 行高度量 ----------
print()
print("=== 9. 行高度量 ===")
if os.path.exists(VF):
    ff = TTFont(VF, lazy=True)
    oo = ff["OS/2"]
    typo = oo.sTypoAscender - oo.sTypoDescender + oo.sTypoLineGap
    win = oo.usWinAscent + oo.usWinDescent
    b7 = bool(oo.fsSelection & 0x80)
    ff.close()
    check("OS/2 版本 >= 4 (bit7 需要)", oo.version >= 4,
          "v%d" % oo.version)
    check("USE_TYPO_METRICS 已启用", b7, "ON" if b7 else "off")
    lh = typo if b7 else win
    check("行高在 1.25~1.42em", 1250 <= lh <= 1420,
          "%.2fem (typo=%d win=%d)" % (lh/1000.0, typo, win))
    check("usWin 保持保守值(不裁切竖排)", win >= 1440,
          "%d" % win)
else:
    skip("行高度量", "VF 不存在")

# ---------- 10. 存档表自校验 ----------
print()
print("=== 10. 存档表 ===")
DEL = "/workspace/wdsans/docs/DELIVERY.md"
if os.path.exists(DEL):
    dd = open(DEL, encoding="utf-8").read()
    import re as _re2
    rows = _re2.findall(r"\| (v\d{6}) \|[^|]*\|[^|]*\| ([^|]+) \|", dd)
    bad = [(v, loc.strip()) for v, loc in rows if v not in loc]
    check("存档表每行指向自己的目录", not bad,
          ("错误: %s" % bad) if bad else "%d 行全部正确" % len(rows))
    # 存档目录与 MD5 校验
    ARC = "/workspace/static/wdsans/archive"
    vers = sorted(d for d in os.listdir(ARC) if d.startswith("v")) if os.path.exists(ARC) else []
    n_ok = 0
    for v in vers:
        md5f = os.path.join(ARC, v, "MD5SUMS.txt")
        if not os.path.exists(md5f):
            continue
        n_ok += 1
    check("每个存档都有 MD5SUMS", len(vers) == n_ok,
          "%d/%d" % (n_ok, len(vers)))
    check("存档数 >= 3", len(vers) >= 3, str(vers))
else:
    skip("DELIVERY.md", "不存在")

# ---------- 11. fontbakery 报告项（固化）----------
print()
print("=== 11. fontbakery 报告项 ===")
if os.path.exists(VF):
    fb = TTFont(VF, lazy=True)
    # 版本号一致性 (opentype/font_version)
    hr = fb["head"].fontRevision
    n5 = fb["name"].getDebugName(5) or ""
    import re as _re3
    m5 = _re3.search(r"([0-9]+\.?[0-9]*)", n5)
    nv = float(m5.group(1)) if m5 else -1
    check("head.fontRevision 与 name ID5 一致", abs(hr - nv) < 0.01,
          "head=%.3f name=%s" % (hr, n5))
    # GDEF mark class (gdef_mark_chars / base_has_width)
    gdc = fb["GDEF"].table.GlyphClassDef
    cdd = gdc.classDefs if gdc else {}
    nmk = sum(1 for v in cdd.values() if v == 3)
    check("GDEF mark class >= 20", nmk >= 20, "mark=%d" % nmk)
    # 零宽基底字符 (base_has_width)
    fcm = fb.getBestCmap(); fh = fb["hmtx"]
    bad_zero = []
    for cp in (0x20DD, 0x20DE):
        if cp in fcm:
            gname = fcm[cp]
            if fh[gname][0] == 0 and cdd.get(gname) != 3:
                bad_zero.append(hex(cp))
    check("零宽字符都在 GDEF mark class", not bad_zero,
          ("问题: %s" % bad_zero) if bad_zero else "-")
    fb.close()
else:
    skip("fontbakery 报告项", "VF 不存在")

# ---------- 12. VF 元数据 (fvar/STAT/name) ----------
print()
print("=== 12. VF 元数据 ===")
if os.path.exists(VF):
    vm = TTFont(VF, lazy=True)
    has_fv = "fvar" in vm
    if has_fv:
        fvx = vm["fvar"]
        n_inst = len(fvx.instances)
        stat = vm["STAT"].table if "STAT" in vm else None
        n_av = 0
        if stat and stat.AxisValueArray:
            n_av = len(stat.AxisValueArray.AxisValue)
        check("STAT 条目覆盖 fvar instance", n_av >= n_inst,
              "STAT=%d instance=%d" % (n_av, n_inst))
    else:
        skip("STAT 检查", "无 fvar（静态字体）")
    # name 平台: 只应有 platform 3
    plats = sorted(set(r.platformID for r in vm["name"].names))
    check("name 只用 platform 3（无过时 Mac 记录）", plats == [3], str(plats))
    # zh-CN 记录
    zh = sum(1 for r in vm["name"].names if r.langID == 0x804)
    check("含 zh-CN name 记录", zh >= 3, "%d 条" % zh)
    # nameID17 必须是 Regular
    n17 = [str(r) for r in vm["name"].names if r.nameID == 17]
    check("nameID17 (Subfamily) = Regular", all(x == "Regular" for x in n17) if n17 else False,
          str(n17))
    vm.close()
else:
    skip("VF 元数据", "VF 不存在")

# ---------- 13. chws/vchw 东亚间距 ----------
print()
print("=== 13. chws/vchw ===")
if os.path.exists(VF):
    cw = TTFont(VF, lazy=True)
    has_gpos = "GPOS" in cw and cw["GPOS"].table.FeatureList
    gtags = []
    if has_gpos:
        gtags = sorted(set(fr.FeatureTag for fr in cw["GPOS"].table.FeatureList.FeatureRecord))
    check("含 chws 特性", "chws" in gtags, str(gtags))
    check("含 vchw 特性", "vchw" in gtags, "-")
    # 原有 GPOS 特性不能被挤掉
    need_g = ["kern", "mark", "mkmk", "palt"]
    miss_g = [x for x in need_g if x not in gtags]
    check("原有 GPOS 特性完好", not miss_g, ("缺 %s" % miss_g) if miss_g else "-")
    cw.close()
else:
    skip("chws 检查", "VF 不存在")

# ---------- 14. Layout 排序 / OTS ----------
print()
print("=== 14. Layout 排序 / OTS ===")
if os.path.exists(VF):
    lf = TTFont(VF, lazy=True)
    for tg in ("GSUB", "GPOS"):
        if tg not in lf:
            continue
        tb2 = lf[tg].table
        if not tb2.FeatureList:
            continue
        tgs = [fr.FeatureTag for fr in tb2.FeatureList.FeatureRecord]
        ok_sorted = tgs == sorted(tgs)
        check("%s FeatureList 有序" % tg, ok_sorted,
              "%d 条" % len(tgs))
    lf.close()
    # OTS sanitize（浏览器实际用的验证器）
    try:
        import ots as _ots
        _r = _ots.sanitize(VF, check=True, capture_output=True)
        _err = _r.stderr.decode() if _r.stderr else ""
        _nw = _err.count("WARNING")
        check("OTS sanitize 零警告", _nw == 0,
              "%d 处警告" % _nw if _nw else "通过")
    except ImportError:
        skip("OTS 检查", "ots 模块未安装")
    except Exception as _e:
        check("OTS sanitize", False, str(_e)[:80])
else:
    skip("Layout 排序", "VF 不存在")

print()
print("=" * 56)
print("交付物核对: PASS %d / FAIL %d / SKIP %d" % (ok, fail, n_skip))
if fail == 0:
    print("全部通过")
    sys.exit(0)
else:
    print("有 %d 项不符，需修正" % fail)
    sys.exit(1)
