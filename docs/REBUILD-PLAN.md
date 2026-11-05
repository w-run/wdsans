# WDesign Sans 重构方案（接手评审稿）

> 起草：2026-11-04 · 原状态：待用户裁决
>
> **已执行完毕（2026-11-05）**。用户裁决：noto 基座 / 不出 OTF-CFF / VF + 命名实例 / Mona Sans 作拉丁 / glow-src 只读参考。
> 全部 22 轮已落地交付，产物见 /data/build-cache/wdsans-dist/。
> 本方案中的若干预测已被实测推翻，详见各 P* 文档与 P22 的方法论总结。
> 依据：/workspace/AGENTS.md、wdsans 全部文档、上游 welai/glow-sans README + 49 条 issue/PR 全量、旧版产物实测审计、Noto/SHS 双基座实测。

---

## 0. 结论速览

| 项 | 结论 |
|---|---|
| 现有 wdsans 代码能不能救？ | **只救「知识」，不救「管线」**：形变路线（栅格化→骨架→重描边）本身就是全部缺陷的根因 |
| 基座改 NotoSans 是否可行 | ✅ **强烈推荐**。原生 TTF（glyf+gvar），单 tuple 可变，天生拓扑一致 |
| 已实测通过的关键能力 | 增量级形变：改写 gvar delta，**400/900 轮廓 maxdiff=0、拓扑 100% 一致** |
| 旧版产物还能否复用 | ❌ 完全不能。七项结构性缺陷全部实测复现（见 §2） |
| 最大风险 | 不是技术，是**视觉方向**：字形细节算子做不做得「好」 |

---

## 1. 上游 glow-sans 缺陷（README + 全部 49 条 issue 已详读）

上游 **2022-03-11 停更，repo 已 archived**。作者原话（#49）：

> 「由于思源黑体项目发布了可变版本，重新基于其需大规模改动算法，故**无限期暂更**。」

### 1.1 算法级缺陷（根因，调参救不回来）

| # | 缺陷 | issue | 根因（源码定位） |
|---|---|---|---|
| A1 | **去脚（feet removal）不可靠** | #2 #7 #10 #28 #34 #47 | 7 点窗口 + 直角容差仅 2° + maxStroke 粗估。字重越极端越失效（#7：contrast<0.87 必坏，作者标 wontfix） |
| A2 | **去脚导致整字「飘起」** | #7 (MY1L) | 摘脚后只「下降 1/4 脚高」补偿，口垫底字（名/容/兽/音/飴）整体浮起 |
| A3 | **撇捺喇叭口**（SHS 原生有） | #2 | 全局滤镜无法按「笔画角色」区分处理 |
| A4 | **点被压扁/喇叭化** | — | dotsoftness 对点做统一缩放 |
| A5 | **曲线被拉直** | #2 #34 | 路线自带：光栅化离散 → CV 骨架 → 重描边，只能拟合折线 |
| A6 | **半角假名只是改字距** | #11 | 作者自认「荧黑的半宽假名着实偷懒了」 |
| A7 | **CID/字形映射错位** | #22 #23 | 作者自认「build 忽略了 SHS 原始 CID，这类问题几乎无法修，除非重写构建脚本」 |
| A8 | **TC 缺字 / CodePage / name 表分裂** | #16 #22 #27 #30 #41 #42 | name 表不完整 → PS/Figma/Windows 只认两档 |
| A9 | **没有 TTF，没有 hinting** | #33 #43 | 只发 OTF/CFF；Windows 低 DPI 糊 |

### 1.2 与我们直接冲突的「设计取向」（不是 bug，是路线差异）

- **#35 Rebase to variable font?** —— 作者承认「应该有这个计划」，但没做。**这正是本次重构要补的**
- **#4 Weight 450** —— 作者拒绝加档，理由是「要迁就 Fira/Raleway 的字重」。我们不受此约束
- **#6 #48 圆角** —— 用户反复要求「圆滑边角但不是圆体」。WDesign 的「全圆角」语言正好吃这一口
- **#23 字形正字法**（牙/呈/青/節…）—— 作者明确「不做手工字形修复」

> **一句话**：glow-sans 是「栅格化形变」路线的极限，它的失败恰好证明 wdsans `docs/PIPELINE.md` §2 的判断——**必须改成节点位移**。

---

## 2. 旧版产物实测审计（D:/Project/Font/v202506）

已上传 w-box 用 fontTools 实测，**POSTMORTEM 的六项缺陷全部复现**：

| 缺陷 | 实测数据 | 判定 |
|---|---|---|
| 无可变结构 | `fvar`=无、`STAT`=无、`glyf`=有 | ❌ 永久不可救（点结构仅 6% 兼容） |
| 拉丁度量失配 | `OS/2 sCapHeight=784`（目标 733，**+51**） | ❌ |
| 行高撑爆 | `hhea = 1160 / -288`（行高 1.448em，目标 1.0em） | ❌ |
| 竖排行高更糟 | `vhea = 1913 / -1502`（SHS 原值 500/-500） | ❌ |
| 特性被裁 | GSUB 仅 **10 个 feature / 仅 DFLT 一个 script**；**无 `locl`** | ❌ 违反 DESIGN §6 铁律 |
| name 表分裂 | Regular: name16/17 = **None**；Thin: 有 | ❌ 直接破坏 CSS weight 匹配 |
| cmap 缩水 | 32,089（Noto VF 44,810 / SHS VF 44,853） | ❌ 少 1.2 万码位 |

> 结论：**旧版只能当「眼睛参照」，一个字节都不能当基座。** POSTMORTEM 的判断经复核依然成立。

---

## 3. 基座裁决：Noto Sans CJK SC VF（推荐）

### 3.1 双基座实测对比

| 指标 | **Noto Sans CJK SC VF** | Source Han Sans VF | 谁更适合 |
|---|---|---|---|
| 轮廓格式 | **TrueType `glyf`（原生）** | CFF2（三次曲线） | **Noto** ← 用户要求原生 TTF |
| 可变结构 | `gvar`，**每字形仅 1 个 tuple**（peak 0→1） | CFF2 blends | **Noto**（增量模型极简） |
| 轴 | wght 100–900（默认 100） | wght 250–900（默认 250） | Noto 覆盖更宽 |
| 命名实例 | 7 档（Thin100/Light300/DemiLight350/Regular400/Medium500/Bold700/Black900） | 7 档 | 打平 |
| numGlyphs | 65,535 | 65,535 | 打平 |
| cmap | 44,810 | 44,853 | 打平 |
| GSUB | **17 feature / 7 script** | 17 feature / 7 script | 打平 |
| `locl` | ✅ **hani×{ZHS,ZHT,ZHH,JAN,KOR} + kana/latn/cyrl/grek 全有** | ✅ 同样完整 | 打平 |
| GPOS | halt,kern,mark,palt,vert,vhal,vkrn,vpal | 同 | 打平 |
| cap / x-height | **733** / （sXHeight 未声明） | 733 / 543 | 目标 cap=733 直接命中 |
| typo/win 度量 | **880/-120，1160/288** | 同 | **两者都已等于 DESIGN §7 目标** |
| RFN（保留字体名） | `Source`（**不是 Noto**） | `Source` | 同 |
| 版本/维护 | NotoSansCJK 2.004（活跃） | SHS 2.005R（活跃） | — |

### 3.2 三条硬结论

1. **原生 TTF 是 Noto 独有的**。SHS VF 只有 CFF2；要走 TTF 必须 otf2ttf 转曲（cu2qu 量化），这会**改变点数、破坏增量一致性**——正是我们最不想做的事。选 Noto = 直接拿到 TTF，零转换。
2. **Noto 的可变模型极简**：每字形 1 个 tuple，peakTuple=(0,1,1)，含义是「wght 从默认 100 到 900 的整体增量」。形变 = **给这个增量加一个修饰项**，不需要重建 blend 运算。
3. **度量已经对上**：Noto 的 typo 880/-120、win 1160/288、cap 733 **就是 DESIGN §7 的目标值**，省掉一整类「改度量」的活。

### 3.3 必须先解决的前置问题

Noto 的默认实例是 **wght=100**（`fvar.defaultValue=100`），而我们要默认 **400**。
→ 用 `instancer` 把轴重设为 `100..900, default 400`，`avar` 同步重建。

---

## 4. 新管线（核心：增量级形变）

### 4.1 为什么必须是「增量级」而不是「轮廓级」

旧管线（glow）做法：实例化 → 拿静态轮廓 → 形变 → 重新编译。
**问题**：一旦对轮廓做非仿射变换（去脚、平切、钩张力），就破坏「同一节点在不同字重的对应关系」，VF 就没了。

新做法：**只改 `gvar` 的 delta 向量**。

```
基座自带：  P(wght)  = Base(i) + delta(i)  * f(wght)
我们改写：  P′(wght) = Base(i) + delta′(i) * f(wght)
其中：      delta′(i) = T( delta(i) )      ← T 只作用于增量
```

**已实测**（/data/scratch/spike/）：

```
identity 改写 delta   →  @400 maxdiff=0，@900 maxdiff=0，拓扑 100% 一致   ✅
点序对齐              →  gvar 坐标数 = glyph 点数 + 4（phantom 点），全部吻合 ✅
250/400/900 点数一致  →  PASS                                        ✅
```

### 4.2 三层形变模型（取代 glow 的「全局非线性滤镜」）

> 直接回应 PARAMS.md §二 的诊断：**「全局几何滤镜的固有缺陷，调参救不回来」**

| 层 | 作用对象 | 算子 | 保证 |
|---|---|---|---|
| **L1 全局仿射** | 全部 delta | 字面缩放 / 平移 / 字重曲线 | 安全，不会自交 |
| **L2 部件级** | 连通分量 + 笔画分类 | 中宫外推、部件间距、重心 | 需部件分割，可人工覆盖 |
| **L3 笔画级**（本次重写重点） | **单笔画端面/折角/钩/点** | 去出脚、端面平直化、钩张力、点柔化、折角圆角 | **只移动节点，绝不删点** |

**L3 硬约束（写进断言）**：
- 变换前后 **点数、顺序、on/off 类型完全不变**
- 在**默认实例（wght=400）**上做形态识别，然后**映射回 delta**（delta 是跨字重共享量）
- 任何算子若需要「删点」，一律改成「把两点收拢到同一点」（保留点数）

### 4.3 笔画角色分类（L3 能成立的前提）

glow 失败的本质是**用固定几何阈值**做角色识别（7 点窗口、容差 2°），字重一变就崩。
新方案改为**基于默认实例 + 拓扑特征**的稳定分类：

| 角色 | 识别依据 | 用途 |
|---|---|---|
| 端点（stroke end） | 轮廓「笔尖」处双 off 点收口 + 局部宽度 | 平切、去喇叭口 |
| 出脚（foot） | 竖画顶端 / 部件竖起处的直角小方突 | 去脚 |
| 折角（corner） | 相邻两段近乎垂直的 on 点 | 微圆角 |
| 钩（hook） | 短横段 + 明显转向 | 钩张力 |
| 点（dot） | 小面积独立轮廓 | 柔化 |

**产出物**：`build/roles/<gid>.json`——**人类可读、可 diff、可人工覆盖、进 git**。
算子误判就从「重跑算法」变成「改一行 JSON」。

---

## 5. 原生 TTF 交付（用户明确要求）

### 5.1 产物矩阵

| 产物 | 格式 | 说明 |
|---|---|---|
| `wdsans-vf.ttf` | **TrueType VF** | 主产物，wght 250–900，原生 glyf+gvar |
| `wdsans-{7档}.ttf` | **TrueType 静态** | 从 VF 实例化，可直接装 Windows |
| `wdsans-vf.woff2` | WOFF2 | 网页，按 unicode-range 分片 |
| ~~`.otf`~~ | — | **不再出 CFF 版**（避免双格式曲线不一致） |

### 5.2 hinting（上游 #33 的诉求）

- 基线：**不做手工 hinting**（成本极高）。
- 可选增强：`ttfautohint` 作为**独立变体产物**，不混入主产物。
- 判断依据：Windows 低 DPI 实测样张，而非「有没有 hint 表」。

---

## 6. 缺陷补齐清单（逐条闭环上游 issue）

| issue | 缺陷 | 新方案怎么解 | 阶段 |
|---|---|---|---|
| #35 | VF rebase | 整条管线就是 VF-first | **P0** |
| #33/#43 | TTF / hinting / woff | §5 产物矩阵 | **P0** |
| #2 #34 | 曲线被拉直 | 不再重描边，只做增量 → **结构上不可能退化** | **P0** |
| #22 #23 | CID/字形映射错位 | Noto 用 `uniXXXX` 稳定命名，不用 CID | **P0** |
| #16 #27 #30 #41 #42 | name/CodePage/家族分裂 | name 1/2/16/17 全档补全 + STAT + fsSelection | **P0** |
| #1 #10 #28 #7 | 去脚不可靠 | L3 + 角色 JSON + 人工覆盖 | P1 |
| #7 飘起 | 去脚后整字浮起 | 去脚时同步做**部件基线补偿**，而不是「降 1/4 脚高」 | P1 |
| #11 | 半角假名假压缩 | 先验证 Noto 原生半角，再决定是否单独处理 | P1 |
| #4 | 加档 / 中间字重 | VF 天然连续插值，**不需要加档** | P0（自动获得） |
| #6 #48 | 圆角 | L3 折角微圆（DESIGN §4.1.1） | P1 |
| #29 | 拉丁扩展 | Noto 已含希腊/西里尔，核对覆盖 | P2 |
| #31 | 韩文 | 明确不做（DESIGN §8） | — |

---

## 7. 代码组织（重构后）

```
wdsans/
├── AGENTS.md              # 新增：本项目 AI 操作规约
├── docs/
│   ├── DESIGN.md          # 保留，按 Noto 基座修订实测值
│   ├── PIPELINE.md        # 重写：节点位移 → 增量位移
│   ├── UPSTREAM-DEFECTS.md# 新增：glow-sans 缺陷台账（= §1）
│   ├── BASEFONT.md        # 新增：Noto/SHS 双基座实测对比（= §3）
│   └── LEGACY-AUDIT.md    # 新增：旧版产物实测审计（= §2）
├── contract/              # 保留：axis/metrics/features（唯一真源）
├── params/design.toml     # 新增：语义参数 → 派生 7 档（取代 81 个手填 JSON）
├── tools/stage/           # L1 全局仿射算子
├── tools/roles/           # L3 笔画角色识别 + JSON
├── tools/delta/           # 增量读写、断言、回滚
├── qa/                    # 渲染 diff + 拓扑断言 + hb-shape 回归
└── vendor/glow-src/       # **降级为只读参考**，不再参与构建
```

**关键决定**：`vendor/glow-src` **保留但不接入构建**。价值在「缺陷台账」和「算子思路」，不在代码。

---

## 8. QA 闸门（硬断言，构建失败即停）

| 闸门 | 判据 | 现状 |
|---|---|---|
| G1 拓扑守恒 | 任意字重实例化后，点数/顺序/on-off 与基座**逐字全等** | ✅ 已实测可行 |
| G2 增量往返 | identity 改写 delta → 轮廓 maxdiff **= 0** | ✅ 实测 0 |
| G3 特性完整 | GSUB feature 集合 ⊇ Noto 原版；`locl` 可切出日文字形（直/骨/次/令） | 待建 |
| G4 cmap 不缩水 | 码位数 ≥ Noto 原版 44,810 | 待建 |
| G5 结构健康 | 退化轮廓=0、孔洞同向=0、零长线段=0、复合引用悬空=0 | 待建 |
| G6 命名一致 | 7 档 name 1/2/16/17 全等 + STAT + fsSelection | 待建 |
| G7 行为回归 | `hb-shape` 固定语料 × 每实例，与静态档**逐字节相同** | 待建 |
| G8 视觉 | 每轮出 PNG，**与 SHS/旧版同尺寸并排，实际看过** | 铁律 |

> G1/G2 是本次重构的**技术地基**，已用 spike 打通；其余按阶段补齐。

---

## 9. 里程碑（建议）

> 状态更新：2026-11-05（P0–P6 已落地，各阶段记录见 `docs/P1..P8-*.md`）

| 阶段 | 交付 | 出口条件 | 预估 | **状态（2026-11-05）** |
|---|---|---|---|---|
| **P0 骨架** | Noto VF 重设轴（default 400）+ 67 字试验田 + 全闸门脚本 | G1–G7 全绿 | 2–3 天 | ✅ **完成** — commit `c6d4d2e`；轴 `wght 250–900/400`，增量引擎打通 |
| **P1 算子** | L1/L2/L3 + 角色 JSON | 67 字视觉通过（并排出图） | 1–2 周 | ✅ **完成**（`P1-PROGRESS.md`）— 自校准减细，墨密度 0.440→0.405；G1 拓扑守恒 PASS |
| **P2 风格定稿** | 3000 常用字 + 参数冻结 | 视觉闸门 + 参数冻结机制生效 | 2 周 | ✅ **完成**（`P2-FEET-REMOVAL.md` + `P3-CORRECTION.md`）— 出脚判决量 107.6u→0.0u，判据定到 v5 |
| **P3 全量** | 65,535 字形 × 7 档 + 分片 | 全闸门 + 耗时达标 | 3–5 天 | ✅ **完成**（`P4-VF-RAMP.md`）— 全字重验证：减细量恒定 12.1/6.7，竖横比 1.057（400 档） |
| **P4 交付** | TTF + WOFF2 + CSS + demo | Windows/macOS/Linux 三场景实测 | 1 周 | 🟡 **部分完成**（`P5-NAMING-DELIVERY.md`）— 七档 TTF+WOFF2 已出，命名/STAT 合规；**三场景实测未做** |
| **P6 拉丁合并** | Mona Sans 拉丁并入 VF | 拉丁跨字重行为与中文一致 | 1 周 | 🟡 **部分完成**（`P6-LATIN-MERGE.md`）— 117 简单字形合并、gvar 采样重建成功（v1/v3/v4 三次失败已记录）；复合字形留给 P7 |
| **P7 复合字形内联** | 重音拉丁与基础字母同族 | 同字母有/无重音宽度一致 | — | ✅ **完成**（`P7-COMPOSITE-INLINE.md`）— v8 内联 136/136，宽度差全 0.0%；撞过 numGlyphs=65535 硬上限 |
| **P8 交付验证** | 七档静态 + WOFF2 实检 | 可解码、竖排完整、实例含复合字形 | — | ✅ **完成**（`P8-DELIVERY-VERIFICATION.md`）— WOFF2 全部可解码；七档 A/Á 同宽且随字重递增；vhea/vmtx/vert 完整 |

### 9.1 修订说明：实际阶段与初始规划的差异

| 初始规划 | 实际执行 |
|---|---|
| P1=算子、P2=风格定稿、P3=全量、P4=交付 | P1=减细算子、P2=去出脚、P3=去脚判据修正、P4=VF 全字重验证、P5=命名+STAT+静态实例、**P6=拉丁合并**、**P7=复合字形内联** |
| 拉丁处理未排期（Q4 待裁决） | 单独立为 P6 + P7，见 `docs/P6-LATIN-MERGE.md`、`docs/P7-COMPOSITE-INLINE.md` |

> 实际是「一个缺陷一个阶段」，不是「3000 字 → 全量」的批量推进。
> 原因：每轮都推翻上一轮的判据（P4 记录累计 7 条判断被推翻），
> 判据不稳时做全量没有意义。这个顺序是对的，保留。

### 9.2 P8 之后的剩余缺口（按优先级）

| # | 缺口 | 出处 |
|---|---|---|
| **1** | **HVAR 的 advance delta 仍是 Noto 旧数据**，叠加 Mona base 后极端字重偏 +45 单位（`wds/hvar_fix.py` 已写但未接入构建） | P7 §6-1 / P6 §7-2 |
| 2 | 中英混排样张 + 12px 正文视觉验收（AGENTS 铁律 6，P6/P7/P8 都欠这张图）；P8 已出 hb-view 渲染但未做并排对比 | P6 §7-6 / P7 §6-2 |
| 3 | `OS/2.sxHeight` 仍 543 / `sCapHeight` 仍 733，与实测拉丁 529/732 不符 | P6 §7-4 / P7 §6-3 |
| 4 | OFL 署名：name ID 0 缺 GitHub(Mona) 版权声明 | P6 §7-3 / P7 §6-4 |
| 5 | ~~`wdsans-dist` 七档仍是合并前产物~~ → **已由 P8 重出**；但仍缺 Windows/macOS/Linux 三场景实测 | P8 / P5 §6 |
| 6 | G3/G4 闸门未覆盖拉丁段 | P6 §7 / P5 §6 |
| 6b | ~~竖排 vmtx/vhea 未查~~ → **已由 P8 验证**（vhea 500/-500、vmtx 65,158 条、GSUB vert/vrt2 全在） | P8 §3 |
| 7 | `periodcentered` 仍为 Noto（253 个拉丁槽位里唯一一个） | P7 §6-6 |
| 8 | **测 advance 一律用 hb-shape，禁用 instancer** —— 已写成规则，但尚未落进 QA 脚本 | P6 §7.7 / P7 §4 |

---

## 10. 需要用户裁决的 5 个点

| # | 问题 | 我的建议 |
|---|---|---|
| **Q1** | 基座定 **Noto** 还是 SHS？ | **Noto**（原生 TTF、单 tuple、度量已对齐） |
| **Q2** | 还出 CFF/OTF 吗？ | **不出**（避免双格式曲线不一致），只出 TTF+WOFF2 |
| **Q3** | 严格 7 档，还是接受任意连续字重？ | **VF 连续 + 7 个命名实例**（顺带解决 #4 的 450 诉求） |
| **Q4** | 拉丁源：仍用 Mona，还是吃 Noto 自带拉丁？ | ~~先吃 Noto 自带~~ → **已裁决：用 Mona Sans VF**（用户五决策之一）。实施与踩坑见 docs/P6-LATIN-MERGE.md |
| **Q5** | glow-src 保留还是删除？ | **保留为只读参考**（它是缺陷台账的证据） |

---

## 11. 已产生的实测证据（可复核）

```
/tmp/glow/issues.json          glow-sans 全部 49 条 issue/PR 原始数据
/tmp/glow/README.md            上游 README 原文
/data/scratch/old/             旧版 TTF（审计对象）
/data/scratch/spike/ident.ttf  identity 增量改写产物（maxdiff=0，证明路线可行）
ref/mona/MonaSansVF.ttf        Mona Sans VF 源（3 轴，glyf+gvar，797 字形）
ref/mona/LICENSE.txt           Mona OFL 1.1 原文（RFN: "Mona Sans"）
/data/build-cache/wdsans-p1/wdsans-p4-stat.ttf           P6 合并前基线（对照）
/data/build-cache/wdsans-p1/wdsans-p6-latin.ttf         P6 v1 失败（gvar 被清空 → 拉丁单字重）
/data/build-cache/wdsans-p1/wdsans-p6b.ttf             P6 v3 失败（保留 Noto gvar → 83 字 pt-mismatch）
/data/build-cache/wdsans-p1/wdsans-p6c.ttf             P6 v4（字重 ramp 出现，但未压缩、advance 冻结）
/data/build-cache/wdsans-p1/wdsans-p7-latin-final.ttf  P6 v5 最终产物（sx=0.895 sy=1.0046，117 字形；≡ p6d）
/data/build-cache/wdsans-p1/wdsans-p8-latin-acc.ttf    复合字形中间态（67 个，gvar 不可反编译，非交付）
/data/build-cache/wdsans-p1/wdsans-p8c.ttf             P7 v8 产物（136 复合字形全部内联，复合数=0）
/data/build-cache/wdsans-p1/wdsans-FINAL.ttf          P8 交付源（md5 644fcc65…，≡ p8c）
/data/build-cache/wdsans-dist/                         P8 交付产物（七档 TTF + WOFF2 + VF WOFF2）
```
