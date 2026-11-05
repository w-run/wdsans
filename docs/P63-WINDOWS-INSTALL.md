# P63：Windows 系统安装与家族分组验证

## 动机

此前只验证了「浏览器能否加载」（P48 OTS / P56 Chrome）。
但用户很可能**双击安装到 Windows 系统**，这条路径从未验证。

## 一、安装前提：基础元数据

| 项 | 值 | 要求 | 判定 |
|---|---|---|---|
| `fsType` | **0** | 0 = Installable Embedding，可自由安装 | ✓ |
| `OS/2.version` | 3 | 支持 Unicode 范围位 | ✓ |
| `unitsPerEm` | 1000 | 标准 | ✓ |
| `usWeightClass` | 250-900 | 与档位对应 | ✓ |
| `usWidthClass` | 5 | Normal | ✓ |

`fsType=0` 是关键：若为 2/4/8（受限嵌入）会阻碍安装。

## 二、家族分组：一个看似缺陷的设计

七个字重的 name 表：

| 档位 | ID1（族名）| ID2（子族）| ID16（排版族）| ID17（排版子族）|
|---|---|---|---|---|
| Thin | **WDesign Sans Thin** | Thin | WDesign Sans | Thin |
| Light | **WDesign Sans Light** | Light | WDesign Sans | Light |
| Normal | **WDesign Sans Normal** | Normal | WDesign Sans | Normal |
| Regular | WDesign Sans | Regular | WDesign Sans | Regular |
| Medium | **WDesign Sans Medium** | Medium | WDesign Sans | Medium |
| Bold | WDesign Sans | Bold | WDesign Sans | Bold |
| Heavy | **WDesign Sans Heavy** | Heavy | WDesign Sans | Heavy |

### 第一眼：ID1 有 6 个不同值，看起来会分裂成 6 个家族

像是个严重问题——用户在字体列表里会看到：
```
WDesign Sans
WDesign Sans Thin
WDesign Sans Light
WDesign Sans Normal
WDesign Sans Medium
WDesign Sans Heavy
```

### 查文档：这是有意设计

`docs/P5-NAMING-DELIVERY.md` 第 61-63 行明确记载：

> Windows 只认 4 个 RIBBI 子族，非 RIBBI 档必须用 nameID 16/17 做排版族名，
> 否则七档会全塞进同一个 "WDesign Sans" 里、无法单独选择。
> 这是 fontbakery / Google Fonts 的标准做法。

**关键约束**：Windows GDI 的子族名（ID2）**只接受 4 个值**：

| ID2 允许值 |
|---|
| Regular |
| Bold |
| Italic |
| Bold Italic |

**`Thin` / `Light` / `Medium` / `Heavy` 都不在允许列表内。**

若强行把 ID2 设成 "Thin"，GDI 会**忽略**它，七个档全部落进
同一个 "WDesign Sans / Regular"，用户根本选不出字重。

### 两个可选方案

| 方案 | ID1 | ID2 | 结果 |
|---|---|---|---|
| A. 全塞一个家族 | 全 "WDesign Sans" | 全 "Regular" | **7 个同名冲突，无法选择** |
| B. **非 RIBBI 独立家族**（我们采用）| "WDesign Sans Thin" 等 | Thin 等 | **6 个家族，但每个都能选** |

**方案 B 是唯一可行的。**

## 三、参照字体的做法（关键证据）

| 字体 | ID1 | ID2 | ID16 | ID17 |
|---|---|---|---|---|
| **OPPO 400** | **OPPOSans R** | Regular | OPPOSans | Regular |
| **OPPO 700** | **OPPOSans B** | Regular | OPPOSans | Bold |
| SHS 250 | **Source Han Sans SC Ext** | Regular | Source Han Sans | ExtraLight |
| SHS 300 | **Source Han Sans SC Lig** | Regular | Source Han Sans | Light |
| SHS 400 | Source Han Sans SC | Regular | — | — |
| 鸿蒙 400 | HarmonyOS Sans SC | Regular | — | — |
| 鸿蒙 700 | HarmonyOS Sans SC | Bold | — | — |

### 结论：三家里两家用同样策略

- **OPPO**：`OPPOSans R` / `OPPOSans B` —— **不同 ID1**，且 ID2 都是 Regular
- **Source Han Sans**：`... SC Ext` / `... SC Lig` —— **不同 ID1**
- **鸿蒙**：只有 Regular/Bold 两档，都在 RIBBI 内，所以能同族

**鸿蒙之所以能同族，是因为它只有 2 档且都在 RIBBI 允许范围内。**
我们 7 档无法照搬。

## 四、验证：ID16/ID17 正确设置

所有 7 档的 ID16 都是 `WDesign Sans`、ID17 对应各自字重。

这意味着支持 **OpenType 排版族名**的现代应用（如 Adobe 系列、
现代浏览器 CSS `font-family: "WDesign Sans"; font-weight: 500`）
能正确把它们归为同族并选到对应字重。

## 五、结论

| 项 | 结果 |
|---|---|
| `fsType` | 0，可自由安装 ✓ |
| OS/2 / head 元数据 | 全部合规 ✓ |
| ID1 有 6 个值 | **设计如此，非缺陷** |
| ID16/17 | 7 档全部正确设置 ✓ |
| 与 OPPO/SHS 对比 | **采用相同策略** ✓ |
| Windows 安装 | 预期可正常安装，选字重通过「家族名 + 字重」两级 |

## 六、教训

**「看起来不对」和「实际不对」是两件事。**

看到 6 个不同的 ID1，第一反应是「家族分裂，需要修」。
但 30 秒后查文档就发现：这是 P5 早已论证过的设计，
而且 OPPO / Source Han Sans 都这么做。

**如果当时直接动手「修」成统一 ID1，反而会破坏可用性**——
七个档会挤成一个，用户选不出字重。

这与 P47（字重非线性）、P53（减细比率）、P54（横竖比）是同一类：
**先查设计意图和参照做法，再判断是否缺陷。**