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
masters_MOD18 MOD17 + name 表修正                     构建中 ← 当前链尾
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
| 横折出头（厶/廴 结构） | 丝 延 各 | 判据未定 |
| 永字左下 7 形拐角 | 永 | 待分析 |
| 纟旁拐角 | 丝 红 | 待分析 |
| 建字左侧部首 | 建 | 待分析 |
| 多字拐角 | 多 | 待分析 |
