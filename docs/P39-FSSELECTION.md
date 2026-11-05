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