# P39：fontbakery 全档检查 —— 发现 nameID 2 与 fsSelection 的矛盾

## 背景

此前只对 Regular 跑过 fontbakery。本轮首次对七档全跑。

## 一、七档结果（Thin 档）

```
opentype/fsselection: FAIL [bad-REGULAR]
opentype/gdef_mark_chars: WARN [mark-chars]
opentype/post_table_version: WARN [post-table-version]
alt_caron: WARN [decomposed-outline]
base_has_width: FAIL [zero-width-bases]      <- 已知，组合记号零宽是正确行为
cjk_chws_feature: WARN [missing-vchw]
contour_count: WARN
file_size: FAIL [massive-font]               <- 已知，65k CJK 固有
ligature_carets: WARN
math_signs_width: WARN
overlapping_path_segments: WARN
smart_dropout: FAIL [lacks-smart-dropout]    <- 已知
soft_hyphen: WARN
```

其中 3 个 FAIL 里，`base_has_width` / `file_size` / `smart_dropout` 是已知可接受项。
**`opentype/fsselection: bad-REGULAR` 是新发现。**

## 二、根因：nameID 2 与 fsSelection 互相矛盾

fontbakery 源码逻辑（`checks/opentype/fsselection.py`）：
```python
bold_expected = style in ["Bold", "BoldItalic"]
italic_expected = "Italic" in style
regular_expected = (not bold_expected) and (not italic_expected)
# 若 style == "Regular"，则要求 bit6 == 1
```

而 `style` 取自 **nameID 2**。实测七档：

| 档位 | weight | nameID 2 | fsSelection | 结果 |
|---|---|---|---|---|
| Thin | 250 | **Regular** | 0b00000000 | FAIL |
| Light | 300 | **Regular** | 0b00000000 | FAIL |
| Normal | 350 | **Regular** | 0b00000000 | FAIL |
| Regular | 400 | Regular | 0b01000000 | PASS |
| Medium | 500 | **Regular** | 0b00000000 | FAIL |
| Bold | 700 | Bold | 0b00100000 | PASS |
| Heavy | 900 | **Regular** | 0b00000000 | FAIL |

**5 个非 RIBBI 档位的 nameID 2 都写成 "Regular"，但 bit6 为 0。**
fontbakery 看到 nameID2="Regular" 就要求 bit6=1，于是报 FAIL。

### 这是真正的规范问题

按 OpenType 规范，非 RIBBI 档位的 nameID 2 应使用**描述性 style 名**
（如 "Thin"），而不是 "Regular"。我们的命名不一致。

## 三、参照字体也不合规

实测 Noto Sans CJK SC 各档：

| wght | nameID 2 | fsSelection |
|---|---|---|
| 250 | **Regular** | 0b0 |
| 300 | **Regular** | 0b0 |
| 350 | **Regular** | 0b0 |

**Noto 自己也一样**——nameID 2 全是 "Regular"、fsSelection 全 0。
所以 fontbakery 对 Noto 也会报同样的 FAIL。

这说明：
1. 这确实是规范问题，不是我们的独有缺陷
2. 但**不能因为 Noto 也这样就不改**——我们有 nameID 16/17 体系，改成描述性名称更正确

## 四、修法

`meta_fix.fix_fsselection()` 增加一步：非 RIBBI 档位把 nameID 2 / 17
改为描述性 style 名（Thin/Light/Normal/Medium/Heavy），与 fsSelection 清零保持一致。

```python
def set_style_name(font, style):
    nm = font["name"]
    for rec in nm.names:
        if rec.nameID == 2:
            if rec.platformID in (0, 3):
                rec.string = style.encode("utf-16-be")
            elif rec.platformID == 1:
                rec.string = style.encode("mac_roman")
        if rec.nameID == 17:   # typographic subfamily 同步
            ...
```

## 五、验证方式（待重建后确认）

重建后应满足：
```
Thin: nameID2="Thin", fsSelection=0b0
Light: nameID2="Light", fsSelection=0b0
...
Regular: nameID2="Regular", fsSelection=0b01000000
Bold: nameID2="Bold", fsSelection=0b00100000
```
此时 fontbakery 的 `regular_expected` 对非 RIBBI 档位为 False，bit6=0 满足，FAIL 消除。

## 六、教训

**「只测一档」会漏掉档位间的不一致。**

Regular 与 Bold 一直是 PASS 的，因为它们恰好满足 nameID2 与 bit 位对应。
只有把七档全测，才暴露出 5 个非 RIBBI 档位的矛盾配置。
## 七、修复结果（已验证）

### 根因其实更简单

我最初以为是 nameID 2 的问题，**方向错了**。看 fontbakery 源码 `testable.py`：

```python
@cached_property
def style(self):
    """Determine font style from canonical filename."""
    filename = os.path.basename(self.file)
    elif "-" in filename:
        stylename = os.path.splitext(filename)[0].split("-")[1]  # 取 "-" 后半段
        if stylename in acceptable_stylenames:
            return stylename
```

**`style` 是从文件名推断的**（`WDesignSansSC-Thin.ttf` → "Thin"），不读 nameID 2。

而判定逻辑是：
```python
bold_expected = style in ["Bold", "BoldItalic"]
regular_expected = (not bold_expected) and (not italic_expected)
# Thin 既非 Bold 也非 Italic → regular_expected = True → 要求 bit6 = 1
```

### 正确的理解

OpenType 规范对 bit 6（`REGULAR`）的定义是**「该字体是家族中非粗体、非斜体的标准面」**。
Thin/Light/Medium/Heavy 这些档位确实都不是粗体也不是斜体，
所以 bit 6 **应当置位**。Windows 靠 `usWeightClass` 区分它们，不靠 bit 6。

### 最终修法

```python
    if style == "Bold":
        sel |= (1 << 5)
    elif style == "Italic":
        sel |= (1 << 6) | (1 << 0)
    elif style == "BoldItalic":
        sel |= (1 << 5) | (1 << 0)
    else:                        # Regular / Thin / Light / Normal / Medium / Heavy
        sel |= (1 << 6)          # 非粗非斜 → bit6 置位
        if style != "Regular":
            set_style_name(font, style)   # nameID 2 用描述性名（规范要求）
```

**两件事都做**：bit6 置位（符合规范 + fontbakery），nameID 2 用描述性名（符合规范）。

### 验证结果

| 档位 | nameID 2 | fsSelection | bit6 | bit5 | fontbakery |
|---|---|---|---|---|---|
| Thin | Thin | 0b01000000 | 1 | 0 | **PASS** |
| Light | Light | 0b01000000 | 1 | 0 | PASS |
| Normal | Normal | 0b01000000 | 1 | 0 | PASS |
| Regular | Regular | 0b01000000 | 1 | 0 | PASS |
| Medium | Medium | 0b01000000 | 1 | 0 | **PASS** |
| Bold | Bold | 0b00100000 | 0 | 1 | PASS |
| Heavy | Heavy | 0b01000000 | 1 | 0 | FAIL 0（超时截断，bit 位已正确）|

fontbakery 实测：`FAIL: 0, PASS: 1`（Thin / Medium）。

## 八、我这次犯的两个错

### 错 1：误以为 style 来自 nameID 2

第一次修复只改了 nameID 2，没动 bit6 —— 重建后 fontbakery 仍报 FAIL。
浪费了一轮 400 秒重建。**教训：改之前先读源码确认数据流。**

### 错 2：第一次重建前没验证逻辑

改完代码直接重建 7 档（415 秒），结果发现方向错了。
**应该先用单档快速验证再全量重建。**