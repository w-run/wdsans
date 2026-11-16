# AGENTS.md — WDesign Sans 字形改造工程规范

> 给所有参与本项目的智能体/协作者。**动手前必读**。
> 项目：WDesign Sans（个人使用），基于 Source Han Sans 2.005 改造成 OPPO Sans 风格。

---

## 0. 绝对原则

### 0.1 基座纪律
- **当前基座 = `build/masters_MOD3`**（见下方链）。任何新模块从最新链尾出发。
```
masters_T6    SHS + taper + step-align + 乙乞        已部署
masters_MOD   T6 + m_barple 6,595字                  已部署
masters_MOD2  MOD + termface 19,546字                已部署
masters_MOD4  MOD2 + bardiag 3,077字 (修好版)        已部署
masters_MOD5  MOD4 + yanrad 62字                     已部署
masters_MOD6  MOD5 + shortl 3,369字                 已部署
masters_MOD7  MOD6 + zerocont 45字                  已部署
masters_MOD8  MOD7 + termface_v2 6,583字            已部署
masters_MOD9c MOD8 + taper_v2 17,405字               已部署
masters_MOD10 MOD9c + residue 清理 186字             已部署
masters_MOD12 MOD10 + latinmat 371字形               已部署
masters_MOD13 MOD12 + latinext 95字符               已部署
masters_MOD14 MOD13 + latinext2 48字符              已部署
masters_MOD15 MOD14 + kerning 77,294对               已部署
masters_MOD16 MOD15 + mark/mkmk 重建                 已部署
masters_MOD17 MOD16 + metrics/fsSelection 修正         已部署
masters_MOD18 MOD17 + name 表修正                     已部署
masters_MOD19 MOD18 + OS/2 UnicodeRange 修正           已部署
masters_MOD20 MOD19 + 时间冒号居中 (calt)              已部署
masters_MOD22 MOD20 + 数字特性 sups/subs/sinf         已部署
masters_MOD23 MOD22 + 特性 pnum/numr/dnom             已部署
masters_MOD24 MOD23 + frac 分数特性                   已部署
masters_MOD26 MOD24 + 长曲线曲率压平                   已部署
masters_MOD29 MOD26 + 顶部横笔右端延伸(横折出头) 1,182字 已部署
masters_MOD30 MOD26 + 顶部横笔右端延伸 v2 2,636字     ⚠️曲线已损坏，废弃

# ⚠️ 现行链（2026-11-15 曲线事故后重建，跳过 termface）
masters_R1  = MOD  + shortl      3,373字
masters_R2  = R1   + zerocont       45字
masters_R3  = R2   (yanrad 0命中)
masters_R4  = R3   + bardiag     3,074字
masters_R5  = R4   + latinmat     371字形
masters_R6  = R5   + latinext     143字符
masters_R7  = R6   + kerning   77,294对
masters_R8  = R7   + markpos      22×442
masters_R9  = R8   + metrics     fsSel 0x0040
masters_R10 = R9   + nametable     31条
masters_R11 = R10  + os2range      21位
masters_R12 = R11  + coloncenter    2字符
masters_R13 = R12  + numfeats      20字形
masters_R14 = R13  + numfeats2     20字形
masters_R15 = R14  + frac           3档
masters_R16 = R15  + ledge      2,636字
masters_R17 = R16  + latinwidth   （无效：advance 本已等于 Mona@400）
masters_R18 = R16  + latinreset   486字形宽恢复
masters_R19 = R18  + featlang     7特性注册到全语言 已部署 ← 当前链尾
masters_R20 = R19  + digitmono    （实验：中文数字强制等宽 -> 与 pnum 冲突，废弃）
masters_R21 = R20  + pnumfix      （实验：pnum 与 locl 抵消，废弃）
masters_R22 = R19  + curvflat   14,878字/54,419曲线  已部署 ← 当前链尾
```
- 任何修改**必须从 T6 出发**，不得从 T3/T4/T5/T7 等中间产物出发。
- **T7 已污染**（含被改坏的 `永`），禁止作为基座。
- 每轮修改输出到**新目录**（`masters_MOD` 等），不要原地覆盖。

### 0.2 三档同步铁律
VF 构建要求 250/400/900 三档的**段数与操作符完全一致**，否则报
`VarLibCFFPointTypeMergeError`。

**正确做法（400 档驱动）：**
```bash
python modules/run_module.py <模块> all
# 内部: detect(400) -> 索引JSON -> apply 三档
```

**禁止做法：** 三档各自独立检测。粗档笔画宽会让阈值失衡，命中集不同 → 构建失败。
> 2026-11-14 实测：独立检测导致 `亨`/`今`/`延` 三档结构不一致。

### 0.3 验证门禁（缺一不可）
1. 单字渲染确认（用 `glyphview.py`，不用临时脚本）
2. **三档操作符签名校验**（全库 20992 字，不一致必须为 0）
3. VF 构建成功
4. 部署后审计（改动字数 = 索引字数，边界突变 = 0）

---

## 1. 渲染工具（**唯一入口**）

```bash
# 整字对比（多字体）
python modules/glyphview.py --chars 永今亨 --fonts A.otf:当前 B.otf:OPPO -o /tmp/x.png

# 局部放大 + 坐标网格
python modules/glyphview.py --chars 延 --fonts A.otf:当前 B.otf:OPPO \
    --win 0,420,-150,650 --grid 50 -o /tmp/y.png

# 可变字体指定字重
python modules/glyphview.py --chars 永 --fonts VF.otf:w700:700 --grid 100 -o /tmp/z.png
```

- `--win x0,x1,y0,y1`：em 坐标矩形裁剪，**y 向上为正**
- `--grid N`：网格间距（em 单位），带坐标标注
- 字体 spec：`path:标签[:wght]`

### ⛔ 严禁自己写渲染脚本
`probe/` 下已有 22 个历史渲染脚本，且都可能有 QM/CFF 曲线处理缺陷。
**统一用 `modules/glyphview.py`**（内部走 `SVGPathPen`，曲线零解析）。

> 2026-11-14 教训：我临时写了 20+ 个残缺渲染脚本，`QM`（多二次曲线）段处理错误，
> 导致多次误判字形。用户明确指出："脚本里应该有很多渲染脚本吧，为什么每次都要重新写一个？"

### 渲染的常见错误
| 错误 | 现象 | 正确做法 |
|---|---|---|
| `endp(s) = s[-1]` 不处理 QM | `ValueError: inhomogeneous shape` | 用 `SVGPathPen` |
| SVG `scale(sx,sy)` 传 4 参数 | 渲染空白 | `scale(k,-k)` 只两参数 |
| `translate(-x0,-y1)` | 字形被推出画布 | `translate(-x0,-y0)` |
| 裁剪窗口凭猜 | 只截到局部或空白 | 先用 `--grid` 看全字定位 |

---

## 2. 已验证的改造模块

| 模块 | 作用 | 规模 | 状态 |
|---|---|---|---|
| `m_taper.py` | 撇/提/捺末端收窄 NARROW=0.95 | 45,611 处 | 已部署 T6 |
| `m_stepalign.py` | 相邻轮廓台阶对齐 | 2,947 处 | 已部署 T6 |
| `m_barple.py` | 横线右端对齐撇右界 + 落点下移 + 删回折段 | 6,595 字 | 已部署 (MOD) |
| `m_termface.py` | 笔端面微弧拉直 (C→L) | 19,546 字 | 已并入 MOD2 |
| `m_bardiag.py` | 横线右端延伸到斜边外缘 (消台阶) | 3,077 字 | 已并入 MOD4 |
| `m_yanrad.py` | 廴/辶旁顶端尖角消除 | 62 字 | 已并入 MOD5 |
| `m_shortl.py` | 删除曲线间冗余短直线段 | 3,369 字 / 4,966 段 | 已并入 MOD6 |
| `m_zerocont.py` | 删除零面积退化轮廓 | 45 处 | 已并入 MOD7 |
| `m_termface_v2` | 端面拉直阈值放宽 0.10→0.16 | 6,583 字 / 10,155 段 | 已并入 MOD8 |
| `m_taper_v2` | 撇捺末端收窄（termface 后重跑） | 17,405 字 / 56,839 段 | 已并入 MOD9c |
| `m_latinmat` | 拉丁横向缩放匹配 CJK 笔干 | 371 字形 | 已并入 MOD12 |
| `m_latinext` | 从 Mona 补入 Latin Extended-A | 95 字符 | 已并入 MOD13 |
| `m_kerning` | 从 Mona 移植拉丁 kerning | 77,294 对 | 已并入 MOD15 |
| `m_markpos` | 重建 mark + mkmk 定位表 | 22 符号 / 442 基字母 | 已并入 MOD16 |
| `m_metrics` | 修正 fsSelection 标志 | 3 档 | 已并入 MOD17 |
| `m_nametable` | 修正 name 表：中文名/版权/OFL 声明/VF 元数据 | 3 档 | 已并入 MOD18 |
| `m_os2range` | 按实际 cmap 重算 OS/2 ulUnicodeRange | 21 位 × 3 档 | 已并入 MOD19 |
| `m_coloncenter` | 时间场景冒号居中 (数字间 calt) | 2 字符 × 3 档 | 已并入 MOD20 |
| `m_numfeats` | 数字特性 sups/subs/sinf + 上下标字符 | 20 字形 × 3 档 | 已并入 MOD22 |
| `m_numfeats2` | pnum 比例数字 + numr/dnom 分子分母 | 20 字形 × 3 档 | 已并入 MOD23 |
| `m_frac` | frac 分数特性（含 ChainContext） | 3 档 | 已并入 MOD24 |
| `m_curvflat` | 长曲线曲率压平（撇捺变直） | 14,825 字 / 53,142 曲线 | 已并入 MOD26 |
| `m_ledge` | 顶部横笔右端延伸（横折出头） | 2,636 字 | 已并入 MOD30（v2） |

### m_termface 判据（端面改直）
```
命中: 段长 L ∈ [0.8, 1.5] × SW  且  弯曲偏离比值 dev/L < 0.10
修复: 该 C 段 → L 直线
```
**关键：必须检查弯曲度比值**，否则会误伤竖钩等有弧度的短段。
> 实测：`永` 的竖钩 seg7 L=93.9 ratio=0.252，只按长度会误改；端面 ratio≈0.04。

### m_termface v2（阈值放宽 0.10 → 0.16）
```
命中: 段长 [0.8, 1.5]*SW  且  弯曲偏离比值 dev/L < 0.16
修复: C -> L
```
**为什么可以放宽**: 弯曲度分布有天然分界
```
ratio 0.04~0.10:    747 段   (原 v1 已处理)
ratio 0.12~0.16:  13,723 段  <- v2 新增，端面微弧集中区
ratio 0.18~0.28:   9,228 段  <- 明显弯曲，不动
ratio 0.30+ :      8,000 段  <- 真实弧线
```
实际在 MOD7 上扫描: 6,583 字 / 10,155 段，安全阀零跳过。
抽查 局/儳/夠/莲/闖 的命中段，全部位于字形边缘、朝向向外，确认为端面。

### m_bardiag 判据（横线未达斜边）
```
bar : 3段纯L，宽≥1.0×SW，高≤2.5×SW
diag: 同字内与 bar 的 y 区间重叠的轮廓
缺陷: 0.05×SW ≤ (diag外缘x − bar右端x) ≤ 0.60×SW
修复: bar 两个右端点各自 → diag 在该 y 处的外缘 x
```
验证：`建` 左上横折 C5 292→315/307（消 23 单位台阶）；`延`、`永` 同类。

### m_yanrad 判据（廴旁顶端尖角）
```
识别: 9段轮廓, 签名 CLCLLLCCL (建/延/健/庭/廷/挺 六字实测一致)
      a4=seg2终点(斜边顶)  a5=seg3终点(尖角)  a6=seg4终点  a7=seg5终点
匹配: 同字内 3段纯L 横线, 右端在 a4 的 [-0.6, 1.2] SW 内, y 区间覆盖 a4
修复: a4 -> (bar.xR, bar.yBot)   斜边顶收到横线右下角
      a5 -> (bar.xR, bar.yTop)   尖角收到横线右上角 (形成垂直新边)
      a7 -> 由新 seg2 法向偏移 w0 决定, w0 = 原 a7 到原 seg2 的法向距离  <- 保斜边宽
      a6 -> a7 沿原 a6->a7 反向
```
**关键: a7 必须用「法向偏移保宽」算法**, 否则斜边会被压窄。
> 实测: 直接沿用 a5->a6 方向内收, 延 顶端厚度 78 -> 44 (-35)。

全库: 含该签名 63 字, 命中 62 字 (98%)。抽查 扬/杨/场/汤/艇 无误报。

### m_shortl 判据（曲线间冗余短直线段）
```
命中: L 段, 长度 0.3 ~ min(15, 0.20*SW), 且前后段都是 C(曲线)
修复: 直接删除该段 (前后曲线端点自然衔接)
```
**为什么安全**: 短直线段夹在两条曲线之间，是台阶对齐的残留。
删除后两条曲线端点重合，几何形状不变。

全库短L段分类: C-L-C 3523 处(可删) / L-L-C 2776 / L-L-L 3011 / C-L-L 373。
**只处理 C-L-C**，其余类型会破坏结构。
> 实测: 3,369 字 4,966 段，安全阀(零长度段不增)跳过 0 字。

### m_zerocont 判据（零面积退化轮廓）
```
命中: 轮廓面积(鞋带公式) < 50 em²
典型形态: A->B->B->A 往返直线 / 3段共线 L 围成
修复: 整个轮廓删除 (保证至少留 1 个轮廓)
```
**为什么安全**: 零面积轮廓不产生任何视觉内容，只浪费数据。
> 实测: 全库 20,992 CJK 中 45 处，全部段数=3 共线三角形。
> 例: 匣 C5 (951,-14)->(141,-14)->(141,-14)->(951,-14) 叉积 0.0000

### 模块饱和度检查（2026-11-15）
在 MOD9c 上重跑全部模块的 find()，看还有多少可改：
```
barple       1 字     1 处   已饱和
stepalign  188 字   192 处   有 residue
bardiag     29 字    30 处   有 residue
yanrad       0 字     0 处   已饱和
termface     0 字     0 处   已饱和
shortl       0 字     0 处   已饱和
zerocont     0 字     0 处   已饱和
```
residue 来源: 前面模块改动几何后，产生了新的可处理项。
MOD10 依次应用 barple → stepalign → bardiag，得到 186 字 218 步。
> 仍有 30 字跳过（索引段号在其它档越界），属正常边界情况。

### ❌ 已否决: m_zeroseg（删除零长度段）
```
现象: 250档 2478处 / 400档 17处 / 900档 23处 零长度段
尝试: 每档独立检测并删除
结果: 门禁 G3 报 1199 字三档不一致 FAIL，禁止部署
```
**为什么不能删**: 在 250 档是零长度的位置，在 900 档是真实短边
```
250档零长度的 2478 个位置，在其他档的实际段长:
  400档: 中位 5.00,  >5单位占 29.3%
  900档: 中位 13.00, >5单位占 97.9%   <- 完全是正常笔画边
```
若从 250 档删掉，400/900 档对应位置仍有段，三档段数不同 → VF 无法插值。

**正解**: varLib 构建 VF 时本来就会静默丢弃零长度段，
且当前 MOD10 能成功构建且三档一致 —— 说明 varLib 已正确处理。
**结论: 零长度段不需人工清理。**

### m_latinmat 判据（拉丁笔干匹配 CJK）
```
位图实测（200px 字号, 多字号交叉验证）:
              字号100  150    200    300    400    平均
  我们(MOD10)  1.241  1.191  1.187  1.209  1.207  1.201
  OPPO Sans    1.143  1.135  1.139  1.136  1.135  1.136
  -> 我们的拉丁竖干相对 CJK 过粗 5.7%

修复: 拉丁字形所有轮廓点沿 x 绕字形中心缩放 k=0.943
      advance width 不变；缩放不改段数与操作符 -> 三档自动一致
```
**测量方法**：PIL 渲染 200px 位图，取字形高度 30%~70% 区间每行墨段宽度众数（笔干），
CJK 取样 `口日田目`，拉丁取样 `HnIEL`。多字号交叉验证确保稳定。

**为什么用横向缩放而非换字重**：Mona Sans 是 VF，换字重需重建整条 10 阶段链；
横向缩放只改最终 masters，4~6% 缩放在视觉上几乎不可察。

实测效果（k=0.943）: 比例 1.201 -> 1.137（OPPO 1.136）。
覆盖范围: Basic Latin + Latin-1 + Latin Ext-A/B + IPA + Latin Ext Additional
          + General Punctuation + Currency Symbols（371 字形）

### m_latinext 判据（补入 Latin Extended-A）
```
问题: Latin Ext-A 只有 30/128，Mona 有 123 个
      缺的是捷克/波兰/匈牙利/土耳其等语言的必需字符 ĄąĆćĘęŁłŐőŘřŠšŹźŽž

硬约束: VF 已达 65,535 字形上限，无空余槽位
        但有 21,189 个未映射字形（glyph#####），未被 GSUB/GPOS 引用，可安全复用

方案: 1) 从 Mona VF 按 250/400/900 实例化（wght 轴）
      2) 取缺失字符轮廓，注入未映射槽位
      3) 添加 cmap 映射 + advance width
      三档用同一批槽位 -> 结构自动一致
```
**关键坑: 必须用 `DecomposingRecordingPen`**
Mona 的 Latin Ext-A 多为复合字形（基字母 + 变音符号）。
`RecordingPen` 对复合字形只返回 1~2 个组件引用，拿不到真实轮廓。
> 实测: 用 RecordingPen 只成功注入 12/95 个（其余轮廓为空被跳过）
>       改用 DecomposingRecordingPen 后 95/95 全部成功
>       例: Ą Recording=2 ops / Decomposing=27 ops

效果: Latin Ext-A 30 -> 125/128，cmap 44,853 -> 44,948
抽查宽度: ą=598（与 a 一致）Ć=763（与 C 一致）

### 🔴 许可合规：只能从 OFL 源取字形
```
OPPO Sans 许可第2条:
  "YOU may not make any modifications to OPPO Sans Fonts
   or any of their individual components."
  -> 明确禁止修改与再分发组件，不能取用其字形

MiSans 版权: Copyright (c) 2020-2025 Beijing Xiaomi Mobile Software Co.,Ltd.
  字体内部无 license 声明，许可不明 -> 保守不使用

可用源（SIL OFL 1.1）:
  Mona Sans  ref/mona/MonaSansVF.ttf    cmap 568   有 wght 轴
  SHS         ref/shs/shs-400.otf       cmap 44,853
  -> SHS 与我们基座同源，拉丁覆盖完全相同，补不了东西
  -> 实际只能用 Mona
```
**教训**: 2026-11-15 曾用 MiSans(241)+OPPO(39) 补入 281 字符，
贡献了 IPA +81 / Comb Diacrit +52 等显著覆盖，但**许可不合规，全部废弃**。
合规的 Mona-only 只能补 48 个：Ext-B +7 / Spacing Mod +6 / Comb Diacrit +17
                        / Ext Add +7 / Gen Punct +1 / Currency +5
                        / Number Forms +4 / Letterlike +1

**参考 vs 取用的边界**:
  OPPO/HOS/MiSans 用于**风格参考**（测量比例、观察笔画形态）是合理的；
  把它们的**字形轮廓复制进我们的字体**则超出许可范围。

### m_kerning 判据（移植拉丁 kerning）
```
问题: 我们 VF 的 kern 配对只有 845 个，Mona 有 3,261 个（少 74%）
      → 字距整体过宽，A/V、A/Y 等经典配对未收紧

实测（72px 位图墨宽）:
  配对   改前  Mona   差值
  AV      91    81    +10
  AY      90    81     +9
  WA     114   107     +7
  VA      92    82    +10

方案:
  1. 从 Mona GPOS 提取全量 kern（含 class-based Format2 展开）
     → 展开后 151,815 对
  2. 按字形名映射（双方交集 543 个字形）→ 77,294 对可用
  3. 用 buildPairPosGlyphs 生成新 PairPos lookup，追加到 kern feature
```

**关键: kerning 强度需缩放 KERN_SCALE=0.65**
Mona 的 kern 值基于其自身字宽；我们经 `m_latinmat` 缩放到 0.943 后字更窄，
直接全量移植会让本已合适的配对变过紧。
```
系数  与 Mona 平均偏差   评价
1.00      3.19 px        AT/LT/To/T- 变过紧
0.65      2.44 px        最优
0.50      2.88 px        偏松
改前      5.62 px        —
```

**API 坑**: `buildPairPosGlyphs` 三个参数细节
- 第1参数是 dict: `{(g1,g2): (ValueRecord_or_None, ValueRecord_or_None)}`
- `buildValue()` 只接受一个 dict: `buildValue({'XAdvance': v})`
- 返回的是 **subtables list**，需自行包 `ot.Lookup()` 并设 LookupType=2
> 连续踩三次: 传 list → 'list has no items'; 传 dict 值 → 'dict has no getFormat';
>              buildValue(xAdvance=v) → 'unexpected keyword argument'

### m_markpos 判据（重建 mark + mkmk）
```
问题: 我们 mark feature 只覆盖 6 个组合符号（共 22 个），mkmk 完全缺失
      → 多符号横向并排而非垂直叠加

实测（80px 位图）:
  组合                改前宽度  修复后  Mona
  a+acute+tilde         69      32     34
  o+diaeresis+macron    55      38     37
  e+circ+acute          39      39     35

方案（不依赖 Mona — 它的 mkmk 只覆盖 23+2 个符号，太窄）:
  1. 组合符号锚点 = 底部包围盒中心 (x_mid, y_min)
  2. 基字母锚点   = 顶部包围盒中心 (x_mid, y_max)
  3. 生成 MarkBasePos (mark, type 4) + MarkMarkPos (mkmk, type 6)
  覆盖: 22 组合符号 × 442 基字母
```

**关键坑: Coverage 必须按 glyph id 排序，不能按字形名**
```python
# 错误: sorted(marks.keys())        -> 按字符串排序
# 正确: sorted(marks.keys(), key=lambda g: gidmap.get(g, 999999))
```
> 实测: 按字形名排序时，三档的 Coverage 顺序不同 →
>       VF 构建报 `InconsistentGlyphOrder: GPOS.table.LookupList.Lookup[12][0]`
>       改为按 glyph id 排序后正常。
> 教训: 任何新建的 Coverage/ClassDef 都必须按 glyph id 排序，
>       因为三档的字形名顺序可能不同，但 glyph id 顺序在三档是一致的。

### 字形比例体检（2026-11-15，三项核心指标全部达标）
```
指标              我们      OPPO      HOS       判定
字面宽(800字采样)  916      896      907       与 HOS 一致
字面高(800字采样)  903      910      902       与 HOS 一致
重心(墨质心)      0.512    0.511    0.501      与 OPPO 一致
中宫(墨密度)      46.8%    44.7%    46.1%      与 HOS 一致
```

**测量方法（可复现）**:
- 字面宽/高：800 个 CJK 的 bbox 均值（em=1000）
- 重心：PIL 渲染 400px 位图，墨迹质心在 bbox 内的相对位置（0=顶, 1=底）
- 中宫：墨面积 / bbox 面积（AreaPen），越低中宫越开

**结论**: 我们的字体在 OPPO 与 HOS 的共通点内，无需调整。
OPPO 的 y 范围整体比我们低 30 单位、右边界收到 931，属于它自己的比例体系；
HOS 与我们几乎完全一致（宽+9 高+1 中心y-3）。

**字面率异常检查**: 20,992 字中，宽或高 >1000 的 0 个，宽高均 <420 的 0 个。

### 拉丁完整性验证（2026-11-15）
```
1) 新注入 Latin Ext 纵向对齐
   A: 我们 y[0,729]  Mona y[0,729]   dy=+0/+0   ✓
   （Ą/Ć/Ł/ő/Š 等有变音符号的，y 范围自然更大，属正常）

2) Ẁ 宽度 953 不是异常
   Mona@400:  W adv=994 ink x[43,953]
               Ẁ adv=994 ink x[43,953]   ← 与 W 完全一致
   之前误判是因为拿 Ẁ(953) 和 A(649) 比。

3) advance 混用 SHS/Mona 但整体协调
   78 个字符换成 Mona，17 个保留 SHS（i, ", ` 等）
   实测文本墨宽:
     文本              我们    SHS     Mona
     il                24     28      18
     ll                22     27      16
     Hamburgefonstiv  501    509     494
     minimum          269    280     260
     Illinois         183    190     170
   -> 我们与 SHS 偏差 3~8，Mona 因笔画细而明显更窄。
   -> m_latinmat 的 0.943 缩放产生了正确效果。
```

**注意**: 不要盲目把 advance 也乘 0.943 —— 实测会让与 Mona 的偏差从 8.1 恶化到 39.4。
因为我们的 advance 本就基于 SHS 体系，缩放轮廓已足够。

**GSUB 特性完整性**: ccmp(271 subtables) / liga / calt / locl / aalt / hist
                        / fwid / hwid / pwid / ljmo / tjmo / vjmo / vert / vrt2 全部存在。

### m_metrics 判据（fsSelection 与垂直度量）
```
对比四个字体的垂直度量:
字体    fsSelection  typo          win
SHS     0x0040       [ 880,-120]   [1160,288]
OPPO    0x0040       [ 850,-150]   [1048,271]
HOS     0x0140       [1056,-271]   [1056,271]   (+ WWS)
我们    0x0000  <-    [ 880,-120]   [1160,288]
```

**缺陷 1: fsSelection = 0x0000，缺 REGULAR(bit6=0x40)**
三个参考字体都设了 0x0040。缺此标志可能导致某些应用无法识别常规字重。
-> 已修正为 0x0040（三档统一）。

**缺陷 2（未修）: usWin 未覆盖 4 个竖排功能字形**
```
〱〲  y[-549,1323]   usWin=[-288,1160]   超界 261/163
〪〭  y[-304,-118]                      超界 16
SHS 原版同样超界 -> 上游缺陷
```
**为什么不修**: 提高 usWin 到 [549,1325] 会让行高增加 29.4%，代价过大。
这 4 个字形主要用于竖排场景，横排裁切影响很小。
三个参考字体也都没解决这个问题（SHS/OPPO 用 win 度量、HOS 用 typo 但 typo 也未覆盖）。

### m_nametable 判据（name 表合规与本地化）
```
发现的问题:
1) 无中文名称 -> 中文系统显示英文，不符合中文字体定位
2) nameID 0 版权只写 "© 2014-2025 Adobe"，缺 WDesign 修改声明
   OFL 1.1 要求衍生作品标明已修改
3) nameID 8 Manufacturer 仍是 "Adobe"
4) nameID 11 Vendor URL 仍是 adobe.com/type/
5) nameID 25 (Variations PSNamePrefix) 缺失 — VF 标准要求
6) nameID 5 版本号仍是上游 "Version 2.005"
```

**修复后的 name 表**:
```
Copyright   : Copyright 2026 WDesign. Derived from Noto Sans CJK (...) and
              Mona Sans (...). This derivative uses neither reserved name
              and is licensed under SIL Open Font License 1.1.
Family      : WDesign Sans (en-US + zh-CN)
FullName    : WDesign Sans (en-US + zh-CN)
Version     : Version 1.000
Trademark   : WDesign Sans is a modified version of Noto Sans CJK and Mona Sans
Manufacturer: WDesign
VendorURL   : https://github.com/w-run/wdsans
VFPrefix    : WDesignSans (nameID 25)
```

**OFL 合规要点（重要）**:
- SHS 的 Reserved Font Name 是 **'Source'**，Mona 的是 **'Mona'**
- 我们用的是 'WDesign Sans'，未占用这两个保留名 -> 合规
- OFL 要求衍生作品**标明已修改** -> nameID 0/7 现在都有明确声明
- name 表是唯一随字体文件走的版权信息，必须写对

### ⚠️ VF 构建会丢弃多语言 name 记录（必须后处理）
```
实测:
  masters_MOD18: 31 条 name, langIDs=[0x0, 0x409, 0x804], zh-CN 5 条
  构建后 VF:     49 条 name, langIDs=[0x0, 0x409],        zh-CN 0 条
```
**原因**: varLib 构建 VF 时只保留 master 的 Windows en-US(0x409) 与 Mac(0x0)，
其它语言记录（zh-CN 0x804 等）会被丢弃。

**修复**: 用 `modules/post_vf_name.py` 在 VF 构建后补回:
```bash
python modules/post_vf_name.py /workspace/static/wdsans/WDesignSans-VF.otf
# -> 从 masters_MOD18 复制 zh-CN 的 nameID 1/2/4/16/17
```
**注意**: ID17 (Subfamily) 必须固定为 'Regular'，不能直接复制 master 的
（master 里写的是 ExtraLight，因为它是 250 档）。

**VF 构建后的标准检查清单**:
1. glyphs / cmap 数量
2. fsSelection / 垂直度量（master 改了会被继承，但需确认）
3. **name 表 langIDs（必须在 master 基础上补回 zh-CN）**
4. 预览子集重新生成

### m_os2range 判据（OS/2 字符分类位）
```
问题: 我们补了 143 个 Latin Ext 字符，但 OS/2 ulUnicodeRange 位仍是 SHS 原版的值。
      系统/应用依赖这些位判断字体是否支持某字符范围，位没置就等于「不支持」。

实测缺失 14 个位（最关键的）:
  bit2   Latin Extended-A        125/128
  bit70  Halfwidth And Fullwidth 225/240
  bit3   Latin Extended-B         30/208
  bit6   Combining Diacrit        22/112
  bit33  Letterlike Symbols       17/80
```

**修复**: 按 OpenType 规范定义的码位区间，逐位检查 cmap 是否有字符，有则置位。
三档均新增 **21 个位**:
```
[2,3,4,5,6,9,30,31,32,33,34,35,37,38,40,41,46,47,62,70,86]

验证每个位都有字符支撑:
  bit2   Latin Ext-A      125 字符
  bit40  Enclosed Alphanum 160 字符
  bit41  Box Drawing      128 字符
  bit70  Halfwidth/Full   225 字符
  bit86  CJK Ideograph  20992 字符
```

**同时修正 ulCodePageRange**: 新增 bit50(936 简体中文) / bit52(950 繁体中文)。

**教训**: 字符集扩张后必须重算 OS/2 分类位，否则字形存在但系统认为不支持。

### m_coloncenter 判据（时间场景冒号居中）
```
问题（用户指出）: 横排时间 12:34 的冒号明显偏低。
  实测: zero 中心 +364, colon 中心 +258, 差 -106
  参考: OPPO colon.centered / HOS colon.ss03 都居中（差 -1）
  -> SHS 没修，两家国内厂商都修了

方案: 复制冒号轮廓上移到数字中心 -> 未映射槽位 -> 数字间 calt 替换
```

**效果（HarfBuzz）**: 12:34 -> gid117（居中）；a:b -> gid27（基线）

#### 🔴 三次失败的过程（代价极大，务必避坑）
```
失败1: feaLib 的 addOpenTypeFeaturesFromString **替换整个 GSUB**
  MOD19: 16 features / 52 lookups (ccmp 271, vert 99, vrt2 37...)
  MOD20:  1 feature  /  2 lookups (只剩 calt)
  -> vert/vrt2/ccmp 全丢，预览子集 4.13MB 掉到 1.96MB

失败2: 备份+反向合并 -> 破坏 locl 的 script 映射
  症状: — … 在竖/横排丢 script 特定变体
  原因: GSUB 有 147 个内部 lookup 引用，只追加 lookup 不改引用会错位

失败3: 手写 ot.Coverage() / ot.ChainContextSubst()
  -> 读回来 Coverage Format=None，HarfBuzz 静默跳过，calt 完全不触发
  （注: feaLib 原生编译的 Format 也是 None，所以 Format 不是判断依据）
```

#### ✅ 可行方案：只追加 subtable 到已接线的 calt lookup
```python
# latn 的 calt = feature#68 -> lookup#30（已接线，勿动 FeatureList/ScriptList）
# 1) 隔离编译拿 feaLib 正确生成的 ChainContext subtable
# 2) 把 SingleSubst 追加到 LookupList 末尾
# 3) 把 ChainContext subtable 追加到 lookup#30.SubTable
# 4) 修正 SubstLookupRecord.LookupListIndex 指向新 SingleSubst
```
**关键**: FeatureList / ScriptList 完全不动 -> 所有原有特性零风险。
验证: lookups 52->54, lookup#30 subtable 1->3, 16 种 feature 全部在位。
竖排回归测试： — … 「 与 MOD19 完全一致。

### m_numfeats 判据（数字排版特性）
```
对比四个字体的数字特性:
  SHS    （无）
  我们    （无）  <- 继承 SHS 的空白
  OPPO   tnum pnum frac subs sups sinf numr dnom
  HOS    tnum pnum frac subs sups sinf numr dnom

同时发现字符缺失:
  上标 U+2070-2079: 缺 6 个（⁰⁵⁶⁷⁸⁹）
  下标 U+2080-2089: 全缺 10 个（₀-₉）
```

**已实现: sups / subs / sinf**
```
上下标字形 = 默认数字缩放 62%，上移 34%em / 下移 16%em
特性映射 = SingleSubst 到新字形
cmap 补齐 = U+2070-2079 填 7 个, U+2080-2089 填 10 个
```

**🔴 关键坑: 我们的字体默认数字是等宽的！**
SHS 的 locl 特性（lookup#42, latn script）会把 `zero` 换成 `glyph63166`。
```
默认:      gid63166~63175  adv 全部 521  （等宽）
locl=False: gid17~26        adv 640/363/530... （比例）
```
所以 sups/subs 的 mapping **必须同时覆盖两套 input**:
```python
# 只写 zero -> 上标 是不够的，因为 locl 已把 zero 换了
mapping = {
    'zero': 'sup_zero', 'one': 'sup_one', ...   # 未走 locl 时
    'glyph63166': 'sup_zero', ...               # locl 之后
}
```
> 实测: 只写默认数字时 sups 完全不触发（gid 不变）；
>       扩充后 sups: gid63167(521) -> gid36712(225) ✓

**tnum 是冗余的**（本字体默认已等宽，无需 tnum）。
真正缺的是 **pnum**（比例数字），留给后续。

### m_numfeats2 判据（pnum / numr / dnom）
```
pnum: locl 的 tabular 映射反向 -> 恢复比例数字
      glyph63166~63175 -> zero~nine
      (默认等宽, pnum 开启后变比例)

numr: 默认数字缩放 60% + 上移 33%em
dnom: 默认数字缩放 60% + 下移 10%em
```

**验证（HarfBuzz）**
```
默认 123:  gid63167 adv 521   （等宽，locl 生效）
pnum 123:  gid18    adv 363   （比例，恢复默认数字）
numr 123:  gid61925 adv 217   （分子）
dnom 123:  gid61940 adv 217   （分母）
```

**累计数字特性（MOD23）**: sups / subs / sinf / pnum / numr / dnom 共 6 个
OPPO/HOS 都有 8 个，还差 frac（分数）与 tnum（我们默认已等宽，冗余）

### m_frac 判据（分数特性）
```
机制（3 步 + ChainContext）:
  1) slash -> fraction          (U+2044 分数线)
  2) zero~nine -> *.numr        (分子字形，MOD23 已建)
  3) ChainContext: [fraction] numr' -> dnom
     [dnom] numr' -> dnom       (多位数分数)
```

**验证（HarfBuzz）**
```
frac 1/2:   [(61925,217), (4744,120), (61927,318)]
             分子        分数线      分母
frac 12/34: [(61925,217),(61927,318),(4744,120),(61928,336),(61931,367)]
```

**🔴 同一个 locl 坑（第三次踩到）**
`locl` 先把 zero~nine 换成 glyph6316x，所以:
- lookup 的 input 写 `one` 匹配不上，要写 `glyph63167`
- mapping 必须同时覆盖两套 input
> 第一次: m_numfeats 的 sups（已修）
> 第二次: m_numfeats2 的 numr/dnom（已修）
> 第三次: m_frac 的 numr（已修）
**规律: 任何以数字为 input 的 feature，mapping 都要叠加 locl_tab。**

**数字特性完成度 7/8**: pnum sups subs sinf numr dnom frac
（tnum 冗余 —— 本字体 default 已等宽）

### 笔画风格量化：顶点形态（2026-11-15）

用户指定的 6 项笔画风格指标，已完成 3 项量化，新增第 4 项：

| 指标 | 我们 | OPPO | HOS | 判定 |
|---|---|---|---|---|
| 重心（墨质心） | 0.512 | 0.511 | 0.501 | 达标 |
| 中宫（墨密度） | 46.8% | 44.7% | 46.1% | 达标 |
| 字面宽/高 | 916/903 | 896/910 | 907/902 | 达标 |
| 折角角度（纯L） | 90.0° | 90.0° | 90.0° | **完全一致** |
| 顶点平顶率 | 3~7% | 38% | 40% | 尖角(需重绘) |

> 注: 早期用「所有相邻边夹角」统计得出「折角偏硬」是错误的，
> 详见下方「折角与喇叭口的量化结论」。


#### 顶点平顶率（顶部第一行墨宽 / 峰值墨宽）
```
字体    今 顶宽/峰宽   会 顶宽/峰宽
我们      3/49 = 6%     1/40 = 3%      <- 尖角
OPPO     27/67 = 40%   26/72 = 36%     <- 截平
HOS      30/75 = 40%   30/78 = 38%     <- 截平
```

#### 🔴 为什么「移动端点」做不出平顶（已证伪，勿重试）
```
HOS 今 = 1 个连通轮廓 7 点:
  p1 (464,839) -> p2 (540,839)    平顶宽 76

我们 今 = 2 个独立轮廓 各 5 点:
  轮廓2 p0 (529,805)   右笔顶点
  轮廓3 p1 (497,845)   左笔顶点

两笔在顶部不连通 -> 无论怎么移动端点，永远是两个尖角。
要实现平顶必须**合并两个轮廓**（改拓扑 + 改点数）。
```

**m_apexflat 尝试记录（已回滚）**:
```
做法: 把两个轮廓的顶部端点各自向外平移 (target_d - d)/2
结果: 三档一致（264/264/264）但视觉效果无效
  今 顶部第一行墨宽: 改前 3px -> 改后 2px（更尖了）
  因为端点外移只让轮廓变宽，顶点仍然是尖的
```

**当时的坑（记录备查）**:
1. `target_w = 0.72 × SW` 太小，250 档只有 21.6 -> 27 字被误判「已有平顶」跳过
   -> 平顶宽度应用**绝对值**（400 档实测 78，约等于 SW 的 1.0 倍）
2. `ymax 差 ≤ 30` 太严，「人」形撇比捺天然高 30~45
   -> 用 50 才能覆盖常用字（今=39 会=39 全=30）
3. 轮廓点索引体系: p0 = start, pK = segs[K-1] 的终点
   -> 整轮廓平移会让 p0/p1 同步动，间距不变

#### 结论与后续方向
```
顶点平顶是真实风格差异，但需要轮廓合并（拓扑重构），
属于「重绘」级别改动，不是参数调整能做到的。
优先级低于其它可参数化的差异（如折角钝化）。
```

### m_curvflat 判据（长曲线曲率压平）

用户指定的 6 项笔画风格指标中，「撇捺曲率」本轮量化并修复。

#### 量化方法（fontTools 官方 API，非手写）
```python
from fontTools.misc import bezierTools
bezierTools.splitCubicAtT(p0,p1,p2,p3, t)    # 精确采样
bezierTools.splitQuadraticAtT(p0,p1,p2, t)

指标 = 最大偏离弦距离（em 单位）
  对曲线采样 10 点，算每个点到「端点连线」的垂直距离取最大值
```

#### 实测差距（3.5 倍）
```
长曲线（chord >= 300）最大偏离:
  字体    中位   均值    P75     P90
  我们    66.8   68.0   108.8   136.9   em
  OPPO    19.2   18.7    23.5    25.7
  HOS     17.1   23.4    31.6    50.2

曲率<0.995 的「真弯」长曲线占比:
  我们 127/167 = 76.0%
  OPPO   67/378 = 17.7%
  HOS    55/302 = 18.2%
```

#### 修法（只改控制点，不改段数/操作符 -> 三档天然一致）
```python
# 把 P1/P2 沿「端点→控制点」方向缩 k
# 偏离与 k 近似线性 -> k = target_dev / dev_original（解析法，非二分）
Q1 = A + (P1 - A) * k
Q2 = B + (P2 - B) * k
# 端点 A/B 完全不动 -> 字形骨架不变，只减小鼓出量
```

**🔴 性能坑: 不要用二分搜索**
```
二分 24 次 x 每字 N 条曲线 x 20,992 字 = 数百万次贝塞尔分割
实测 >4 分钟仍在检测阶段（2.4 分钟时仍未输出）

解析法: k = target/dev，校验一次即可（偏离的二次项很小）
实测检测阶段 4 分钟内完成，总耗时约 5 分钟
```

#### 效果验证
```
字体      中位偏离   均值     P90
改前       66.8     67.9    136.3
改后       20.0     17.6     20.2     <- 精确命中目标
OPPO       19.2     18.7     25.7
HOS        17.1     23.4     50.2
```

**规模**: 14,825 字 / 53,142 条曲线（CJK 的 70%），三档全一致跳过 0
**门禁**: G1 零长度段 0 / G2 包围盒漂移 0 / G3 三档不一致 0 → 全通过

**目标偏离按字重缩放**: 250档 8 em / 400档 20 em / 900档 39 em
（与 SW 比例一致: 30:77:150 ≈ 8:20:39）

> 6 项总表见下方「笔画风格量化最终结论」。


### 🔴 折角与喇叭口的量化结论（2026-11-15，重要纠错）

#### 1. 折角：纯几何直角三家完全一致，此前判断有误

早期用「所有相邻边夹角」统计，得到我们 91.9° / OPPO 98.4° / HOS 93.5°，
误判为「折角偏硬」。**严格区分段类型后结论反转**：

```
只统计两侧都是 L 段的折角（真实几何直角）:
  字体    n     中位    均值    >100°占比
  我们   556   90.0    90.0     0.0%
  OPPO   408   90.0    90.0     0.0%
  HOS    464   90.0    90.0     0.0%
```

**此前 91.9° vs 98.4° 的差距全部来自曲线轮廓**
（把贝塞尔控制点当顶点算角度会得到 120~180° 的假角）。
-> **折角不是差异项，不需要修改。**

#### 2. 喇叭口：不存在（三家都是均匀笔画）

位图实测笔画宽度剖面:
```
「丨」单独竖笔（800pt 字号）:
  我们 48px 恒定    OPPO 46px 恒定    HOS 55px 恒定

「十」横笔:
  我们 47px 恒定    OPPO 43px 恒定    HOS 51px 恒定

横笔端面斜切:
  我们/OPPO/HOS 全部 +0.0 px（精确垂直）
```
**中文黑体的「喇叭口」不是靠笔画粗细变化实现的，三家都没有。**
（m_termface 模块已把所有端面拉直，端面斜切实测 = 0px）

#### 3. m_cornercut 失败记录（已回滚，勿重试）
```
做法: 把纯 L 轮廓的 90° 顶点拆成 2 点做倒角（cut = 0.35×SW）
命中: 15,539 字 / 121,736 个折角

结果（400 档）:
  字体    中位    均值    >100°占比
  改前    90.0    93.1     10.9%
  改后    90.0   108.9     45.3%    <- 过头了
  OPPO    90.0   100.6     18.3%

逐字验证暴露方向错误:
  口  90.0 -> 129.4  (OPPO/HOS 都是 90.0)
  回  90.0 -> 126.6  (OPPO/HOS 都是 90.0)
  十  90.0 -> 112.5  (OPPO/HOS 都是 90.0)
  今  89.4 -> 89.4   (该改的没改)
  朋  96.4 -> 96.4   (该改的没改)
```
**教训: 动手前必须先逐字验证「对照组」，不能只看聚合统计。**
口/回/十 是天然对照组（三家都是精确直角），它们被改坏就直接说明方向错了。

#### 笔画风格量化最终结论（6 项）
```
指标          我们      OPPO     HOS      状态
重心          0.512    0.511    0.501    达标
中宫          46.8%    44.7%    46.1%    达标
比例(宽/高)   916/903  896/910  907/902  达标
撇捺曲率      20.0     19.2     17.1     达标 (MOD26)
折角          90.0°    90.0°    90.0°    无差异
喇叭口/切角   均匀     均匀     均匀     无差异
顶点平顶率    3~7%     38%      40%      唯一剩余差异
```

**6 项中 5 项已达标或确认无差异，唯一剩余是顶点平顶**
（需合并轮廓 = 拓扑重构，属重绘级别）。

### 🔬 m_apexmerge 技术验证（2026-11-15，方向对但 VF 不兼容）

用专业图形库（skia-pathops 0.9.2）尝试合并「人」形两笔做平顶。

#### ✅ 视觉效果完全达成
```
pathops.simplify(轮廓自并集) 后:
  轮廓数 5 -> 3（与 HOS 的 3 个一致）
  顶端从单尖点变为两个同高点 -> 真平顶

顶部墨宽/峰宽:
        改前          改后          OPPO    HOS
  今     2/76 = 3%    63/88 = 72%   59%     59%
  合     2/69 = 3%    64/76 = 84%   59%     60%

顶宽绝对值（em）:
  改前 2   改后 80   OPPO 69   HOS 76
  (目标 78 实现为 80，误差 2.5%)
```

#### 🔴 硬阻塞：simplify 在三档产生不同拓扑，VF 无法插值
```
同一字形 uni5F29 的 simplify 结果:
  250: 5 轮廓  签名 LCLCCCLCLCLLCLLLLL|...
  400: 6 轮廓  签名 LCLCLCCCLCLCLLCLLLLL|...
  900: 4 轮廓  签名 LCLCLLLCLCCLCCLLCCLCCLLLLLLCCCCL|...

全库统计（4,900 字三档都能切平）:
  签名不一致: 4,888 字（99.7%）
```
**原因**: 布尔运算的交点位置随笔画粗细变化，
不同字重会切出不同数量的边与不同的段型组合。
这是 skia-pathops 的本质行为，无法通过调参解决。

#### 尝试过的缓解方案（均失败）
```
1. 三档预筛（任一档失败则整字跳过）
   -> 仍有 99.7% 签名不一致
2. 只要求顶点两侧是 L 段（放宽判据）
   -> 覆盖率从 1 字提升到 5,835 字，但不解决签名问题
3. 目标宽度按字重缩放（39/72/130）
   -> 宽度对齐了，签名仍不一致
```

#### 结论
```
视觉方案正确且已验证，但**与可变字体插值不兼容**。
除非改为「单档 VF + 不插值」或「三档各自独立字体」，
否则顶点平顶无法在 VF 架构下实现。

这是 6 项笔画风格指标中唯一未达成项，且是架构级限制。
```

#### 可复用的技术资产
```python
import pathops
p = pathops.Path(); glyphset[gn].draw(p.getPen())
p2 = pathops.simplify(p, fix_winding=True)   # 自并集，消除重叠
rp = RecordingPen(); p2.draw(rp)
contours = contours_from_pen(rp.value)
```
**注意 API 坑**: `pathops.union([p], outpen, ...)` 的 outpen 需要 pen 对象，
传 Path 会报 `moveTo() takes exactly 2 positional arguments`。
用 `pathops.simplify(path)` 返回新 Path 最简。

### m_ledge 判据（顶部横笔右端延伸 = 横折出头）

AGENTS.md 第 7 节「横折出头（厶/廴 结构）」的第一个可解子问题。

#### 量化发现（fontTools 精确点位 + 位图交叉验证）

顶部横笔的**右端余量**（字形右界 − 横笔右端）:
```
字    我们    OPPO    HOS
各    171     121     0
冬    180     135     0
条    206     122     0
备    191     122     0
务    126     126     0
```
-> 我们的顶部横笔右端收得太紧，比 OPPO 多 50~85 em，比 HOS 多 126~206 em
-> 视觉上就是「横折不出头」

位图交叉验证（顶部横笔墨宽 / 字面宽）:
```
        我们    OPPO    HOS
各      0.601   0.672   0.686
冬      0.571   0.656   0.667
条      0.578   0.680   0.696
备      0.598   0.681   0.686
均值    0.602   0.674   0.685   -> 我们短 11%
```

#### 修法（只改 2 个点的 x，三档天然一致）
```python
# 找顶部横笔: 4 点纯 L、宽/高 >= 3.5、ymax >= 字形顶 - 150
x_target = 字形右界 - TARGET_MARGIN[tag]
# 把横笔「x 最大的 2 个点」平移到 x_target
# 段数、操作符完全不变 -> 无 VF 插值风险
```
**目标右余量 v1**（按字重缩放）: 250档 35 / 400档 90 / 900档 175（v2 已调整为 35/90/110）

#### 效果验证 v1（400 档）
```
字    改前(宽/右余)   改后(宽/右余)   OPPO        HOS
各    507/171      588/90       786/121     925/0
条    439/207      556/90       777/122     912/0
```
右余精确命中 90，落在 OPPO(121~126) 与 HOS(0) 之间。

**规模**: 1,182 字，三档全一致，签名不一致 **0 字**
**门禁**: G1 0 / G2 0 / G3 0 → 全通过

#### 为什么这个模块能成功（与 m_apexmerge 对比）
```
m_apexmerge: 用 pathops 布尔运算改拓扑 -> 三档切出不同结构 -> 失败
m_ledge:     纯点坐标平移，不动段数/操作符 -> 三档必然一致 -> 成功

教训: CJK 结构问题优先用「只移动已有点」的方式解决，
      任何改变段数/点数的方案（布尔运算、拆点、合并轮廓）
      在多档 VF 下都会因阈值差异产生结构分歧。
```

#### 判据放宽（v2, MOD30）

首版（MOD29）只覆盖 1,182 字，冬/备/务 等字被漏掉。逐档排查发现:
```
备 250: c0 w=460 h=30  → 命中
备 400: c0 w=453 h=67  → 命中
备 900: c0 h=127 w/h=3.5  ← 卡在边界（浮点比较失败）

冬 900: c1 h=124 w/h=3.3  ← 明确不达标（阈值 3.5）
务 900: c3 h=120 右余=139，目标 175 > 139 → 反而不需延伸
```
**根因: 粗字重下笔画变厚，h 增大导致 w/h 自然下降。**

修正:
```python
MIN_RATIO: 3.5 -> 2.8        # 900档横笔 h 可达 127，比例降至 3.3
TARGET_MARGIN['900']: 175 -> 110   # 900档右余本来就小(139)，175 会反向收窄
```

**效果（400 档）**:
```
字    改前(宽/右余)   改后(宽/右余)
冬    430/179      519/90
备    453/191      554/90
务    513/124      547/90
各    507/171      588/90
条    439/207      556/90
```
覆盖 1,182 -> **2,636 字**，三档全一致，签名不一致 **0 字**，门禁全通过。

#### 注意: 仍有一部分字未覆盖
```
夏 麦 玫 玖 等字未命中 —— 它们的顶部横笔不是「4点纯L」轮廓
（可能是 C-L-C 或含曲线），属于另一种「横折出头」形态，需另立判据。
第 7 节仍保留该条。
```

### 🔵 用户裁定：包围结构字面宽度差异属风格，不调整

量化发现的差异（2026-11-15）:
```
包围结构字（口田回同明四困团圆等 26 字）:
  宽 +3.0%（中位 +2.4%）
  高 −1.1%（中位 −0.9%）

最显著:
  口  750 vs 704  w+6.5% h-4.0%
  田  810 vs 748  w+8.3% h-0.9%
  回  837 vs 782  w+7.0% h+1.0%
  困  835 vs 782  w+6.8% h-0.3%
  四  822 vs 773  w+6.3% h-6.5%
```
2000 字大样本整体（宽/高）:
```
  我们 914/910   OPPO 893/914   HOS 905/907
  -> 整体只差 1~2%，只有包围结构这一类偏宽
```

**用户裁定（2026-11-15）**: 「这个不用调整、风格不同」
-> 包围结构的字面比例是设计选择，不是缺陷。**不要修改。**
-> 已记录的量化数据保留备查，但不再作为待办项。

#### 同理确认无需修改的字（`夏麦玫玖`）
```
夏  顶横笔 340/372=0.914  vs OPPO 0.969 / HOS 0.989  差 8px（绝对宽）
麦  321/366=0.877          vs 0.885 / 0.897          差 6px
玫  217/375=0.579          vs 0.962 / 0.968          差 138px
玖  308/373=0.826          vs 0.825 / 0.830          一致
```
**`玫` 的 0.579 是测量假象**: 逐行剖面显示前 39 行与 OPPO 完全一致，
差异来自「王」部件顶部横笔位置不同导致的顶部 18% 窗口取样偏差。
`夏` 的横笔右余 44 已小于目标 90（更靠右），不需要延伸。
-> 这 4 字不属于 m_ledge 可解范围，也不构成缺陷。

### 🔴🔴 重大事故修复：曲线全部丢失（2026-11-15）

**用户反馈**: 「汉字字体所有曲线怎么都没了？」

#### 实测确认
```
                曲线占比   永的段型
SHS 原始        42.3%      LCLC / LLLCCCL / LCCCCLCCLLLLLCCCCC
线上(事故版)     32.7%      LCLC / LCLC / LLLCCLCC / LCLC / LCLC   <- 全变直线
```

#### 两个罪魁祸首

**1. `m_termface` (MOD2): C→L，全局砍掉 8% 曲线**
```
阶段      曲线%
shs      38.2%
MOD      38.0%
MOD2     30.0%   <<< m_termface 突变 -8.0%
```
判据「段长 ∈ [0.8,1.5]×SW 且弯曲比 < 0.10」实际命中范围远超「笔端面」，
把大量真实弧线也拉直了。

**2. `m_latinext` (MOD6): 硬编码路径导致覆盖 CJK**
```python
# ❌ 错误: 读死 MOD12 的槽位，与实际基座不符
F = '/workspace/wdsans2/build/masters_MOD12/master-Regular-400.otf'
BASE = os.environ.get('WDS_BASE', ...)   # 不认 WDS_SRC

# ✅ 修复
F = os.environ.get('WDS_SRC', ...) + '/master-Regular-400.otf'
BASE = os.environ.get('WDS_SRC') or os.environ.get('WDS_BASE', ...)
```
后果: 复用的「未映射槽位」在 R5 中已被 CJK 占用 → 直接覆盖 CJK 字形。

#### 修复方案：从 MOD 重建整条链，跳过 termface

**用户决定**: 「不要改曲线、之前的曲线就够」
-> 保留 SHS 原始曲线，**放弃 m_termface / m_termface_v2**（端面拉直）
-> 放弃 m_taper_v2（依赖 termface 的 C→L 后才能命中）

新链（masters_R1..R16）:
```
R1  = MOD  + shortl      3,373 字
R2  = R1   + zerocont      45 字
R3  = R2   (yanrad 0 命中，跳过)
R4  = R3   + bardiag    3,074 字
R5  = R4   + latinmat     371 字形
R6  = R5   + latinext     143 字符
R7  = R6   + kerning   77,294 对
R8  = R7   + markpos      22×442
R9  = R8   + metrics     fsSelection 0x0040
R10 = R9   + nametable     31 条 name
R11 = R10  + os2range      21 位
R12 = R11  + coloncenter    2 字符
R13 = R12  + numfeats      20 字形
R14 = R13  + numfeats2     20 字形
R15 = R14  + frac           3 档
R16 = R15  + ledge      2,636 字
```

**效果**：
```
曲线 32.7% -> 42.6%（SHS 42.3%）
永: LCCC / LLLCCCCC / LLCCC  <- 曲线回来了
VF 40.4MB -> 41.3MB（+0.9MB 正是曲线数据）
门禁 G1/G2/G3 全通过
特性 23 种、fsSelection 0x0040、name 31 条、cmap 45,012
```

#### 关键教训
```
1. 任何「C→L」类模块（termface）必须先在样本字上逐字验证，
   不能只看命中数量。8% 的全局曲线损失 = 视觉可察觉的「变方」。

2. 复用「未映射槽位」的模块必须从**当前基座**读槽位表，
   硬编码历史目录会导致槽位与实际占用冲突 -> 覆盖真实字形。
   所有模块应统一用 WDS_SRC / WDS_BASE 环境变量。

3. 事故前建议做「曲线占比」作为门禁指标：
   全库 C/Q/QM 段占比相对 SHS 的偏差不应超过 2%。
```

### 🔴 拉丁宽度与预览子集修复（2026-11-15）

**用户反馈**: 「拉丁字体怎么窄了这么多？恢复原宽」「和MonaSans比宽了很多啊」
「字体特征那些我在预览页面上完全没有看到效果」「数字9比其他的字形要细一些」

#### 问题 1: 拉丁轮廓被 m_latinmat 压窄 5.7%
```
实测墨宽（400 档）:
  字   我们      Mona@400   墨宽比
  H    550       583        0.944
  A    597       636        0.939
  M    687       728        0.943
  W    858       910        0.943
  n    412       435        0.947
  0    453       483        0.937

所有拉丁字形都只剩 Mona 原宽的 94.3%（= m_latinmat SCALE=0.943）
但 advance 却是 Mona 原值（H=764 A=697 M=894 W=994）
-> 字形变窄 + 字距相对变宽 -> 混排显得松散
```

**m_latinmat 的历史误判**:
```
它的理由是「拉丁竖干比 CJK 粗 5.7%」，但那是对 **SHS 拉丁** 的测量。
实际常用拉丁 46/62 字已从 Mona 注入，Mona 字形本身就协调，不该再压窄。

旁证: advance 早已是 Mona@400 的值，说明当初就没打算改字形间距，
只改轮廓 = 半途而废。
```

**修复**: `m_latinreset` 对所有拉丁轮廓做 1/0.943 = 1.0604 反向横向缩放（绕中心）。
```
效果: H 550->583 (Mona 583, 比 1.000)
      A 597->635 (Mona 636, 比 0.999)
      W 858->910 (Mona 910, 比 1.000)
486 个拉丁字形，三档全一致
```

#### 问题 2: 预览子集裁掉了所有特性目标字形
```
fontTools 的 populate(text=...) 只保留文本里出现的字符，
不会自动保留 GSUB 引用的目标字形。

实测: sups 目标10个 -> 子集里0个
      subs/sinf/numr/dnom 各自 10个 -> 全部0个
      frac 目标11个 -> 0个
      pnum 10个 -> 10个 OK（目标就是普通数字，本身在文本里）

-> 预览页上这些特性完全没效果（GSUB 定义了但目标字形不存在）
```

**修复**（`probe/make_subset.py`）:
```python
# 1) 收集 WANT = {sups,subs,sinf,numr,dnom,frac,pnum,calt,liga,dlig} 的 lookup 目标
# 2) 展开 ChainContext 的 SubstLookupRecord 内部引用
# 3) 🔴 排除 lookup#30: SHS 自带谚文 calt，带 2.4 万 CJK/谚文目标
#    否则子集会膨胀到 20k 字形 / 0.05MB 全是空壳
#    只取它的冒号相关 subtable（InputCoverage 含 colon/semicolon）
# 4) 过滤掉无轮廓的空壳槽位
```
结果: 7,600 字形 / 4.23MB，GSUB 指向缺失字形 **0 条**

#### 问题 3: 「数字 9 偏细」的核查结论
```
笔画厚度实测（位图，中部最细段）:
  字   我们    OPPO    HOS
  9    34.0    34.0    40.0    <- 与 OPPO 完全一致
  中位 37.5    34.5    39.0
  极差 16.0     6.0     9.0    <- 我们极差大，因为数字 2 = 50.0

墨宽（400 档）: 我们 458 vs SHS 457 -> 一致
```
**数字 9 正常，真正偏粗的是数字 2（厚度 50.0 vs 中位 37.5）。**
同排对比时 2 偏粗 → 9 显得细。

数字 2 的结构原因（SHS 原始数据）:
```
我们/ MOD: CCCCCCCCLCCCCCCCCCCCCLLLLLCCC  (28 段)
SHS:       LLLCCCCLCCC                      (9 段)
```
SHS 原版就过度细分成 28 段曲线，非本项目引入。**保持原样不改。**

### 🔴 数字排版特性在中文环境失效（2026-11-16）

**用户反馈**: 「冒号特性啥的没有、看看原字体呢」（截图显示 sups 与默认数字相同）

#### 根因：7 个特性只注册在 DFLT，中文 LangSys 里完全没有
```
hani(中文) 的 LangSys 分布:
  DFLT : aalt calt ccmp dlig dnom frac fwid hist hwid liga numr pnum pwid ruby sinf subs sups vert vrt2
  ZHS  : aalt calt ccmp dlig fwid hist hwid liga locl pwid ruby vert vrt2
         ^^^^ 只有 13 个，缺 sups/subs/sinf/numr/dnom/pnum/frac

关键规则: 某脚本一旦存在 LangSysRecord(ZHS/ZHH/ZHT/JAN/KOR)，
          HarfBuzz/Chrome 就不再回退到 DefaultLangSys。
          -> 中文环境下这 7 个特性完全失效
```

**实测对比**:
```
lang=en  (无 LangSysRecord) -> sups 123 = gid43272(241)  生效
lang=zh-hans (ZHS)          -> sups 123 = gid18(390)     不生效
```

**修复 `m_featlang`**: 把这 7 个 FeatureRecord 索引追加到每个 LangSys 的 FeatureIndex。
只改 ScriptList，不动 FeatureList/LookupList -> 零风险。三档各新增 210 处指向。
```
效果（lang=zh-hans）:
  sups 123 -> gid43272(241) gid61877(337) gid61878(353)  ✓
  subs 123 -> gid61910(241) gid61911(337) gid61914(353)  ✓
  frac 1/2 -> gid61927(234) gid3265(128) gid61928(326)   ✓
```

**浏览器实测（headless Chrome 截图测墨量）**:
```
  默认  高43 宽310 墨4338
  sups 高27 宽189 墨1538   <- 生效
  subs 高26 宽189 墨1596   <- 生效
  frac 高44 宽 37          <- 生效
```

#### 冒号居中其实一直是好的（重要纠错）
```
  colon         y[-14,529] 中心=258
  glyph03346    y[ 92,635] 中心=364   <- calt 替换目标
  zero          y[-11,738] 中心=364   <- 数字中心
  one           y[  0,730] 中心=365

12:34 输出 gid3346 = glyph03346 = 居中冒号，与数字中心完全一致。
之前误判为「未生效」，是因为把 gid3346 当成了普通 colon(gid27)。
```

#### ❌ 已否决: m_digitmono / m_pnumfix（中文数字强制等宽）
```
动机: SHS 的 locl 只在 latn-DFLT 注册数字等宽映射 lookup#42;
      指定语言后数字变回比例宽。看起来像 bug。

但三家实测:
  OPPO  adv=[620,383,548,558,616,585,598,540,589,596]  比例
  HOS   adv=[570,570,...] 全相同                      等宽
  SHS   adv=[555,555,...] 全相同                      等宽

两家参考厂商本身不一致 -> 保持 SHS 原行为即可。

更关键的硬阻塞: locl 与 pnum 在同一次 GSUB 传递中互相抵消
  locl:  one -> glyph63167
  pnum:  glyph63167 -> one      <- 又变回原样
  实测 pnum + locl关 = gid18(390) 生效；pnum + locl开 = gid63167(555) 无效
除非新建独立的「比例数字」字形（占 10 个槽位），否则 pnum 无法与 locl 共存。
-> 放弃该方向，保持 SHS 原设计。
```

### 🔴 回归修复：重建链漏掉 m_curvflat（2026-11-16）

重建曲线事故链时（MOD -> R1..R19）只跑了 MOD 之后的模块，
**漏掉了原本在 MOD26 的 `m_curvflat`（撇捺曲率压平）**。
R19 上线后实测发现曲率指标回退到了比 SHS 还差的水平。

#### 实测对比（长曲线 chord>=300 最大偏离 em）
```
                中位    均值    P90
R19(漏 curvflat) 21.9   31.6    74.0   <- P90 远超参考
R22(补上)        19.8   15.4    20.1   <- 达标
SHS 原始         18.7   23.7    52.0
OPPO              7.5    8.7    16.6
HOS               7.8   10.1    22.3
```
**P90 从 74.0 降到 20.1，进入 HOS 区间。**

#### 门禁
```
G1 零长度段新增: 0 字 PASS
G2 包围盒漂移>46: 0 字 PASS
G3 三档不一致:   0 字 PASS
```

#### 教训
```
重建链时必须对照「原链已部署模块清单」逐项核对，
不能只凭记忆挑模块。本次遗漏的是纯几何模块（不改拓扑），
所以三档一致性与构建都不会报错，只能靠指标测量发现。

建议: 每次重建链后，跑一遍全部量化指标（6 项笔画风格）做回归。
```

### ✅ 6 项笔画风格回归套件（2026-11-16）

**每次重建链、每次部署前必须跑一遍。** 纯几何模块的遗漏不会触发门禁报错，
只能靠指标测量发现（m_curvflat 遗漏事件就是这么漏过去的）。

```bash
cd /workspace/wdsans2
python modules/regress.py     # 约 5 分钟，对比 我们/SHS/OPPO/HOS
```

#### 输出（2026-11-16 R22 实测，全部达标）
```
字体   比例W/H    中宫%   重心    曲率中位/P90   折角°
我们   915/911   42.9   0.499   19.8/20.1   90.0
SHS   915/912   40.5   0.479   18.7/52.0   90.0
OPPO  894/914   42.1   0.497    7.5/16.6   90.0
HOS   906/908   42.4   0.476    7.8/22.3   90.0
```

#### 判定标准
```
比例     宽/高与 SHS 或 HOS 同档（±15）
中宫     在 OPPO(42.1) 与 HOS(42.4) 之间
重心     0.497~0.499（OPPO 0.497）
曲率     中位 ≤20，P90 ≤25（HOS P90=22.3）
折角     与三家同为 90.0°（无差异项）
```

#### 实现要点
```python
# 折角统计容易写错索引: pts[0]=起点, pts[k]=第 k 段终点
# 段 i 的起点=pts[i] 终点=pts[i+1]
# 前一段 (i-1) 的起点=pts[i-1] 终点=pts[i]
# 只统计「前后段都是 L」的折角，曲线控制点当顶点会算出 120~180° 假角
```

### m_barple 参数（用户确认 RATIO=0）
```
1. bar 右端 → xR                    横线右对齐到撇右界
2. body 倒数第2段终点 → (xR, bar.bottom)   落点下移到横线右下角
3. 删除回折段
（不做根部收窄 —— E3 验证确认 ratio=0 效果最佳）
```

验证字：永 今 亨 夕 多 了 互 乳 亂 延 各（11/11 改善，0 副作用）

---

## 3. 踩坑清单（**必读，每条都付过代价**）

### 3.1 结构识别
1. **落点取倒数第 2 段终点**，不是末段。
   末段是「回折段」（绕回起点），取其终点会让 `dx/dy` 全超范围 → 整字漏检。
   > 实测：`永` 用末段算出 dx=3、dy=73（全超），用倒数第2段 dx=52、dy=52（命中）。

2. **左边界 `j` 必须排除末段，且取最短者**。
   否则被回折段覆盖 → `cap` 变负 → 补偿完全失效。
   > 实测：`永` 的 j 被循环末尾覆盖成 seg5，cap = (329-392)×0.85 = -53.5。

3. **容差按横线高度，不按 SW**。
   `0.25×SW` 在 250 档（SW=30）只有 7.5，过严。
   用 `max(0.25×SW, 0.40×横线高)`。

### 3.2 修改动作
4. **不要移动主边终点** —— 会拉细笔画。
   > 实测：`了` 字移动主边终点后竖弯钩明显变细。只做横线对齐 + 落点下移。
5. **不要对短边做「根部收窄」** —— 试过 25%/30%/35%/60%/85%，全部不如 ratio=0。
6. **删除段必须真删，不能退化成零长度** —— varLib 会静默丢弃零长度段，导致三档段数不一致。

### 3.2b 模块间依赖（m_taper 必须在 termface 之后跑）
7b. **`m_taper` 的判据要求「前段 C + 本段 L」，但 SHS 原始撇捺末端是 C 段**
    → 在 T6 时期 taper 几乎命中不到；必须先跑 `m_termface`（C→L）才有目标。
    → 2026-11-15 在 MOD8 上重跑 taper，命中 17,405 字 / 56,839 段（T6 时期几乎为 0）。

7c. **`m_taper` 的索引必须是完整 `(ci, k, j)` 三元组，且只能 400 档检测**
    `find()` 返回 `(ci, k, j)`：ci=轮廓，k=端面段，j=相邻曲线段；
    `apply()` 三者都要用（j 的控制点要向中点拉 C2PULL）。
    > 实测错误: 只存 [ci,k] 丢 j → apply 静默无效，只应用 56 字。
    > 实测错误: 三档各自 `T.find(C, SW[tag])` → 900 档 SW=150 使段长判据变成 [82.5,217.5]，
    >           漏掉 5,582 字，三档实际改动 17380/17405/11823 严重不一致。

7d. **`m_taper` 不可重复运行 —— 判据不收敛**
    判据用段长 `[0.55,1.45]×SW`；而 NARROW=0.95 只让端点各向中点收 5%，
    段长 84.0 → 79.8，仍在判据范围内 → 每次运行都会继续削细 1.5~2 单位。
    > 实测: 连续 apply 两次，第二次仍命中同样位置（人 1处 / 入 3处 / 八 2处）。
    > 约束: `m_taper` 在一条基座链上**只能跑一次**。若需重跑，必须从该模块之前的基座重新开始。

### 3.3 工作方法
7. **基座必须是原始状态**。用已改过的文件当基座推导判据，会让判据只在「已修」状态成立。
   > 实测：拿 T7（`永` 已改）当基座，判据 `|E.x − bar.right| ≤ 0.15SW` 对原版 `永`（dx=52）完全不成立。
8. **截图窗口必须先确认覆盖目标区域**。凭猜裁剪 → 看到空白或错误局部 → 误判。
   先 `--grid` 渲染整字定位，再裁剪。
9. **缩略图不可用于判断**。必须放大到 ≥600px 宽并看结构化数据。
10. **不要凭「看起来像」下结论**。先用 `glyphview.py` 精确渲染 + 数值测量。

### 3.4 用户沟通
11. **「看不出差异」时先检查自己的渲染/裁剪是否正确**，而不是断言无差异。
12. **不确定就问**。猜错方向的代价远大于问一句。
    > 本会话曾连续 5 轮改错边（S 右移 / Pend 下移 / 端面收缩 / 删台阶 / 闭合缺口），全部因为没确认。

---

## 4. 字体机制事实

- SHS 2.005：CFF2，upm 1000，**65,535 字形（硬上限）**，cmap 44,853，CJK 20,992
- CFF 段格式：`['L',(x,y)]` / `['C',c1,c2,end]` / `['Q',ctrl,end]` / `['QM',[pts...]]`
- 写入：`csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)`
- 保存前必须：`post.formatType=3.0`、`post.glyphOrder=None`
- OPPO 用二次曲线（Q/QM），SHS 用三次（C）—— **不可直接比较坐标**
- 可变字体构建约 **312 秒**，RSS ~1.7GB

---

## 5. 长任务与部署

```bash
# 长任务（VF 构建、全库扫描）
setsid nohup <cmd> > /tmp/x.log 2>&1 < /dev/null &
# 轮询间隔 250~320 秒
```

```bash
# VF 构建
python /tmp/bvf_mod.py     # designspace -> /workspace/static/wdsans/WDesignSans-VF.otf
# 更新预览子集
python probe/make_subset.py <VF> /workspace/static/wdsans/wd-preview.woff2
# 验证
curl -s -o /dev/null -w "%{http_code} %{size_download}\n" http://127.0.0.1:8020/wdsans/WDesignSans-VF.otf
```

---

## 6. 文件同步

本地开发 → `ssh_upload` 上传。**不要用 base64 管道写文件**（会静默失败，文件不更新）。

```js
await tools.ssh_upload({ alias: 'w-box',
  localPath: 'D:\\Project\\WDesign\\wdsans-modules\\m_x.py',
  remotePath: '/workspace/wdsans2/modules/m_x.py' });
```

---

## 7. 未解决问题（待攻）

| 类 | 代表字 | 状态 |
|---|---|---|
| 顶点平顶（人字形） | 今 合 会 含 令 | 风格差异，用户已接受；技术上需拓扑重构且与 VF 不兼容 |
| 横折出头（厶/廴 结构） | 丝 延 各 | 顶部横笔已解决（m_ledge 2,636字）；其余形态待攻 |
| 永字左下 7 形拐角 | 永 | 待分析 |
| 纟旁拐角 | 丝 红 | 待分析 |
| 建字左侧部首 | 建 | 待分析 |
| 多字拐角 | 多 | 待分析 |
