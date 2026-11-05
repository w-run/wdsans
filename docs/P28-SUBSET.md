P28：WOFF2 子集化方案 —— 实测可行，0.81 MB 起

这是用户反复提出的待决问题的实测答案。

## 一、体积实测（决定性数据）

用 hb-subset + fontTools 对 WDesignSansSC-Regular 做子集，转 WOFF2：

| 方案 | 字符数 | WOFF2 体积 | 相对原文件 |
|---|---|---|---|
| 原始全字库 | 44,810 码位 | **7.49 MB** | 基准 |
| 3500 汉字 + 拉丁 | 4,027 | **0.81 MB** | **-89%** |
| 6763 汉字 + 拉丁 | 7,290 | **1.53 MB** | -80% |
| 全 CJK 基本区 | 21,503 | 5.14 MB | -31% |

拉丁部分包含：ASCII + Latin-1 + Latin Extended-A（带重音字母）。

**结论：3500 字档 0.81 MB，对网页完全可以接受。**

## 二、子集化的三个真实陷阱（都踩过）

### 陷阱 1：`--keep-everything` 会让子集完全失效

加了该参数后输出与原文完全相同（20.97 MB / 44,810 cmap / 65,535 字形）。
它的语义是「全部保留」，与子集目标相反。

### 陷阱 2：特性会被裁剪

| 方案 | GSUB 特性 | GPOS 特性 |
|---|---|---|
| 原始 | 16 | 8 |
| hb-subset + `--no-layout-closure` | 10 | **1（只剩 vert，kern 丢失）** |
| **fontTools subset API** | 10 | **6（halt/kern/palt/vert/vhal/vpal）** |

**必须用 fontTools 的 Python API，不能用 hb-subset CLI** —— 
hb-subset 即使加 `--layout-features=*` + `--no-layout-closure` 也会丢掉 kern。

### 陷阱 3：测试字符集必须显式包含用例字符

`骨`（locl 测试）、`（）「」`（vert 测试）如果不在字符集里，
子集后会变成 gid0（豆腐块）。这不是 bug，是子集的正常行为。

## 三、功能完整性验证

子集前后逐项对比（gid 编号变化属正常重编号，看字形与 advance）：

| 测试 | 原 | 子集 | 判定 |
|---|---|---|---|
| 国（汉字） | gid13185 +1000 | gid4198 +1000 | ✅ 同字形同宽度 |
| 骨（locl 繁体） | gid45134 | gid36111 | ✅ 正确映射繁体形 |
| （（竖排 vert） | -500,-868 / -1000 | -500,-868 / -1000 | ✅ 偏移一致 |
| Hamburg | 7 段 | 7 段 | ✅ **完全一致** |
| AV（kern） | 621/632 | 621/632 | ✅ **kern 保住** |
| fi（连字） | gid58975 +600 | gid38635 +600 | ✅ 连字生效 |

### 丢失的 6 个 GSUB 特性实际影响

| 特性 | 作用的 script | 对本字体影响 |
|---|---|---|
| `ljmo` | hang（韩文） | 无（不做韩文）|
| `tjmo` | hang | 无 |
| `vjmo` | hang | 无 |
| `calt` | 全部 | 轻微（上下文替代，中文少用）|
| `hist` | 全部 | 轻微（历史字形，中文少用）|
| `ruby` | 全部 | 轻微（注音，需特定字形）|

3 个韩文特性无影响，3 个「轻微」特性在中文排版中极少使用。
**可接受。**

## 四、推荐方案

### 方案 A（推荐）：双档发布

```
主文件（Web 默认）  3500 汉字 + 拉丁   0.81 MB  WOFF2
备用（生僻字场景）  6763 汉字 + 拉丁   1.53 MB  WOFF2
桌面/设计          全字库 7 档 TTF     20.93~21.00 MB
```

### 方案 B：单一 6763 档

1.53 MB 覆盖 GB2312 全集，一个文件搞定。
代价：比 3500 档大 0.7 MB。

## 五、可直接执行的命令

```python
from fontTools import subset
from fontTools.ttLib import TTFont

SRC = "/data/build-cache/wdsans-dist/WDesignSansSC-Regular.ttf"
text = open("charset-3500.txt", encoding="utf-8").read()

opts = subset.Options()
opts.layout_features = ["*"]
opts.layout_scripts = ["*"]
opts.name_IDs = ["*"]
opts.name_languages = ["*"]
opts.name_legacy = True
opts.glyph_names = True
opts.notdef_outline = True
opts.drop_tables = []
opts.passthrough_tables = True

font = TTFont(SRC)
subsetter = subset.Subsetter(options=opts)
subsetter.populate(text=text)
subsetter.subset(font)
font.flavor = "woff2"
font.save("WDesignSansSC-Regular-subset.woff2")
```

## 六、待用户决策

子集范围需要用户定：
1. **3500 字**（0.81 MB）—— 覆盖日常使用，但生僻字会回退到系统字体
2. **6763 字**（1.53 MB）—— GB2312 全集，覆盖绝大多数场景
3. **不子集**（7.49 MB）—— 全字库，适合桌面/设计，不适合网页