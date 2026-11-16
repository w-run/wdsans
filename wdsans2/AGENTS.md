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
masters_R22 = R19  + curvflat   14,878字/54,419曲线
masters_R23 = R22  + punctscale  5个句读标点（curvflat 有害，已废弃）
masters_R24a = R16 + punctscale  （去掉 curvflat，标点缩小）
masters_R25 = R24a + featlang
masters_R25b = R25 + latinreset  486字形宽恢复 已部署 ← 当前链尾
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

### 字形比例（最新值见 regress.py）
```
指标        我们    OPPO    HOS
比例 W/H   915/911 894/914 906/908
中宫%       43.2    42.1    42.4
重心       0.499   0.497   0.476
```
测量: bbox 均值 / PIL 渲染 400px 墨迹质心 / AreaPen 墨面积比。
字面率异常: 20,992 字中宽或高 >1000 的 0 个，宽高均 <420 的 0 个。

### 拉丁完整性
A 纵向对齐 y[0,729] = Mona y[0,729]；Ẁ 宽 953 与 W 一致（正常）。
字形 GSUB: ccmp/liga/calt/locl/aalt/hist/fwid/hwid/pwid/ljmo/tjmo/vjmo/vert/vrt2 全部存在。

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

### 6 项笔画风格指标
见下方回归套件与各专项章节。

### ❌ 已废弃: m_curvflat
**不要使用。** OPPO/HOS 只有 350 条长曲线，我们有 2853 条；
该指标对参考字体不适用。强行压平使撇捺展开 0.531 -> 0.616~0.629（参考 0.531）。
详见「重要纠错：m_curvflat 有害」。

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
把纯 L 的 90° 顶点拆 2 点做倒角（cut=0.35×SW），命中 15,539 字。
改后 >100° 占比 10.9% -> 45.3%（OPPO 18.3%），过头。
对照字 口/回/十 被改成 129°/127°/113°（OPPO/HOS 都是 90°）——
**对照组被改坏就说明方向错了，动手前必须先验证对照组。**

### ⚠️ 顶点平顶: VF 版不可行 / 静态版已实现

多档 VF 下 m_apexmerge 的布尔运算在三档切出不同拓扑（99.7% 签名不一致），
报 VarLibCFFPointTypeMergeError。**这是架构级限制，不要重试。**
静态单档版已成功实现，详见「🎉 顶点平顶已在单档静态版实现」。

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

#### 为什么这个模块能成功
```
m_apexmerge 用 pathops 布尔运算改拓扑 -> 三档切出不同结构 -> 失败
m_ledge 纯点坐标平移，不动段数/操作符 -> 三档必然一致 -> 成功

教训: CJK 结构问题优先用「只移动已有点」的方式解决。
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

### ✅ 全库系统扫描方法（2026-11-16）

不再凭猜测挑字。已建立两个全库扫描工具，**每次大改后跑一遍**。

#### 1. `modules/scan_struct.py` — 结构异常扫描（3.5 秒）
```bash
cd /workspace/wdsans2 && python modules/scan_struct.py
```
检查: 轮廓数是否远多于 SHS、bbox 偏差是否 >15%
**性能关键: 字体只打开一次**（每字重开 TTFont 会从 3.5 秒变成 5 分钟以上）

实测结果：
```
bbox 偏差 >15%: 0 字          <- 字号比例完全正常
轮廓数比 SHS 多 3 个以上: 3059 字
```
3059 字「轮廓多」是**误报**: SHS 的 CFF CharStrings 用 subr 子程序复用，
展开成 RecordingPen 后轮廓边界与 SHS 原版天然不同。**不是缺陷。**

#### 2. 墨量分布扫描 — 找视觉差异最大的字
4x4 网格墨量占比向量 + L1 距离，全库 3755 常用字。
```
偏差分布: 中位28.03 均值29.12 P90=40.60 P99=56.20 最大77.50
最大: 叶 77.50 / 吓 76.29 / 吃 75.13 / 玄 72.90 / 又 72.28
```
排查结论：**全部是高偏差但非缺陷**。逐字验证了 叶/叫/吃/又/玄/车 等，
「口」旁闭合正常，竖直重心偏差仅 0.004（500 字采样）。
偏差来自**部件位置与比例的微小差异**，属风格范畴。

#### 🔴 折角测量的严重陷阱（重要）
早期「多」字测出 98°/101° 钝角与 61°/62° 锐角，看起来像缺陷。
实际是**短臂造成的假折角**：
```
我们 多 c0: 113.9° @(298,575) 臂长 67/12   <- 短臂仅 12 单位
             97.8° @(507,499) 臂长 72/10   <- 短臂仅 10 单位
```

**正确判据：两侧臂都 >= 40 且角度在 70~110° 才算真实折角。**
过滤后实测（全部精确 90°，与参考一致）:
```
字   我们      OPPO    HOS     SHS
各   15个@90  11个@90 16个@90 12个@90
永   11个@90  11个@90  9个@90  6个@90
亨   18个@90  17个@90 16个@90 14个@90
口   12个@90   8个@90 12个@90 12个@90
中   16个@90  12个@90 20个@90 24个@90
```

#### 方法学总结
```
1. 任何「聚合统计指标」都必须先做「对照组验证」：
   口/回/十/中/申/甲 是天然直角对照组（三家都是精确 90°），
   如果它们被算成非 90°，说明是测量方法问题，不是字形问题。

2. 视觉缺陷要靠「放大渲染 + 逐行墨段扫描」确认，
   不能只靠单一数值指标。本轮扫描出的所有高偏差字都是误报。

3. 扫描工具自身要有性能意识：字体只开一次，避免 O(n) 次 IO。
```

### ✅ VF 插值与子集完整性验证（2026-11-16）

三个必查项，`modules/vi*.py` 系列脚本可复用。

#### 1. 字重插值：必须用拉丁字测，不能用 CJK
```
🔴 陷阱: CJK 是等宽设计，advance 在所有档位都是 1000 单位恒定。
   用 CJK 测「字宽是否随字重变化」会得到「完全无变化」的错误结论。

正确做法: 用拉丁字与符号测。
  Hamburgefonstiv  250=7875 → 400=8074 → 700=8443 → 900=8690  ✓ 单调递增
  minimum          250=4246 → 400=4390 → 700=4583 → 900=4713  ✓
  0123456789       250=5210 → 400=5550 → 700=5870 → 900=6090  ✓
  —                250= 638 → 400= 663 → 700= 704 → 900= 732  ✓

CJK advance（应恒定）:
  永 [1000,1000,1000,1000]  永国字体 [4000×4]  永国字体设计的书 [8000×4]  ✓
```

#### 2. CJK 字形映射：康熙部首共用是正确设计
```
抽查发现「一」映射到 uni2F00（康熙部首名）而非 uni4E00：
  U+4E00(一) -> uni2F00  gid=9506
  U+2F00(⼀) -> uni2F00  gid=9506   <- 同一字形

SHS 把汉字与对应康熙部首共用一个字形（以部首名命名），节省槽位。
OPPO/HOS 用 uni4E00 命名但不共用。**两种都正确，渲染完全一致。**
抽查 10 个基本字（一人儿入八口日月木水）全部如此。
```

#### 3. 子集完整性：HarfBuzz 不能直接读 woff2
```python
# 🔴 直接 open(woff2) 喂给 HarfBuzz 会全部返回 gid 0（静默失败）
f = TTFont(W); f.flavor = None
buf = io.BytesIO(); f.save(buf); f.close()
data = buf.getvalue()   # 用解压后的数据
```

实测（解压后）:
```
常用 3500 在子集中缺失: 0
竖排: 9/9 有替换（： — … 。 「 」 ！ ？ ～）
sups [6701,7192,7193]  subs [7201,7202,7204]
frac [7215,308,7216]   pnum [18,19,20]
calt: 12:34 -> gid309(居中)  a:b -> gid27(基线不替换)  ✓
fvar wght 250-900 保留
```

子集丢失 5 种特性（hist ljmo ruby tjmo vjmo）—— 韩文 Jamo 与注音专用，
fontTools 会丢弃「目标字形不存在」的特性，前提页无影响。**中文竖排 9/9 正常。**

### 🎉 顶点平顶已在单档静态版实现（2026-11-16）

**这是 6 项笔画风格指标中唯一未达成项的突破。**

#### 为什么单档可以、多档 VF 不行
```
多档 VF: pathops 布尔运算在三档切出不同拓扑（99.7% 签名不一致）
         -> VarLibCFFPointTypeMergeError，无解
单档静态: 没有插值约束，可以做
```

#### 参考字体的做法
```
HOS  今: qCurveTo(464,839) -> lineTo(540,839)   平顶宽 76
OPPO 今: qCurveTo(460,824) -> lineTo(528,824)   平顶宽 68
我们 今: 两个独立尖点，顶宽 0
```

#### 关键判据（走了 5 版才对）
```
❌ v1-v3 只做 pathops 合并 -> 两个尖点变成一个尖点，顶宽仍 0
❌ v4   判据缺「顶部轮廓要窄」-> 误伤 甲/田（把横画当顶点）
❌ v5   MAX_TOPW=300 用「全轮廓 bbox 宽度」-> 人字形两笔各占半字宽(499/532)，全被排除，命中 0
✅ v6   改用「顶部 3% 高度带内的墨宽」作为判据，正确区分:
         今  c2 顶宽 1   c3 顶宽 0    <- 双尖点，命中
         甲  c0 顶宽 79  c1 顶宽 751  <- 竖笔端面+横画，跳过
         田  c2 顶宽 810 c3 顶宽 76   <- 横画+竖笔端面，跳过
```

#### 🔴 pathops API 三个致命坑
```python
# 坑1: difference 需要「轮廓列表」不是 Path 对象
pathops.difference(merged, cutter, out.getPen())        # ❌ 'tuple' has no attribute 'draw'
pathops.difference(list(merged.contours), list(cutter.contours), out.getPen())  # ✅

# 坑2: path.contours 是生成器，必须 list() 转换
len(merged.contours)   # ❌ generator has no len()
list(merged.contours)  # ✅

# 坑3: difference 是三个位置参数 (subject, clip, outpen)
pathops.difference([pa, pb], out.getPen())   # ❌ _do() missing 'outpen'
```

#### 实现（`modules/m_apexflat.py`）
```python
APEX_WIN   = 70     # 顶部窗口
FLAT_DEPTH = 28     # 截平深度（决定平顶宽度）
MAX_TOPW   = 40     # 顶部墨宽上限（区分尖点与横画）

# 1. 找顶部 70 单位内、顶宽都 <40 的两个轮廓
# 2. pathops.union 合并
# 3. 构造顶部切刀矩形（y > gmax - FLAT_DEPTH）
# 4. pathops.difference(合并轮廓, 切刀) 得到平顶
```

#### 效果（400 档，`FLAT_DEPTH=28`）
```
字   改前    改后    HOS    OPPO
今   0/5 →  79/4    76/3   68/3   ✓
合   0/5 →  82/4    75/4   71/4   ✓
会   0/7 →  91/6    77/3   66/5
含   0/7 →  78/6    76/4   66/5   ✓
令   0/6 →  77/5    77/3   69/4   ✓ 精确命中
全   0/6 →  83/6    75/1   69/5
金   0/8 →  89/7    76/4   66/7
余   0/7 →  81/6    84/4   74/6   ✓
介   0/4 →  58/3    76/3   67/3
企   0/6 →  84/5    76/2   67/5

规模: 1804 字，跳过 0
对照组 10/10 零误伤: 口回十中申甲田日国目
```

#### 部署
```
静态版: /workspace/static/wdsans/WDesignSans-FlatApex-Regular.otf  (17.8 MB)
name:   WDesign Sans FlatApex Regular
VF 版保留不变（平顶与多档插值不兼容）
```

两个版本并存: 日常使用 VF（250-900 全字重），需要平顶风格时用静态版。

### 平顶静态版的完整验证（2026-11-16）

部署后必须验证特性真的生效，不能只看 glyphs/cmap 数量。

#### 特性验证（HarfBuzz，全部通过）
```
默认 123 : [63167, 63168, 63169]   (等宽，locl 生效)
sups 123 : [43272, 61877, 61878]
subs 123 : [61910, 61911, 61914]
frac 1/2 : [61927, 3265, 61928]
numr 123 : [61927, 61928, 61931]
dnom 123 : [61941, 61942, 61943]
pnum 123 : [18, 19, 20]

zh-hans sups 123: [43272, 61877, 61878]   <- ZHS LangSys 已注册 ✓
calt 12:34 = [63167,63168,3346,63169,63170]  3346 是居中冒号 ✓
calt a:b   = [66, 27, 67]                    27 是基线冒号 ✓
竖排 9/9 有替换，中文字宽恒定 1000/字
```

#### 表完整性
```
FlatApex 17 表: BASE CFF2 GDEF GPOS GSUB OS/2 STAT VORG cmap head hhea
                hmtx maxp name post vhea vmtx
VF       20 表: 上述 + HVAR fvar VVAR
-> 静态版少 HVAR/fvar/VVAR 是对的（静态无变体轴）
```

#### 位图复验（400px，四体对比）
```
字   静态版  可变版  OPPO   HOS
今    36      5     28    32
合    34      8     31    33
会    38      8     29    33
含    36      5     31    33
令    36      8     29    33
全    33      6     29    33
金    37      8     28    33
余    32      6     32    36
介    27      6     29    32
企    34      6     30    33

对照组 10/10 完全一致零误伤:
口 299/299  回 334/334  十 31/31  中 30/30  申 31/31
甲 299/299  田 323/323  日 262/262  国 330/330  目 271/271
```
**几何测量与位图测量双重验证一致，平顶真实生效。**

#### 预览页新增「顶点平顶」面板
```
四行对比: 本字体静态版 / 本字体可变版 / OPPO Sans / HOS
需新增 hos-compare.woff2（12.3 KB，285 字形子集）供 CmpHOS 使用
指标表同步更新为 R25 实测值（重心 0.499 / 中宫 43.2% / 撇捺展开 0.524/0.535/0.610）
```

### ✅ 全库缝隙与碎裂检测（2026-11-16）

新增两个全库扫描工具，补上此前从未检测的「像素级缺陷」维度。

#### 1. `modules/scan_gap.py` — 几何近邻缝隙（22 秒）
```
检测两个轮廓本应相接、但留有 0.5~10 单位微缝的情况。
这类缝隙在渲染时会变成发丝裂缝（hairline crack）。

结果: 「我们 0.5~10 单位 / SHS 无缝」的候选 14 字
  靡9.6 廖9.1 签8.5 窘8.0 熔7.9 赊7.7 秩7.3 窝7.0
  滁5.1 愉4.5 臆4.5 敝4.4 捧4.1 爵1.0
```

**⚠️ 重要: 最小缝隙分布不能直接比**
```
  我们: 中位 3.64  P90=32.00
  SHS : 中位 34.67 P90=72.00
```
我们的中位只有 SHS 的 1/10，看起来「轮廓贴得过近」。
但这是**测量口径差异**: SHS 用 subr 子程序复用，展开后轮廓边界天然更少更整；
我们是逐轮廓存储，轮廓数更多，最近邻距离自然更小。
**不能据此判定缺陷。**

#### 2. `modules/scan_frag.py` — 位图碎裂度（6 秒，3755 字）
```python
from scipy import ndimage
lab, n = ndimage.label(bitmap)   # 数墨迹连通块
# 96px 实际使用尺寸渲染，缝隙会切断笔画 -> 块数变多
```

结果（我们 - SHS 的块数差值）:
```
  中位 0.0   均值 -0.07   n=3755
  我们更完整  6 字 (0.2%)
  略好      371 字 (9.9%)
  相同     3236 字 (86.2%)
  略碎      140 字 (3.7%)
  明显更碎    2 字 (0.1%)   <- 嘴(+4) 眠(+3)
```
**86.2% 完全一致，均值 -0.07 说明整体略优于 SHS。**

#### 3. 最终判定：位图墨量（最可靠）
```
字   我们      SHS      差
嘴  42.9%   45.1%   -2.2%
眠  45.6%   47.1%   -1.5%
靡  42.3%   42.0%   +0.3%
廖  37.7%   37.8%   -0.1%
签  35.7%   36.2%   -0.5%
窘  43.9%   42.9%   +1.0%
熔  37.9%   37.6%   +0.3%
赊  36.2%   37.0%   -0.8%
秩  36.9%   37.5%   -0.6%
窝  42.2%   42.4%   -0.2%
滁  36.2%   37.2%   -1.0%
愉  38.1%   37.9%   +0.2%
臆  44.1%   43.9%   +0.2%
敝  41.7%   42.8%   -1.1%
捧  38.8%   39.2%   -0.4%
爵  44.8%   44.7%   +0.1%
```
**墨量差全部在 ±2.2% 内，且约半数为正（我们更饱满）。**
-> 所谓「缝隙」是轮廓拆分方式不同导致的测量假象，**不是真实笔画断裂**。

#### 🔴 方法学：三层递进判据
```
第1层 几何近邻距离   -> 只能生成候选，不能定罪（受轮廓拆分方式影响大）
第2层 位图连通块数   -> 能发现系统性碎裂，但单字 ±2 块属噪声
第3层 位图墨量占比   -> 最可靠，±3% 内一律视为一致
```
**任何「缝隙/断裂」结论必须走到第3层才能下。**
本轮 14 个候选字全部在第3层被判定为非缺陷。

### 🔴 事故：重建链又一次漏掉 latinreset（2026-11-16）

**用户反馈**: 「拉丁字体怎么又变窄了？」

#### 实测
```
阶段              H     A     M     W
R16 (latinreset前) 550   597   687   858
R24a              550   597   687   858
R25 (旧)          550   597   687   858   <- 与 R16 完全相同
Mona @400         544   587   648   867
```
H = 550 而应为 583，比值 550/583 = 0.943 = m_latinmat 的 SCALE。
**这说明 latinreset 没有生效。**

#### 根因
```
R25 = R24a + featlang
R24a = R16 + punctscale
-> 第41轮从 R16 出发重建时，漏掉了 R18 的 m_latinreset
```
**与第40轮漏掉 m_curvflat 完全同类的错误：**
重建链时凭记忆挑模块，没有对照「原链已部署模块清单」逐项核对。
两者都是纯几何模块，不改拓扑，三档一致性与 VF 构建都不会报错，
只能靠视觉或指标测量发现。

#### 修复
```
masters_R25b = R25 + m_latinreset  (486字形 × 3档)
效果: H 550 -> 583, A 597 -> 635, M 687 -> 728, W 858 -> 910
VF 重建 320s / 41.3MB
预览子集重建 2.21MB / 7600 字形 / GSUB 缺失 0
```

#### 🔴 强制检查清单（重建链后必须逐项确认）
```
原链已部署的全部几何模块，按顺序核对（缺一不可）:
  1. m_barple      (T6 -> MOD)
  2. m_shortl      (R1)
  3. m_zerocont    (R2)
  4. m_bardiag     (R4)
  5. m_latinmat    (R5)
  6. m_latinext    (R6)
  7. m_kerning     (R7)
  8. m_markpos     (R8)
  9. m_metrics     (R9)
 10. m_nametable   (R10)
 11. m_os2range    (R11)
 12. m_coloncenter (R12)
 13. m_numfeats    (R13)
 14. m_numfeats2   (R14)
 15. m_frac        (R15)
 16. m_ledge       (R16)
 17. m_latinreset  (R18)   <- 两次被漏掉的就是这个
 18. m_featlang    (R19)
 19. m_punctscale  (R24a)
```
**最容易漏的是纯几何模块（latinreset / punctscale / ledge），**
因为它们不改拓扑，构建不会报错，也不会触发三档一致性门禁。

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
| 顶点平顶（人字形） | 今 合 会 含 令 | ✅ 已在单档静态版实现（1804字），VF 版不可用 |
| 横折出头（厶/廴 结构） | 丝 延 各 | 顶部横笔已解决（m_ledge 2,636字）；其余形态待攻 |
| 永字左下 7 形拐角 | 永 | ✅ 已核查非缺陷（渲染假象，我们断行 16 < HOS 35） |
| 纟旁拐角 | 丝 红 | ✅ 已核查非缺陷 |
| 建字左侧部首 | 建 | 已放弃（多轮 KD_/CT_/DX_ 等 10+ 方案全部回滚） |
| 多字拐角 | 多 | ✅ 已核查非缺陷（短臂假折角，过滤后精确 90°） |
| 缝隙/碎裂 | 嘴 眠 靡 廖 等 | ✅ 全库 3755 字扫描，墨量差全在 ±2.2% 内 |
