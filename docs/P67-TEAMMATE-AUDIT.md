# P67：队友审计结果的独立复核 + A4 修复

## 背景

本轮按目标要求启用 teammate（`otf-tables`）做了表结构审计，
报告 27 个文件，指出 7 项异常。

**按 P48 的教训（队友报过 ≠ 现在成立），我逐项独立复核。**

## 一、硬指标：全部确认

| 项 | 队友报告 | 我的复核 |
|---|---|---|
| 必需表 10 项 | 27/27 齐 | ✓ 一致 |
| 未知表/重复表 | 0/0 | ✓ 一致 |
| 静态档无 fvar | 是 | ✓ 一致 |
| VF 五表齐全 | fvar/gvar/HVAR/avar/STAT | ✓ 一致（22 表）|

## 二、7 项异常：逐项复核

### A4 命名冲突 —— **确认为真，且有上游先例**

```
VF.woff2        ID1=WDesign Sans  ID6=WDesignSansSC-Regular
Regular.ttf     ID1=WDesign Sans  ID6=WDesignSansSC-Regular   ← 完全相同
Regular.woff2   ID1=WDesign Sans  ID6=WDesignSansSC-Regular
```

**VF 与静态 Regular 的 name 表逐字相同，PS 名都是 `WDesignSansSC-Regular`。**

子集也一样：
```
Regular-sub3755.woff2   ID6=WDesignSansSC-Regular
Regular-sub6763.woff2   ID6=WDesignSansSC-Regular   ← 与全库同名
```

#### 查上游做法（决定性证据）

| 字体 | ID1 | ID6 |
|---|---|---|
| **MonaSansVF.ttf** | **Mona Sans VF** | **MonaSansVF-Regular** |
| MonaSans-Regular.otf | Mona Sans | MonaSans-Regular |
| NotoSansCJKsc-VF.ttf | Noto Sans CJK SC | NotoSansCJKsc-Thin |

**Mona 上游给 VF 的族名加了 "VF" 后缀**，正是为了避免与静态冲突。

这就是修复依据——不是我发明的做法，是跟随上游。

### A1/A2/A3 子集裁剪 —— 观察属实，但归因错误（见 P86/P87）

| 项 | 全库 | 子集（6763）| 队友说法 | 复核 |
|---|---|---|---|---|
| 表数 | 17 | **16** | — | ✓ |
| GDEF | 有 | 无 | A1 | P86 更正：无组合标记时的正常闭包裁减 |
| GSUB 特性 | 16 | 11 | P28 已记录 | ✓ |
| GPOS 特性 | 8 | 6 | A2 | P86 更正：特性数不随字符集变，非丢失 |
| GPOS lookup | 11 | 7 | A2 | ✓ |
| cmap 子表 | 6 | 2 | A3 | P87 更正：fmt12 需非BMP / fmt14 需变体选择符 |
| cmap format 14 (IVS) | 有 | 无 | A3 | P87 更正：需变体选择符在字符集内 |

A2 具体影响：~~竖排西文不 kern（vkrn 丢失）~~ — P86 更正：vkrn 未丢失。
A1 具体影响：**mark 定位失效**（若将来需要组合标记）。

### A6 fsSelection —— 确认属实

| 文件 | fsSelection | bit6(REGULAR) |
|---|---|---|
| 静态 Regular | 0b1000000 | **1** |
| **VF** | **0b0** | **0** ← 不一致 |

全部 27 个文件 bit7（USE_TYPO_METRICS）都是 0——
这一点在 P24 已论证过是**有意为之**（与 Noto/OPPO 一致），不是新问题。

### A5/A7 —— 已知设计，非缺陷

| 项 | 判定 |
|---|---|
| A5 静态家族不统一（5 个单成员家族）| **P63 已论证**：RIBBI 限制，且 OPPO/SHS 同样做法 |
| A7 VF 只有 woff2 无 ttf | 交付决策；VF.ttf 50MB 体积过大，Web 场景用 woff2 即可 |

## 三、修复 A4：给 VF 加 VF 后缀

参照 Mona 上游：

```python
CHANGES = {
    1:  "WDesign Sans VF",       # 族名
    3:  "WDesignSansSC-VF;2026.100;WDGN;WDesignSansSC-VF",  # 唯一标识
    4:  "WDesign Sans VF",       # 全名
    6:  "WDesignSansSC-VF",      # PostScript 名
    16: "WDesign Sans VF",       # 排版族名
}
```

修改前 → 修改后：

| ID | 修改前 | 修改后 |
|---|---|---|
| 1 | WDesign Sans | **WDesign Sans VF** |
| 3 | Version 1.000;WDGN;WDesignSansSC-Regular;WDGN | **WDesignSansSC-VF;2026.100;...** |
| 4 | WDesign Sans | **WDesign Sans VF** |
| 6 | WDesignSansSC-Regular | **WDesignSansSC-VF** |
| 16 | WDesign Sans | **WDesign Sans VF** |

共替换 15 条记录（多平台多语言）。

## 四、尚未处理的项（需要决策）

| 项 | 优先级 | 建议 |
|---|---|---|
| A4 子集同名 | 中 | 子集是 Web 用（@font-face 显式指定路径），同名不冲突；**可暂不改** |
| ~~A2 子集丢 vkrn~~ | — | P86 更正：非缺陷 |
| ~~A1 子集丢 GDEF~~ | — | P86 更正：非缺陷 |
| A6 VF fsSelection=0 | 低 | VF 用 wght 轴标识，fsSelection bit6 影响小；**可评估** |

## 五、这条路线的价值

teammate 审计发现了 **A1/A2/A3 三项我此前完全没查的东西**：
- 子集丢了 GDEF
- 子集 GPOS 还丢了 mark/vkrn（P28 只记录了 GSUB 的丢失）
- 子集 cmap 只剩 2 个子表，format 14 丢失

**这三项在我的 VERIFICATION-INDEX 里都没有覆盖。**

但队友的判断也需要复核：
- A5（家族不统一）实际是 P63 已论证的**正确设计**
- A7（无 VF.ttf）是**交付决策**，不是缺陷

**所以正确姿势是：队友扩大搜索面，我负责判定哪些是缺陷。**


---

## P86/P87 重要更正

本文 A1/A2/A3 三项结论经实测均已推翻。它们是**字符集闭包导致的正常行为**，不是子集缺陷。

| 项 | 本文原结论 | 实测真相 |
|---|---|---|
| A1 GDEF | 子集丢失 | 字符集无组合标记则 GDEF 无内容，自动裁掉（正确）|
| A2 mark/vkrn | GPOS 8→6 | GPOS 特性数恒定 5，从未丢失 |
| A3 cmap | 只剩 2 子表 | fmt12 需非BMP字符；fmt14 需变体选择符在字符集内 |

### 操作清单（取代「暂不改」）

| 需要什么 | 子集字符集必须包含 |
|---|---|
| 组合标记定位 | U+0300–036F |
| IVS 异体字 | U+FE00–FE0F 变体选择符本身 |
| 非 BMP 字符 | 对应码位 |

详见 P86-SUBSET-CORRECTION.md 与 P87-SUBSET-A3-CLOSED.md。
