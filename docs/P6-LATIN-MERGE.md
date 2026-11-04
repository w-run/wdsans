# P6：Mona Sans 拉丁合并

> 2026-11-05 · 三次失败后打通。三次失败里有两次性质一样：**以为保住了 VF，实际把拉丁做成了单字重或错位轮廓**。
> 本文所有数字都来自 fontTools 复算，可照 §8 的命令重跑。

---

## 1. 结论速览

| 项 | 结果 |
|---|---|
| 拉丁来源 | **Mona Sans VF** —— 上游名 `MonaSansVF[wdth,opsz,wght].ttf`，仓库内 `ref/mona/MonaSansVF.ttf`（**真 TrueType** `glyf`+`gvar`） |
| 合并字形数 | **117**（跳过 2 个：`space` / `uni00A0`，无轮廓属正常） |
| 字重行为 | 250 / 400 / 900 三档轮廓**不同**，墨宽与 advance 都随 `wght` 单调递增 |
| gvar 结构 | 1 轴，每字形 **2 个 tuple**（peak +1→900 / −1→250），coords 长度 = 点数 + **4**（phantom） |
| 中文影响 | **零**：CJK 字形 glyf 与 gvar 逐点相同；cmap 44,810 不变；glyph 65,535 不变；GSUB 483 features / 52 lookups、GPOS 296 / 13 与合并前完全一致 |
| 本阶段产物 | `/data/build-cache/wdsans-p1/wdsans-p7-latin-final.ttf`（≡ `wdsans-p6d.ttf`，md5 `16eb0736…`）<br>**后续 P7 已在此基础上内联复合字形，最终产物见 `wdsans-p8c.ttf`** |
| 已知限制 | ~~Mona 的 512 个复合字形未搬~~ → **已由 P7 解决**（复合字形数已归零）；HVAR advance delta 仍是 Noto 旧数据，待接入 `wds/hvar_fix.py` |

---

## 2. 源字体与许可

### 2.1 源文件

| 项 | 值 |
|---|---|
| 路径 | `ref/mona/MonaSansVF.ttf` |
| 轮廓格式 | **TrueType `glyf`**（原生，非 CFF）—— 选它而不是 CFF 版的唯一理由 |
| 可变结构 | `gvar`，**3 轴**：`wdth` 75–125（默认 100）、`wght` 200–900（默认 200）、`opsz` 0–100（默认 0） |
| 字形总数 | 797，其中**复合字形 512** |
| UPM | 1000（与中文基座一致，无需换算单位） |

取实例时恒用 `{wdth: 100, opsz: 0}` 把另两轴钉在默认值 —— 只搬 `wght` 一根轴。

> 附带实测：`opsz` 会让 H 墨宽从 582.8（opsz=0）涨到 616.7（opsz=100），
> 所以 **opsz 必须钉死**，否则同一字形在不同光学尺寸下宽度不一致。

### 2.2 许可（硬约束）

`ref/mona/LICENSE.txt` 原文首行：

```
Copyright (c) 2023, GitHub https://github.com/github/mona-sans
with Reserved Font Name "Mona Sans"

This Font Software is licensed under the SIL Open Font License, Version 1.1.
```

| 条款 | 对本项目的约束 |
|---|---|
| 许可 | **SIL OFL 1.1**，与思源一致；衍生字体不能换证 |
| 保留字体名（RFN） | **`Mona Sans` 不可沿用** → 已按 P5 改为 `WDesign Sans` |
| 署名 | OFL 要求保留上游版权声明（`Copyright (c) 2023, GitHub`）。**当前 name 表里没有这条，见 §7 限制 3** |
| 禁用词 | DESIGN §1 禁用词已含 `Mona`；实测最终字体 name 表**残留 Mona 字样 0 处** |

---

## 3. 度量实测与对齐系数

### 3.1 两端实测

| 指标 | Mona Sans @400 | Noto 中文基座 @400 | 差 |
|---|---|---|---|
| UPM | 1000 | 1000 | — |
| **x-height** | **526** | **543**（`OS/2.sxHeight` 声明值）/ **535**（x 字形 bbox 实测） | Mona 矮 3–3.1% |
| **H 墨宽** | **582** | **520** | **+62（+12.1%）** |
| H advance | 764 | 728 | +4.9% |
| cap height（H 字面高） | 729 | 721 | +8 |

> ⚠️ **口径说明（两种说法都对，量的是不同档位）**：
> - 任务书写「H 宽 582 vs 520，**宽 14%**」→ 那是 **wght=250 档**：554.5 / 487 = **1.139（+13.9%）**；
> - **wght=400 档**是 582.8 / 520 = **1.121（+12.1%）**。
> 缩放作用在轮廓上，所以取 400 档（默认实例）做对齐基准，得 `sx=0.895`。
>
> ⚠️ x-height 同样有两个值：`OS/2.sxHeight` 声明 543，但 x 字形 bbox 实测只有 535。
> **543 是声明值，不是墨高**——后续 §7 会处理这个不一致。

### 3.2 对齐系数

目标不是「H 等宽」，而是「视觉上拉丁与中文同高、同灰度」。Mona 天生比 Noto 的拉丁宽 +12%，必须压。

```
sx = 0.895      # 水平压缩：520 / 582 = 0.894，再按 x/n/o 中位数复核
sy = 1.0046     # 垂直：DESIGN §5「x-height = Mona × 1.0055」，取 1.005 量级
```

实测校验（`sx` 只压轮廓，advance 同步 ×`sx`）：

| 字形 | Mona@400 | ×sx/×sy 后（本产物） | 校验 |
|---|---|---|---|
| H | 583 × 729 | **521 × 732** | 583×0.895 = 521.5 → 521 ✓；729×1.0046 = 732.4 → 732 ✓ |
| x | 516 × 526 | **462 × 529** | 516×0.895 = 462 ✓；526×1.0046 = 528.4 → 529 ✓（**DESIGN §5 目标 529，命中**） |
| n | 435 × 535 | 390 × 537 | ✓ |
| o | 488 × 544 | 436 × 546 | ✓ |
| H advance | 764 | 684 | 764×0.895 = 684 ✓ |

**结果**：cap 732（DESIGN 目标 733，差 1 单位）、x-height 529（目标 529，命中）。

---

## 4. 三次失败（诚实记录）

### v1：清空 gvar —— 拉丁变成单字重

**做法**：把 Mona 默认实例的轮廓搬进 `glyf`，然后把这些字形的 `gvar` 条目**整条 `del` 掉**，
理由是「Mona 的三轴 tuple 跟我们单轴不兼容」。

**当时以为**：删掉私有 tuple，字重由中文的 gvar 兜住。

**实测**：

| 项 | wght 250 | 400 | 700 | 900 |
|---|---|---|---|---|
| H 高（cap） | 732 | **732** | 732 | 732 |
| H 墨宽 | 487 | **487** | 487 | 487 |
| H 竖干宽 | 34 | **34** | 34 | 34 |

四个字重**逐点完全相同**，`gvar.variations['H']` 是空列表。

**根因**：删条目 ≠ 沿用别的条目。这些字形在新字体里**没有任何 delta**，实例化时被当「无变化」。
**这是本轮最贵的一课：VF 的价值全在 delta，轮廓只是 400 那一个切片。**

产物：`wdsans-p6-latin.ttf`。

### v3：只换 base、保留 Noto 原 gvar —— 83 个字形的 delta 套错了点

**做法**：不删 `gvar`，只替换 `glyf` base，指望「Noto 的 delta 能套在 Mona 的轮廓上」，
并加一道守卫：点数不一致的字形直接跳过。

**实测点数比对**（Mona@400 vs 合并前 Noto）：

```
same-points: 34   mismatch: 83
dollar   53↔52   percent 60↔52   ampersand 66↔75
asterisk 15↔30   comma   21↔26   one      13↔10
two      30↔39   four    17↔11
```

**83 个直接跳过**——也就是本次只换成了 34 个。

而那 34 个「点数恰好相同」的更糟：点数对得上，**点位语义完全对不上**。
Noto 的 delta 被套到 Mona 的锚点上，得到一个既不 Mona 也不 Noto 的畸变轮廓：

| 字形 | 250 | 400 | 900 |
|---|---|---|---|
| H 高 | 747 | 732 | **767** |
| H 墨宽 | 530 | 487 | 562 |
| n 高 | 531 | 543 | 569 |

cap height 本该跨字重恒定（Mona 自己 729/729/729），这里变成 747→732→767 乱跳。
**点数守恒 ≠ 语义守恒**——增量模型的前提是「同一 index 指同一锚点」，跨字体永远不成立。

产物：`wdsans-p6b.ttf`。

### v4：从 Mona 在 250/400/900 采样重建 gvar —— 思路对了，实现有两个 bug

这一版才找到唯一正确的路：**不指望任何现成 delta，让 Mona 自己减自己。**

1. 在 Mona 上实例化 **250 / 400 / 900** 三档，各取一次轮廓；
2. `glyf` base 用 **400** 那一份；
3. `d(900) = P900 − P400`、`d(250) = P250 − P400`，尾部补 4 个 phantom 点；
4. 写成我方单轴的两个 tuple。

**为什么这次必然成立**：三个采样点来自**同一 Mona 字形、同一次轴解析**，
点数/顺序/on-off 天然一致 —— 不是「两个字体猜对齐」，而是「一个字体自己减自己」。

**主路打通了（字重 ramp 出现）**，但复算抓到两个实现 bug，都是脚本写法问题、不影响路线：

| # | bug | 实测症状 |
|---|---|---|
| 1 | 采样时**没套 sx/sy**（`inst_at()` 收了参数却没用），hmtx 还取了 Mona 的**默认实例 200** 而非 400 | 轮廓**根本没被压缩**：合并后 H 墨宽仍 **583**，与设计目标 520 差 12% |
| 2 | 4 个 phantom 点的 delta 全写 **0** | **advance 冻结**：H advance 在 250 和 900 都是 **675** |

第 2 条是 TrueType 的关键机制：**advance 的变体走 gvar 的 phantom 点**，不走 hmtx。

```
pp1.x = xMin - lsb
pp2.x = pp1.x + advanceWidth

所以  delta(pp1.x) = (xMin_w - lsb_w) - (xMin_b - lsb_b)
      delta(pp2.x) = delta(pp1.x) + (adv_w - adv_b)
```

**v5 修正**：采样时套上 `sx/sy`、hmtx 取 400 档、按上面两式写 phantom delta。
其余（采样重建的骨架、2 tuple 结构、点数+4）完全沿用 v4 —— **v4 是路线上的成功，v5 只是把参数接对**。

| 字形 | 250 | 400 | 900 | 单调？ |
|---|---|---|---|---|
| H 墨宽 | 497 | 521 | 589 | ✅ |
| H advance | 678 | 684 | 700 | ✅ |
| n 墨宽 | 362 | 390 | 461 | ✅ |
| o 墨宽 | 419 | 436 | 485 | ✅ |

cap 全程 732（恒定，符合 Mona 的设计），不再出现 v3 的乱跳。

产物：`wdsans-p6c.ttf`（v4，未压缩、advance 冻结）→ `wdsans-p6d.ttf` / `wdsans-p7-latin-final.ttf`（**v5，当前最终产物**）。

---

## 5. gvar 结构（本产物的拉丁字形）

我方字体只有 **1 根轴**：`wght` 250–900，默认 400。每个被合并的拉丁字形写 **2 个 tuple**：

```python
TupleVariation({"wght": (0.0, 1.0, 1.0)},  d900)   # peak = +1 → 900
TupleVariation({"wght": (-1.0, -1.0, 0.0)}, d250)   # peak = -1 → 250
```

| 项 | 值 / 说明 |
|---|---|
| 轴数 | **1**（`wdth` / `opsz` 全钉默认值，不搬） |
| tuple 数 | **2**：一个向粗（peak +1）、一个向细（peak −1），都以 400 为起点 |
| **coords 长度** | **字形点数 + 4**（末尾 4 个 phantom 点：左/右/上/下） |
| phantom 点 | `(pp1.x, 0)` / `(pp2.x, 0)` / `(0,0)` / `(0,0)`，承载 advance 变体 |
| 实测抽样 | H：12 点 → 2 tuple × **16** 坐标；n：22 → **26**；a：37 → **41** |
| H 的 phantom delta | 900：`[pp1 +0, pp2 +16]`；250：`[pp1 +0, pp2 −6]` → advance 684±… ✓ |

`fontTools` 的算术校验（`P = base + Σ delta·f(wght)`）与真实实例化逐点一致，说明 (min, peak, max) 写法正确。

---

## 6. 结果

### 6.1 替换范围

| 项 | 数 |
|---|---|
| Mona 落在 `≤U+024F` + 标点区（2000–206F / 20A0–20CF）且**非复合**的字形 | 119 |
| 其中我方 cmap 也有的 | 119 |
| **实际替换** | **117** |
| 跳过 | **2**：`space`(U+0020)、`uni00A0`(U+00A0) |

**跳过 space/nbsp 属正常**：它们是「无轮廓的空白字形」，只有 advance，
`numberOfContours == 0`，取不到坐标。脚本以「无轮廓」为由跳过，其 advance 保留原值。

### 6.2 中文零影响（逐项核对，合并前后对比）

| 检查 | 结果 |
|---|---|
| `uni56FD`（国）、`uni660E`（明）等 CJK 抽样 | glyf **逐点相同**，gvar **逐 tuple 相同** |
| cmap 码位数 | 44,810 → 44,810（**不增不减**） |
| numGlyphs | 65,535 → 65,535 |
| GSUB | 483 features / 52 lookups，**与合并前完全一致**（含 `locl`） |
| GPOS | 296 features / 13 lookups，同上 |
| name 1 / 6 | `WDesign Sans` / `WDesignSansSC-Regular`（P5 命名未被破坏） |
| 复合字形总数 | **0**（与合并前一致，没有引入悬空组件引用） |

### 6.3 逐字形校验

拿最终产物 117 个拉丁字形的 base 坐标，与「Mona@400 × (0.895, 1.0046)」逐点比对：

```
p6d/d7 coords == Mona@400 × (sx, sy): 116 match   1 mismatch
唯一不符：periodcentered（12 点中有取整差 > 1 单位者）
```

偏差来自「先缩放后逐点取整」的顺序，量级 ≤ 2 单位，不影响视觉。

---

## 7. 已知限制（下一轮必须处理）

1. ~~**带重音的拉丁仍是 Noto 原样**~~ → **已由 P7 解决**（`docs/P7-COMPOSITE-INLINE.md`）。
   Mona 拉丁区共 225 个复合字形（其中 136 个在我们 cmap 内），P7 用 **v8 内联**（`DecomposingRecordingPen`
   把组件展开成单一简单轮廓，不新增字形槽位）全部搬完，**136/136 成功**。
   重音字母与基础字母宽度差已归零。最终字体中**复合字形数 = 0**。
   > 关键卡点：本字体 `numGlyphs` 已满 65,535（TrueType 上限），
   > 任何「新增组件字形」的方案都不可行（v7 崩在 `struct.error: 'H' format requires <= 65535`）。
2. **advance 的验证方式是错的（不是数值范围问题）** —— v5 已按 `pp1/pp2` 公式把 phantom delta 写对，
   但**当时用 `instancer` 读 `hmtx` 来验证，这个方法本身无效**（详见 §7.7）：
   `instancer` 会丢掉 HVAR，而 HarfBuzz 优先用 HVAR。真值须用 `hb-shape`。
   另有一个**尚未修复**的缺陷：**HVAR 的 advance delta 仍是 Noto 旧数据**，
   叠加在 Mona 的 base 上，使极端字重最多偏 **+45 单位**（T 字形）。修复函数 `wds/hvar_fix.py` 已写好但未接入构建。
3. **OFL 署名待补** —— name ID 0 在 P5 已删（原 `Reserved Font Name 'Source'`），
   现在表里**没有 GitHub 的 Mona Sans 版权声明**。OFL 1.1 要求保留上游署名，建议写入：
   `Copyright (c) 2023, GitHub (Mona Sans, OFL 1.1); Copyright (c) 2014-2021 Adobe (Source Han Sans, OFL 1.1); modified by WDesign`。
4. **OS/2 度量未跟拉丁同步** —— `OS/2.sxHeight` 仍是 **543**、`sCapHeight` 仍是 **733**，
   而实测拉丁 x-height 已变 529、cap 732。部分排版引擎会拿这两个值算小字号对齐，需按实测更新。
5. **交付产物未重出** —— `/data/build-cache/wdsans-dist/` 里的七档 TTF/WOFF2
   （拉丁 H 墨宽 520 = Noto 原样）**还是合并前的**，需从 `p7-latin-final` 重跑 `wds/deliver.py`。
6. **无视觉验收图** —— 本轮只有量化验证，**没有出 PNG 并排图**（AGENTS.md 铁律 6 未满足）。
   下一轮第一件事：中英混排样张，250/400/900 三档并排 + 12px 正文，实看字重过渡。

### 7.7 踩坑：用 `instancer` 测 advance 是错的（P7 补记）

> 这条在 P6 当时没发现，是 P7 阶段由 verify-latin 队友用 HarfBuzz 交叉验证才暴露的。
> 写在 P6 是因为**源头在 P6 的 advance 实现**（§5 phantom 点那段）。

P6 §5 里我用 `fontTools` 的 `instancer` 实例化后读 `hmtx` 来验证 advance。
**这个测法是错的**，原因有两条：

1. `instancer` 实例化时**把 HVAR 表整个丢掉**（实测：实例化后表清单里没有 HVAR）；
2. 真实排版引擎（HarfBuzz）**优先用 HVAR** 算 advance，gvar phantom 只是兜底。

所以 `instancer` 给出的是「只有 phantom 那一份 delta」的 advance，与用户实际看到的宽度不一致：

| 字形 H | wght 250 | 400 | 700 | 900 |
|---|---|---|---|---|
| `instancer` → `hmtx`（错） | 678 | 684 | 694 | 700 |
| **hb-shape（真值）** | **663** | **684** | **713** | **730** |

400 档两者相同（幻影 delta 为 0），**越往极端字重差得越多**：250 差 −15、900 差 +30。

**规则**（写进项目操作习惯）：

| 测什么 | 用什么 |
|---|---|
| 轮廓几何（点数 / 坐标 / bbox） | `fontTools` `instancer` ✅ |
| **advance / 排版宽度** | **`hb-shape --variations="wght=..." --no-glyph-names --output-format=json`** ✅ |
| 单字宽度（避免 kerning 干扰） | 单字 shape，不要整串 |

> 这个坑的危险之处在于**它会静默给出一个自洽的错值**：单看 `instancer` 的 678/684/694/700，
> 曲线是单调的、看着完全正常。只有拿第二个独立工具交叉验证才发现。
> 详见 `docs/P7-COMPOSITE-INLINE.md` §4。

---

## 8. 复算命令

```bash
cd /workspace/wdsans && ./venv/bin/python - <<'PY'
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.boundsPen import BoundsPen

def bb(f, n):
    gs = f.getGlyphSet(); b = BoundsPen(gs); gs[n].draw(b); return b.bounds

M = 'ref/mona/MonaSansVF.ttf'
N = '/data/build-cache/wdsans-p1/wdsans-p4-stat.ttf'      # 合并前
P = '/data/build-cache/wdsans-p1/wdsans-p7-latin-final.ttf'

# 1) 度量与对齐系数（§3）
m = instancer.instantiateVariableFont(TTFont(M), {'wght': 400, 'wdth': 100, 'opsz': 0},
      inplace=True, updateFontNames=False, optimize=False)
n = instancer.instantiateVariableFont(TTFont(N), {'wght': 400},
      inplace=True, updateFontNames=False, optimize=False)
mh, nh, mx, nx = bb(m, 'H'), bb(n, 'H'), bb(m, 'x'), bb(n, 'x')
print('H 墨宽  Mona %.1f / Noto %.1f = %.3f' % (mh[2]-mh[0], nh[2]-nh[0], (mh[2]-mh[0])/(nh[2]-nh[0])))
print('x-height Mona %.1f / Noto %.1f' % (mx[3]-mx[1], nx[3]-nx[1]))
print('OS/2 sxHeight 声明', TTFont(N)['OS/2'].sxHeight)

# 2) gvar 结构（§5）—— 长度必须 = 点数 + 4
f = TTFont(P, lazy=True); glyf = f['glyf']
for g in ('H', 'n', 'a'):
    pts = len(glyf[g].getCoordinates(glyf)[0])
    print(g, 'pts', pts, [(dict(t.axes), len(t.coordinates)) for t in f['gvar'].variations[g]])

# 3) 字重 ramp（§6）—— 三档必须不同
for w in (250, 400, 900):
    i = instancer.instantiateVariableFont(TTFont(P), {'wght': w},
          inplace=True, updateFontNames=False, optimize=False)
    H = bb(i, 'H')
    print('wght', w, 'H 墨宽 %.0f  advance %d' % (H[2]-H[0], i['hmtx']['H'][0]))
PY
```

---

## 9. 下一轮

> 状态（P7 之后回看）：
> - ✅ 复合字形 → **P7 已完成**（v8 内联 136/136，复合字形数归零）
> - ⚠️ advance 验证方式 → **原列的「117 字形 advance 全量断言」方向错了**，
>   因为当时用 `instancer` 读数（§7.7）；正确做法是 `hb-shape`，且这条已升级为项目规则
> - ❌ **HVAR 未修** —— 当前优先级最高的遗留项

- [ ] **接上 `wds/hvar_fix.py`**（HVAR advance delta 仍是 Noto 旧值，极端字重偏 +45）
- [ ] 出中英混排样张（250/400/900 并排 + 12px 正文），**实看**字重过渡与小字号
- [ ] `OS/2.sxHeight` → 529、`sCapHeight` → 732
- [ ] name ID 0 补 GitHub / Adobe 双版权（OFL 合规）
- [ ] 从 `wdsans-p8c.ttf` 重跑七档静态 + WOFF2，regen `wdsans-dist`
- [ ] G3/G4 闸门脚本纳入拉丁段（当前只覆盖 CJK 段），并把 hb-shape 定为 advance 唯一口径

---

## 10. 方法论收获

**「VF 保住了吗」不能靠推理，只能靠三档实例化复算。**

v1 和 v3 两次失败，如果只看单张 400 的渲染图，**都完全正常**——
v1 的 H 在 400 档就是标准 Mona H，v3 的 H 在 400 档也是标准 Mona H。
只有把 250/400/900 摆一起量，才看到「四档同粗细」和「cap 747→767」。

v4 更典型：**路线正确但参数没接上**，字重 ramp 已经出现，
可轮廓根本没压缩（墨宽 583）、advance 根本没变（675）。这两条单看一档都看不出来。

这与 P3/P4 的教训同源：
- P3 证明**低分辨率目视会看出不存在的特征**（648 个角点全 90°）；
- P4 证明**量化能救回被推理骗过的判断**（7 条全被推翻）。

两者必须同时做。本轮只做了量化、没做目视，已列入 §7 限制 6，**不当作已完成**。
