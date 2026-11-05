# 表结构审计报告（TMP）

- 审计对象：`w-box:/data/build-cache/wdsans-dist/` + `/data/build-cache/wdsans-subset/`
- 执行：`/workspace/wdsans/venv/bin/python`（fontTools 4.67.0），`TTFont(lazy=True)` 只读表目录，未做任何 save()
- 文件总数：**27**（dist 15 = 7 档静态 × {ttf, woff2} + VF.woff2；subset 12 = 3 档 × {3755, 6763} × {ttf, woff2}）
- 结论：**必需表 27/27 全齐；无未知表、无重复表；checksum 全部通过。** 发现 1 类命名冲突、1 类 VF 与静态不一致、以及子集裁剪范围比文档描述的更大。

---

## 一、文件清单与表数

| # | 文件 | 容器 | 表数 | 大小(MB) | numGlyphs | cmap 码位 | 备注 |
|---|---|---|---|---|---|---|---|
| 1 | dist/WDesignSansSC-Thin.ttf | sfnt | 16 | 20.98 | 65535 | 44905 | 静态 |
| 2 | dist/WDesignSansSC-Thin.woff2 | woff2 | 16 | 7.50 | 65535 | 44905 | 静态 |
| 3 | dist/WDesignSansSC-Light.ttf | sfnt | 16 | 20.97 | 65535 | 44905 | 静态 |
| 4 | dist/WDesignSansSC-Light.woff2 | woff2 | 16 | 7.60 | 65535 | 44905 | 静态 |
| 5 | dist/WDesignSansSC-Normal.ttf | sfnt | 16 | 20.96 | 65535 | 44905 | 静态 |
| 6 | dist/WDesignSansSC-Normal.woff2 | woff2 | 16 | 7.63 | 65535 | 44905 | 静态 |
| 7 | dist/WDesignSansSC-Regular.ttf | sfnt | 16 | 20.95 | 65535 | 44905 | 静态 |
| 8 | dist/WDesignSansSC-Regular.woff2 | woff2 | 16 | 7.48 | 65535 | 44905 | 静态 |
| 9 | dist/WDesignSansSC-Medium.ttf | sfnt | 16 | 20.93 | 65535 | 44905 | 静态 |
| 10 | dist/WDesignSansSC-Medium.woff2 | woff2 | 16 | 7.79 | 65535 | 44905 | 静态 |
| 11 | dist/WDesignSansSC-Bold.ttf | sfnt | 16 | 20.92 | 65535 | 44905 | 静态 |
| 12 | dist/WDesignSansSC-Bold.woff2 | woff2 | 16 | 7.93 | 65535 | 44905 | 静态 |
| 13 | dist/WDesignSansSC-Heavy.ttf | sfnt | 16 | 20.91 | 65535 | 44905 | 静态 |
| 14 | dist/WDesignSansSC-Heavy.woff2 | woff2 | 16 | 7.80 | 65535 | 44905 | 静态 |
| 15 | **dist/WDesignSansSC-VF.woff2** | woff2 | **21** | 20.01 | 65535 | 44905 | **唯一 VF 交付物** |
| 16 | subset/...-Bold-sub3755.ttf | sfnt | 15 | 2.24 | 7992 | 4394 | 子集 |
| 17 | subset/...-Bold-sub3755.woff2 | woff2 | 15 | 0.99 | 7992 | 4394 | 子集 |
| 18 | subset/...-Bold-sub6763.ttf | sfnt | 15 | 4.12 | 13549 | 7402 | 子集 |
| 19 | subset/...-Bold-sub6763.woff2 | woff2 | 15 | 1.77 | 13549 | 7402 | 子集 |
| 20 | subset/...-Medium-sub3755.ttf | sfnt | 15 | 2.24 | 7992 | 4394 | 子集 |
| 21 | subset/...-Medium-sub3755.woff2 | woff2 | 15 | 0.98 | 7992 | 4394 | 子集 |
| 22 | subset/...-Medium-sub6763.ttf | sfnt | 15 | 4.13 | 13549 | 7402 | 子集 |
| 23 | subset/...-Medium-sub6763.woff2 | woff2 | 15 | 1.75 | 13549 | 7402 | 子集 |
| 24 | subset/...-Regular-sub3755.ttf | sfnt | 15 | 2.25 | 7992 | 4394 | 子集 |
| 25 | subset/...-Regular-sub3755.woff2 | woff2 | 15 | 0.95 | 7992 | 4394 | 子集 |
| 26 | subset/...-Regular-sub6763.ttf | sfnt | 15 | 4.13 | 13549 | 7402 | 子集 |
| 27 | subset/...-Regular-sub6763.woff2 | woff2 | 15 | 1.69 | 13549 | 7402 | 子集 |

> 同一字重的 ttf 与 woff2 **表集合完全相同**（逐 tags 对比 0 差异），说明 woff2 就是对应 ttf 的压缩形态，不是另一次构建。

---

## 二、关键表存在性对照

### 2.1 必需表（10 项）

| 表 | dist 静态(14) | dist VF(1) | subset(12) | 合计 |
|---|---|---|---|---|
| head / hhea / hmtx / maxp / cmap / glyf / loca / name / OS/2 / post | 全 ✓ | 全 ✓ | 全 ✓ | **27/27 ✓** |

**必需表无缺失。**

### 2.2 扩展 / 变体表矩阵

| 表 | dist 静态 ttf+woff2 | dist VF.woff2 | subset 全部 |
|---|---|---|---|
| BASE | ✓ | ✓ | ✓ |
| GDEF | ✓ | ✓（VarStore 有） | **✗ 被裁** |
| GPOS | ✓ | ✓ | ✓（特性变少） |
| GSUB | ✓ | ✓ | ✓（特性变少） |
| vhea / vmtx | ✓ | ✓ | ✓ |
| **fvar** | **✗（正确，不应有）** | ✓ | **✗（正确）** |
| gvar | ✗ | ✓ | ✗ |
| HVAR | ✗ | ✓ | ✗ |
| avar | ✗ | ✓ | ✗ |
| STAT | ✗ | ✓ | ✗ |
| MVAR / VVAR / cvar | ✗ | ✗ | ✗ |

### 2.3 VF 五表核验（WDesignSansSC-VF.woff2）

| 表 | 状态 | 内容 |
|---|---|---|
| fvar | ✓ | 轴 `wght` 250–400–900，7 个命名实例（250/300/350/400/500/700/900）名称齐全 |
| gvar | ✓ | 存在（65535 字形） |
| HVAR | ✓ | 存在（水平 advance 变化） |
| avar | ✓ | wght 6 段映射非恒等映射，正常 |
| STAT | ✓ | DesignAxis wght(nameID 265 "Weight")；7 个 Format 4 AxisValue；ElidedFallback=2 "Regular"；400 档带 ELIDABLE 位 |

缺失 MVAR / VVAR / cvar 属**可接受**：vhea/vmtx 全档恒定、字体无 cvt 表。

---

## 三、异常清单

### A1【中】子集丢失 GDEF（15 表 vs 全库 16 表）
`sub3755` / `sub6763` 全部 12 个文件都没有 GDEF；全库静态与 VF 都有（含 GlyphClassDef）。
原因：子集化时 GPOS 的 `mark` 系列 lookup 被整组裁掉，fontTools 顺手丢了 GDEF。
影响：当前无 mark 定位需求，**不致命**；但一旦要恢复 `mark`/`vkrn`，必须同时保留 GDEF，否则 GPOS mark lookup 会失效。

### A2【中】子集特性裁剪范围大于 `docs/P28-SUBSET.md` 记载
以 Regular 为例：

| | GSUB 特性 | GPOS 特性 |
|---|---|---|
| 全库 | 16（含 calt / hist / ruby / ljmo / tjmo） | 8（halt kern **mark** palt vert vhal **vkrn** vpal）→ 11 lookups |
| sub3755/6763 | 11（calt/hist/ruby/ljmo/tjmo 丢失） | 6（**mark、vkrn 也丢了**）→ 7 lookups |

P28 文档只写了「丢 6 个 GSUB 特性」，**没提 GPOS 的 mark 与 vkrn 也丢了**。vkrn 丢失意味着子集版**竖排西文不 kern**。Bold 同理（13 → 9 lookups）。

### A3【低】子集 cmap 子表从 6 个降到 2 个
全库：(0,3) fmt4 / (0,4) fmt12 / (0,5) fmt14(UVS) / (1,25) fmt6(Mac) / (3,1) fmt4 / (3,10) fmt12。
子集：只剩 (0,3) fmt4 + (3,1) fmt4。
连带后果：非 BMP 码位从 2590 → **0**；**format 14（变体选择器）消失 → IVS 序列（如 葛+VS）在子集版不再映射**；老 Mac 编码不再可用。若线上有 IVS 需求需单独确认。

### A4【中】命名冲突：VF / 子集 / 静态 三套文件共用同一 family + PostScript 名
- VF.woff2 的 name 表与**静态 Regular 完全一致**：family `WDesign Sans`、style `Regular`、**PostScript 名 `WDesignSansSC-Regular`**（无 -VF 后缀，无 axis 说明）。
- 子集的 name 表也与全库**逐字相同**（`sub3755`/`sub6763` 无任何子集标识，nameID1/2/4/6 一致）。
- 后果：本地同时安装会互相覆盖（Windows 按 PS 名去重）；同字重的 3755 与 6763 两档也同名。

### A5【中】静态档命名策略混用 RIBBI 与"单成员家族"
| 文件 | nameID1 (family) | nameID2 (style) | Windows 归类 |
|---|---|---|---|
| Regular / Bold | `WDesign Sans` | Regular / Bold | 同一家族（正常 RIBBI） |
| Thin | `WDesign Sans Thin` | Thin | 独立家族 |
| Light | `WDesign Sans Light` | Light | 独立家族 |
| Normal | `WDesign Sans Normal` | Normal | 独立家族（**"Normal" 非标准样式名**） |
| Medium | `WDesign Sans Medium` | Medium | 独立家族 |
| Heavy | `WDesign Sans Heavy` | Heavy | 独立家族 |

→ 系统里会出现 6 个"家族"，其中 5 个只有 1 个成员；`Normal` 作为 style 名不合 Windows/Adobe 惯例（应为 Regular/Book）。CSS 侧用 @font-face 不受影响，但桌面交付（设计软件字体列表）体验会碎。

### A6【低】VF 的 OS/2 fsSelection 与静态不一致
- VF：`fsSelection = 0`（**无 bit6 REGULAR**，也无 bit7 USE_TYPO_METRICS）
- 静态 Regular：`fsSelection = 64`（bit6 REGULAR）
- 全部 27 个文件都**未设 bit7 USE_TYPO_METRICS**：于是行高按 hhea `1000/-200`（1.2em），而非 typo `880/-120`（1.0em）。
→ VF 与静态在"是否 Regular"判定上不一致；行高行为在两处渲染器上可能不同。若"1.0em 行高"是设计意图，应补 bit7。

### A7【信息】交付物缺 VF 的 TTF
dist 里 VF 只有 `.woff2`（20.01 MB），没有对应 `.ttf`。桌面端若需要可变 TTF 得另找（`/data/build-cache/subset-study/vf/WDesignSansSC-VF.ttf`，50 MB，不在本次交付目录）。
另：VF 的 woff2 高达 20 MB，比静态 7.5 MB 还大（glyf+gvar 双份轮廓），网页首屏基本不可用 —— 属体积策略问题，非表结构问题。

### A8【信息，非异常】head.flags 差异
ttf 全部 `flags=1`，woff2 全部 `flags=2049`（= 1 + bit11）。bit11 是 WOFF/WOFF2 规范要求的「数据无损压缩」标记，**正常**。

### A9 无异常项（明确确认）
- **未知表：0 例**（27 个文件，同时用原始 sfnt 目录逐条 tag 解析 + fontTools `reader.tables` 双重确认）
- **重复表：0 例**（原始 16/15/21 条目数与去重后数量相等）
- **大小写/空格 tag 问题：0 例**
- **checksum：13 个 TTF 全部通过**（`checkChecksums=2` 全表读取无错）
- **loca 一致性**：13 个 TTF 全部 `len(loca) == numGlyphs + 1`，且 `loca[-1] == glyf 表长度`（无截断/无多余空洞）
- **hmtx/vmtx**：`hmtx 条数 == numGlyphs`，`vmtx 条数 == numGlyphs`，`hhea.numberOfHMetrics=65532(全库)/7976,13526(子集)`、`vhea.numberOfVMetrics=65158(全库)` 均在合法区间
- **垂直度量全档统一**：hhea 1000/-200/0，typo 880/-120/0，win 1160/288，vhea 500/-500
- **子集字形与全库一致**：抽样 advance 完全相同（国 1000、骨 1000、（1000、A 636、V 632、H 696、space 224、a 496、m 811…），HarfBuzz 整形对比 kern（AV=621/632）、连字（fi=600）、竖排偏移（-500,-868）在 full / sub6763 / sub3755 三者一致；仅 gid 重编号

---

## 四、建议优先级

1. **P0（发布前定）**：A4 命名冲突 —— 给 VF 和子集补区分性 name（VF 至少改 PS 名 + 加 `WDesign Sans VF` 家族名），否则桌面端安装即覆盖。
2. **P1**：A5 静态家族命名统一（要么全 RIBBI 进 `WDesign Sans`，要么全走 `WDesign Sans X` 且把 `Normal` 改作 `Regular/Book`）。
3. **P1**：A2 若线上依赖竖排西文 kern，需重跑子集并显式保留 `vkrn` + `GDEF`（A1）。
4. **P2**：A6 全档补 `USE_TYPO_METRICS`（若设计意图是 1.0em 行高），并让 VF 的 fsSelection 与静态对齐。
5. **P2**：A3 若需 IVS，子集版要单列保留 cmap format 14。
6. **P3**：A7 VF woff2 20 MB 的网页可用性问题。

---

## 五、复现

```bash
# 表清单（秒级，不 save）
/workspace/wdsans/venv/bin/python - <<'EOF'
import os
from fontTools.ttLib import TTFont
for d in ['/data/build-cache/wdsans-dist','/data/build-cache/wdsans-subset']:
    for fn in sorted(os.listdir(d)):
        if fn.endswith(('.ttf','.woff2')):
            f=TTFont(os.path.join(d,fn), lazy=True)
            print(fn, len(f.reader.tables), sorted(f.reader.tables))
            f.close()
EOF
```

> 注：WOFF2 用 `TTFont(..., lazy=True)` 时，`loca.locations` / `glyf` 访问会触发 brotli 全量解压（20 MB 文件约 1–2 min/个），**只读表名用 `f.reader.tables` 或 `f.keys()` 即可秒回**。本报告的 loca/glyf 深度校验只对 TTF 做了全量。
