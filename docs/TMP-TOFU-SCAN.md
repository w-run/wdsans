# TMP-TOFU-SCAN：全码位空白字形（豆腐块）扫描

> 对象：/data/build-cache/wdsans-dist/WDesignSansSC-Regular.ttf（TTF，19.2 MB，65535 glyphs，upm 1000）
> 工具：uharfbuzz 0.57 + FreeType 2.12（像素渲染）+ fontTools 4.67；交叉验证用 hb-shape CLI 8.4.0
> 时间：2026-11-06

## 一、结论（TL;DR）

**没有豆腐块。排除合法空白后，空白字形数量 = 0。**

- cmap 覆盖 **44905** 个码位（format 12；format 4 的 42315 个全部是它的 BMP 子集，两者零差异）
- 逐码位 hb-shape：**44905 / 44905 全部得到非 gid0**，gid0 数量 **= 0**
- 逐码位 FreeType 实际渲染（100px，NO_HINTING）：**44895** 个有墨量像素，**10** 个为 0 像素
- 那 10 个里 **9 个是合法空白字符**（见第二节），第 10 个 U+00AD 是 HarfBuzz 的软连字符特判，字体里其实是真实连字符字形
- 因此 **空白码位清单为空**（0 个）

## 二、空白码位明细（共 10 个，全部合法）

| 码位 | 名称 | 类别 | gid | 字形名 | advance | 墨量@100px | 判定 |
|---|---|---|---|---|---|---|---|
| U+0020 | SPACE | Zs | 1 | space | 224 | 0 | 合法空格 |
| U+00A0 | NO-BREAK SPACE | Zs | 1 | space | 224 | 0 | 合法空格（与 U+0020 共用 space）|
| U+2002 | EN SPACE | Zs | 63164 | uni2002 | 500 | 0 | 合法空格（专属空白字形）|
| U+2003 | EM SPACE | Zs | 1396 | uni2003 | 1000 | 0 | 合法空格 |
| U+3000 | IDEOGRAPHIC SPACE | Zs | 1396 | uni2003 | 1000 | 0 | 合法全角空格（与 U+2003 共用）|
| U+115F | HANGUL CHOSEONG FILLER | Lo | 467 | uni115F | 920 | 0 | 合法（谚文初声填充符，规范即空白）|
| U+1160 | HANGUL JUNGSEONG FILLER | Lo | 468 | uni1160 | 920 | 0 | 同上 |
| U+3164 | HANGUL FILLER | Lo | 468 | uni1160 | 920 | 0 | 同上 |
| U+FFA0 | HALFWIDTH HANGUL FILLER | Lo | 468 | uni1160 | 920 | 0 | 同上 |
| U+00AD | SOFT HYPHEN | Cf | hb→1(space) | — | 0 | 0 | **误报，非空白**（见下）|

**U+00AD 说明**：HarfBuzz 按 UAX #14 对 SOFT HYPHEN 特判：直接输出 space 字形且 advance=0，所以 hb 侧看到的是“空白”。
但 cmap 里 U+00AD 实际映射到 hyphen（gid 720，墨量 100px），字体本身是正常连字符，不是豆腐。这是 hb 的行为，不是字体缺陷。

> 交叉验证：多字号（12 / 16 / 24 px）全码位重扫，空白数恒为 9（即上表去掉 U+00AD 的 9 个），
> 说明 U+00AD 的空白纯粹来自 hb 特判，与栅格化无关。

## 三、四道独立验证（互不依赖）

| # | 方法 | 结果 |
|---|---|---|
| 1 | uharfbuzz hb.shape 逐码位 44905 次 | gid0 = **0** |
| 2 | hb-shape CLI 批量 500 随机码位 | gid0 = **0**，gid 与 #1 完全一致 |
| 3 | FreeType 65535 glyph 逐个 load_glyph+render 数非零像素 | 零墨量仅 **10** 个，全部为上表 |
| 4 | fontTools RecordingPen 逐字形数绘图指令 | 零路径指令仅 **9** 个，全部为合法空白（U+00AD 不在其中，反证其为真字形）|

#1 与 #4 的差集恰好只有 U+00AD，说明空白判定只源于 hb 特判，字体轮廓层面不存在空字形。

## 四、方法说明与陷阱规避

- **只用 TTF**：hb-shape 对 WOFF2 会静默返回 gid0（METHOD-TRAPS 陷阱 2）。本次直接扫 TTF，避开该陷阱。
- **未用 AreaPen**：墨量一律来自实际栅格化像素计数（FT_RENDER_MODE_NORMAL，100px，FT_LOAD_NO_HINTING | NO_AUTOHINT），避免绕向导致的内外轮廓加减抵消（陷阱 1）。
- **两个 gid 通道一致性**：FreeType.get_char_index 与 hb 的 gid 全量对比，仅 U+00AD 不同（原因同上），其余 44904 个完全一致。
- **额外形态学筛查（确认非豆腐）**：按轮廓数 ≤2、bbox ≥850x850 筛“空心方框”候选，共 129 个，逐个核对后全部是设计上就该空心/实心的字符：
  U+25A1 □、U+25A2 ▢、U+25B3 △、U+25B7 ▷、U+25BD ▽、U+25C1 ◁、U+25C7 ◇（几何图形）、
  U+20DD/U+20DE（组合圈/方框）、U+2500–259F 制表符与方块元素（U+2588 █ 等）。**无一个 .notdef 式豆腐框。**
   另有一个假阳性 U+30E1 メ（两笔，被轮廓数规则误命中）。
- **最低墨量抽查**（100px）：最低几个是 U+119E(56)、U+FE52(96)、U+2010(100)、U+11A2(110)、U+002E(118)，都是正常出墨的小字符，非空白。

## 五、附带发现（非豆腐，供参考）

cmap **缺少**以下常用空白码位，浏览器会回退到系统字体（不产生豆腐，但宽度不可控）：

U+2000 EN QUAD、U+2001 EM QUAD、U+2004–U+200A（THREE-PER-EM 到 HAIR SPACE，共 7 个）、U+202F NARROW NO-BREAK SPACE、U+205F MEDIUM MATHEMATICAL SPACE、U+1680 OGHAM SPACE MARK。

其中正文排版常用的 **U+2009 THIN SPACE**、**U+200A HAIR SPACE**、**U+202F** 缺位，若要完全控制西文间距建议后续补齐（属覆盖缺口，不是渲染缺陷）。

## 六、复现命令

```bash
/workspace/wdsans/venv/bin/python /workspace/wdsans/tools/tofu_scan.py   # 全量：cmap + hb + FreeType 像素
# 结果 JSON: /tmp/tofu_scan_result.json
```
