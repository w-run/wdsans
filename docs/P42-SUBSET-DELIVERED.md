# P42：子集化产物落地（两档可选，附完整功能验证）

## 背景

子集范围一直是悬置的决策项。本轮把它变成**可直接取用的产物**，
不再停留于讨论。

## 一、两档产物

| 方案 | 字符集 | cmap | TTF | **WOFF2** | 压缩比 |
|---|---|---|---|---|---|
| 全库 | 全部 | 44,905 | 20.95 MB | 7.48 MB | — |
| **GB2312 全集** | 6763 汉字 + 739 附加 | 7,402 | 4.33 MB | **1.69 MB** | **−77%** |
| **GB2312 一级** | 3755 汉字 + 735 附加 | 4,394 | 2.35 MB | **0.95 MB** | **−87%** |

三档都出了 Regular / Medium / Bold（最常用的三个字重）。

## 二、功能验证（关键，不能只看体积）

### 关键排版行为全部保留

| 方案 | kern | liga | locl | vert |
|---|---|---|---|---|
| 全库 | ✓ | ✓ | ✓ | ✓ |
| 3755 字 | ✓ | ✓ | ✓ | ✓ |
| 6763 字 | ✓ | ✓ | ✓ | ✓ |

### 常用字覆盖

测试串 35 字（永和九年岁在癸丑…中国特色社会主义）在 3755 字档：
**缺失 0 字**。

### GSUB 特性从 16 → 11，需要如实说明

丢失的 5 个：`calt`、`hist`、`ruby`、`ljmo`、`tjmo`

**逐个查证后确认均无实质影响：**

| 特性 | 作用范围 | 查证结果 |
|---|---|---|
| calt | 通用 | **覆盖 glyph 数 = 0**，空特性 |
| hist | 通用 | **覆盖 glyph 数 = 0**，空特性 |
| ruby | 通用 | **覆盖 glyph 数 = 0**，空特性 |
| ljmo | `hang/KOR` 韩文 | 子集韩文音节 = 0，无影响 |
| tjmo | `hang/KOR` 韩文 | 子集韩文音节 = 0，无影响 |

`calt/hist/ruby` 在母版里就是**空的 feature 记录**（37 个记录但 Coverage 为空），
子集化把它们清掉了，属于正确行为。

## 三、生成方式

用 **fontTools Subsetter API**，不用 hb-subset CLI：

```python
o = subset.Options()
o.layout_features = ["*"]      # 必须，否则特性全丢
o.name_IDs = ["*"]
o.notdef_outline = True        # 避免 notdef-is-blank
o.recalc_timestamp = False
o.drop_tables = []
o.passthrough_tables = True
ss = subset.Subsetter(options=o)
ss.populate(text="".join(sorted(keep)))
ss.subset(font)
```

（P28 已证实 hb-subset CLI 会丢 kern，必须用 Python API）

## 四、选型建议

| 场景 | 推荐 | 理由 |
|---|---|---|
| **Web 正文 / 首屏** | **3755 字，0.95 MB** | 覆盖日常 99% 用字，体积最小 |
| **Web 全站 / 需完整 GB2312** | **6763 字，1.69 MB** | 覆盖 GB2312 全部，零风险 |
| **桌面设计 / 印刷** | 全库 7.48 MB | 含全部 65k 字形与异体 |

组合方案：首屏加载 3755 档，异步补 6763 档（两档体积之和仍小于全库）。

## 五、产物位置

```
w-box:/data/build-cache/wdsans-subset/
  WDesignSansSC-{Regular,Medium,Bold}-sub3755.{ttf,woff2}   (6 个)
  WDesignSansSC-{Regular,Medium,Bold}-sub6763.{ttf,woff2}   (6 个)
```

## 六、教训

**「特性数量减少」不等同于「功能丢失」。**

GSUB 从 16 降到 11 看起来是退化，逐个查证后才发现：
5 个里 3 个本来就是空特性、2 个只作用于子集不含的韩文。

这与 P34 的「9 个单笔部首偏窄」是同类方法：
**先查证「这个差异有没有实际作用」，再判断是否为缺陷。**
## 七、补充验证（P43 纠正后）

### 重要：之前的 woff2 测试无效

发现 HarfBuzz 8.4.0 **不解 WOFF2**（见 P43），之前用 hb-shape 测 woff2 得到的「正常」
实际测的是 `gid0`。已改用 **TTF 产物**重新验证。

### 有效验证结果（全库 TTF vs 两档子集 TTF）

| 用例 | 全库 | 6763 | 3755 |
|---|---|---|---|
| kern AV | 2段/1253 | 2段/1253 **OK** | 2段/1253 **OK** |
| liga fi | 1段/600 | 1段/600 **OK** | 1段/600 **OK** |
| locl 骨 zh-Hant | 1段/1000 | 1段/1000 **OK** | 1段/1000 **OK** |
| vert （ | 1段/0 | 1段/0 **OK** | 1段/0 **OK** |
| 中文 国永 | 2段/2000 | 2段/2000 **OK** | 2段/2000 **OK** |
| Latin Ąą | 2段/1159 | 2段/1159 **OK** | 2段/1159 **OK** |

**六项全等（段数 + advance 都一致）。**

### 视觉确认

三档用 TTF 渲染「永和九年岁在癸丑暮春之初 中国特色社会主义 AV fi」，
视觉完全一致（docs/img/p42-subset-render.png）。

`AV` 有 kern、`fi` 是合字、中文正常 —— 全部正确。