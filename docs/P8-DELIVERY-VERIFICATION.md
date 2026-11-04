P8：交付产物验证（WOFF2 可解码、竖排完整、七档实例含复合字形）

## 本轮验证结论（全部基于实测）

1. WOFF2 可解码：Thin 解码后 17 表 / 44810 cmap / 65535 glyph，hb-view 渲染成功。
   7 档 WOFF2 体积 7.48-7.94 MB，VF WOFF2 20.03 MB。

2. 七档静态实例均含合并后的拉丁（含复合字形）：
   Thin   A=537 Á=537    Light  A=542 Á=542    Normal A=586 Á=586
   Regular A=594 Á=594   Medium A=615 Á=615    Bold   A=643 Á=643
   Heavy  A=670 Á=670   -> 与对应无重音字母宽度完全一致，且随字重递增。

3. 竖排完整：vhea(500/-500) + vmtx(65158 条) + GSUB vert/vrt2 均在。
   vhal/vpal 缺失是上游 Noto 原版即如此（横排变体特性，CJK 排版不依赖）。

4. 度量与命名：typo 880/-120、win 1160/288、xHeight 543、capHeight 733、
   usWeightClass 400、achVendID WDGN、fvar 7 实例、STAT 7 档。

## 交付清单 /data/build-cache/wdsans-dist/

| 文件 | 大小 |
|---|---|
| WDesignSansSC-{Thin,Light,Normal,Regular,Medium,Bold,Heavy}.ttf | 20.93-21.00 MB |
| WDesignSansSC-*.woff2 | 7.48-7.94 MB |
| WDesignSansSC-VF.woff2 | 20.03 MB |

VF 源：/data/build-cache/wdsans-p1/wdsans-FINAL.ttf（50.3 MB）

## 踩坑记录（重要）

用 fontTools 的 instancer.instantiateVariableFont 读 advance width 是**错的**：
它不会应用 HVAR，会读到 hmtx 的 base 值（对 H 恒为 675/684），
从而误判「advance 不随字重变化」。必须用 hb-shape 或 hb-view 测真实渲染值。

这个假象一度让我以为 HVAR 有问题，实际是测量方法错误。