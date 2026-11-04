# P5：命名、STAT 与交付流水线

> 2026-11-05 · 本轮把字体从「能看的产物」变成「能交付的字体」。

---

## 1. 改名（合规前提）

### 法律依据（实测 nameID 0）

```
© 2014-2021 Adobe (http://www.adobe.com/), with Reserved Font Name 'Source'
```

**保留字体名是 `Source`，不是 `Noto`。** 所以改名为 WDesign Sans 合法。
但 OFL 要求：改名后不得再声明 reserved name，且需保留版权/许可/作者署名。

### 处理清单

| nameID | 原值 | 处理 |
|---|---|---|
| 0 | Reserved Font Name 'Source' | **删除**（改名后不得保留） |
| 1/4/16 | Noto Sans CJK SC | WDesign Sans |
| 2/17 | Regular | 按实例改 |
| 6 | NotoSansCJKsc-Thin | WDesignSansSC-Regular |
| 3 | 2.004;ADBO;NotoSansCJKsc-Thin;ADOBE | Version 1.000;WDGN;WDesignSansSC-Regular;WDGN |
| 7 | Source is a trademark of Adobe... | **删除**（上游商标声明，改名后不适用） |
| 8 | Adobe | WDesign |
| 9/10 | 西塚涼子、Ken Lunde | **保留**（OFL 要求署名） |
| 13/14 | OFL 许可与链接 | **保留** |
| 269-279 | NotoSansCJKsc-* | **删除**（旧 STAT 实例名） |

`OS/2.achVendID`: `ADBO` → `WDGN`。

**最终残留品牌字样：0 处**（脚本自动扫描确认）。

---

## 2. STAT 重建

旧 STAT 是六档（Light/DemiLight/Regular/Medium/Bold/Black），与新七档不匹配。
macOS / Windows 按 STAT 排字重菜单，不匹配会导致菜单错乱。

用 `fontTools.otlLib.builder.buildStatTable` 按七档重建：

```python
axes = [{"tag": "wght", "name": "Weight", "ordering": 0,
         "minimum": 250, "default": 400, "maximum": 900}]
values = [{"name": sub, "location": {"wght": wght}} for wght, sub in STOPS]
buildStatTable(font, axes, values, elidedFallbackName="Regular")
```

注意两个踩过的坑：
- `values` 要的是 `location` 字典，不是 `value`（否则 KeyError）
- Regular 要打 `flags=0x2`（Elidable），否则部分系统会显示成 "Regular Regular"

---

## 3. 七档静态实例（Style Linking）

Windows 只认 4 个 RIBBI 子族，非 RIBBI 档必须用 nameID 16/17 做排版族名，
否则七档会全塞进同一个 "WDesign Sans" 里、无法单独选择。
这是 fontbakery / Google Fonts 的标准做法。

### 结果验证

| 档位 | wght | nameID 1 | nameID 16/17 | usWeightClass | macStyle |
|---|---|---|---|---|---|
| Thin | 250 | WDesign Sans Thin | WDesign Sans / Thin | 250 | 0 |
| Light | 300 | WDesign Sans Light | WDesign Sans / Light | 300 | 0 |
| Normal | 350 | WDesign Sans Normal | WDesign Sans / Normal | 350 | 0 |
| **Regular** | 400 | **WDesign Sans** | WDesign Sans / Regular | 400 | 0 |
| Medium | 500 | WDesign Sans Medium | WDesign Sans / Medium | 500 | 0 |
| **Bold** | 700 | **WDesign Sans** | WDesign Sans / Bold | 700 | **1** |
| Heavy | 900 | WDesign Sans Heavy | WDesign Sans / Heavy | 900 | 0 |

RIBBI 档（Regular/Bold）用裸族名，非 RIBBI 档用「族名+样式」——完全正确。
静态实例已移除 fvar/gvar/avar/STAT/HVAR。

---

## 4. 产物清单

`/data/build-cache/wdsans-dist/`

| 文件 | 大小 |
|---|---|
| WDesignSansSC-{Thin,Light,Normal,Regular,Medium,Bold,Heavy}.ttf | 各 ~21-22 MB |
| WDesignSansSC-*.woff2 | 生成中 |
| WDesignSansSC-VF.woff2 | 生成中 |

**七档 TTF 合计 146.8 MB。** 这是 65,524 个字形的必然体积——
网页使用必须子集化（后续项）。

---

## 5. 验收证据

1. **视觉**：七档并排渲染，字重递进清晰、无跳变（`seven.png`）
2. **元数据**：nameID / STAT / wClass / macStyle 逐项核对（见上表）
3. **合规**：品牌字样残留 0 处（脚本自动扫描）

---

## 6. 下一轮

- [ ] WOFF2 体积测量（若单档仍 >8MB，需要子集化方案）
- [ ] Mona Sans 拉丁合并（用户五决策之一）
- [ ] 竖排 vmtx/vhea 检查
- [ ] 全字库 GSUB/GPOS 未被删减的最终确认
