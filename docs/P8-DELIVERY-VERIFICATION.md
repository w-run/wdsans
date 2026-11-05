P8：交付产物验证（WOFF2 可解码、竖排完整、七档实例含复合字形）

## 本轮验证结论（全部基于实测）

1. WOFF2 可解码：Thin 解码后 17 表 / 44810 cmap / 65535 glyph。
   > **P43 更正（2026-11-06）**：原写「hb-view 渲染成功」是**错的**。
   > HarfBuzz 8.4.0 不解 WOFF2 容器（返回 gid0），当时的「渲染成功」实为空白。
   > 正确的验证方式是先 `TTFont(...).flavor=None` 解包成 TTF 再渲染。
   > 本条正确的部分是「fontTools 能解码」，这一点仍然成立。
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

用 fontTools 的 `instancer.instantiateVariableFont` 读 advance width 是**错的**：
它实例化时会**丢掉 HVAR 表**，只剩 gvar phantom 那一份 delta，
与 HarfBuzz（优先用 HVAR）的真实渲染值不一致。必须用 `hb-shape` / `hb-view` 测。

实测对照（字形 H，本字体）：

| 来源 | 250 | 400 | 700 | 900 |
|---|---|---|---|---|
| `instancer` → `hmtx` | 678 | 684 | 694 | 700 |
| **hb-shape（真值）** | **663** | **684** | **713** | **730** |

### ⚠️ 更正：HVAR 确实有问题，不是「测量方法错误」

本文初稿写成「这个假象一度让我以为 HVAR 有问题，实际是测量方法错误」——**后半句是错的，现已更正。**

HVAR 是真实缺陷，实测证据：

```
本字体 HVAR 的 advance delta 与合并前 Noto 逐字形完全相同（抽样 200 个：same=200, diff=0）
  H  ours hmtx 684 + HVAR[+46,-21]  ==  Noto hmtx 728 + HVAR[+46,-21]
  T  ours hmtx 576 + HVAR[+41,-18]  ==  Noto hmtx 599 + HVAR[+41,-18]
  o  ours hmtx 532 + HVAR[+31,-14]  ==  Noto hmtx 606 + HVAR[+31,-14]
```

也就是：**base 换成了 Mona，delta 还是 Noto 的**。真实 advance = Mona base + Noto delta，
既不是 Noto 也不是 Mona：

| 字形 | base(Mona×0.895) | HVAR 后 @900 | 应为(Mona@900×0.895) | 误差 |
|---|---|---|---|---|
| H | 684 | 730 | 700 | **+30** |
| T | 576 | 617 | 572 | **+45** |
| o | 532 | 563 | 539 | **+24** |

**所以「两个测法数字不同」这件事本身，既证明了测量口径问题，也暴露了 HVAR 未重建这个真 bug。**
不能因为换对工具就宣布没问题——换对工具之后读到的 730 里，有 30 是错的。
修复函数 `wds/hvar_fix.py` 已写好但**未接入构建**。

详见 `docs/P7-COMPOSITE-INLINE.md` §4 与 §6-1。