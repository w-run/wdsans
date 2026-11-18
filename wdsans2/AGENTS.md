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
masters_R25b = R25 + latinreset  486字形宽恢复
# 2026-11-17 重建（修 m_ledge 误报 + 数字 9 来源）
masters_L3   = R15 + m_ledge3   1,511字（旧版误伤 2,645 字）
masters_R26a = L3  + punctscale
masters_R26b = R26a + featlang
masters_R26  = R26b + latinreset
masters_R27  = R26 + m_digitnine  数字9 换 Mona
# 2026-11-17 晚：m_ledge 误伤 1,456 字，彻底移除
masters_R29  = R15 + punctscale + featlang + latinreset + digitnine + chufoot
masters_R30  = R29 + m_spikefix6   眼字艮部撇尖 11字
masters_R31  = R30 + m_seamfix3    全库 20,479 字闭合缝隙
masters_R32  = R31 + m_by0align    326 字 bar/body 接合点 y 跟随本档
masters_R33  = R32 + m_boxrad     1,040 字 闭口偏旁垂直居中+拉高
masters_R34  = R33 + m_radfoot       11 字 部首出脚  已部署 ← 当前链尾
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
| ~~`m_ledge`~~ | 顶部横笔右端延伸（横折出头） | 三轮失败 | ❌ 已彻底废弃，误伤 1,456 字 |
| `m_chufoot` | 去掉「出」类字右下伸脚 | 7 字 | 已并入 R29 |
| `m_digitnine` | 数字 9 换成 Mona 版本 | 1 字形 | 已并入 R29 |
| `m_spikefix6` | 修复撇端点被抬高成尖刺 | 11 字 | 已并入 R30 |
| `m_seamfix3` | 闭合轮廓首末点缝隙 | 20,479 字 | 已并入 R31 |
| `m_by0align` | bar/body 接合点 y 跟随本档 | 326 字 | 已并入 R32 |
| `m_boxrad` | 闭口偏旁垂直居中+拉高 | 1,040 字 | 已并入 R33 |
| `m_radfoot` | 左偏旁底部出脚 | 11 字 | 已并入 R34 |

### ❌ 已废弃: m_termface / m_termface_v2（C→L 端面拉直）
```
判据曾是: 段长 [0.8,1.5]×SW 且弯曲偏离比值 dev/L < 0.10（v2 放宽到 0.16）
废弃原因: 命中范围远超「笔端面」，把大量真实弧线也拉直了，
          全库曲线占比 38.2% -> 30.0%（-8%），视觉上明显「变方」。
详见「重大事故：曲线全部丢失」。不要重新启用。
```
### m_bardiag / m_yanrad 判据
```
bardiag: bar(3段纯L,宽>=1.0SW,高<=2.5SW) 右端未达斜边外缘 0.05~0.60SW -> 拉到外缘
  「建」C5 292->315/307 (消 23 单位台阶)
yanrad: 9段轮廓签名 CLCLLLCCL (建延健庭廷挺), a5=尖角收到横线右上角
  关键: a7 用「法向偏移保宽」, 否则斜边被压窄 (实测 延 78->44)
  全库含该签名 63 字, 命中 62
```
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
barple 1字/stepalign 188字/bardiag 29字/yanrad+termface+shortl+zerocont 全 0。
residue 由前面模块改几何产生，MOD10 依次跑 barple→stepalign→bardiag 得 186字。

### ❌ 已否决: m_zeroseg（删零长度段）
```
各档独立删除 -> G3 报 1199 字三档不一致。
250 档零长度的位置在 900 档是真实短边（中位 13 单位）。
正解: varLib 构建时自行丢弃，不需人工清理。
```

### m_latinmat / m_latinreset（拉丁宽度）
```
m_latinmat: 拉丁所有轮廓沿 x 绕中心缩放 k=0.943，advance 不变。
  理由曾是「拉丁竖干比 CJK 粗 5.7%」（对 SHS 拉丁的测量）
  但常用拉丁已从 Mona 注入，Mona 字形本身已协调 -> 不该再压窄
m_latinreset: 反向 1/0.943 = 1.0604 缩放回去（486 字形）
  效果 H 550->583 / A 597->635 / W 858->910（= Mona@400）

🔴 教训: 这两步是一对，重建链时若漏掉 latinreset，拉丁会窄 5.7%。
```

### m_latinext（补 Latin Ext-A）
```
从 Mona VF 按 250/400/900 实例化，注入未映射槽位（21,189 个可用）。
效果: Latin Ext-A 30 -> 125/128，cmap 44,853 -> 44,948

🔴 必须用 DecomposingRecordingPen：Mona 的多为复合字形，
   RecordingPen 只返回组件引用拿不到真实轮廓（实测只成功 12/95）。
```
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

### m_kerning / m_markpos 判据
```
kerning: 从 Mona 提取 77,294 对, KERN_SCALE=0.65
  未缩放时 AT/LT/To 过紧; 0.65 时与 Mona 平均偏差 2.44px 最优
  坑: buildPairPosGlyphs 第1参数是 dict, 返回 subtables list 需自行包 Lookup
markpos: 22 组合符号 x 442 基字母, 生成 MarkBasePos + MarkMarkPos
  🔴 Coverage 必须按 glyph id 排序, 按字形名排序会导致三档顺序不同 -> VF 构建报错
```
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

### m_metrics 判据
fsSelection: 我们原 0x0000 -> 已修为 0x0040（三个参考字体都是 0x0040）。
**未修**: usWin 未覆盖 〱〲〪〭 四个竖排字形（超界 261/163/16），
SHS 原版同样超界 -> 上游缺陷。提高 usWin 会让行高 +29.4%，代价过大。

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

### ⚠️ VF 构建会丢弃多语言 name 记录
varLib 只保留 master 的 Windows en-US(0x409) 与 Mac(0x0)，zh-CN(0x804) 全丢。
**修复**: `python modules/post_vf_name2.py <VF>`（WDS_MASTER 指定当前链尾 master）。
🔴 ID17 (Subfamily) 必须强制固定为 'Regular'（master 里是 ExtraLight）。
验证: langIDs 应含 0x804。审计项 `nametable.zh` 会检查这一点。

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

#### 🔴 三次失败（务必避坑）
```
1. feaLib addOpenTypeFeaturesFromString 会替换整个 GSUB -> 16 features 掉到 1 个
2. 备份+反向合并会破坏 locl 的 script 映射
3. 手写 ot.Coverage() 读回 Format=None，HarfBuzz 静默跳过
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

### m_numfeats / numfeats2 / frac 判据（数字排版特性）
```
OPPO/HOS 有 8 个: tnum pnum frac subs sups sinf numr dnom
我们实现 7 个: pnum sups subs sinf numr dnom frac  (tnum 冗余, 本字体默认已等宽)

sups/subs/sinf = 默认数字缩放62%, 上移34%em / 下移16%em
pnum = locl 的 tabular 映射反向 -> 恢复比例数字
numr = 缩放60% 上移33%em   dnom = 缩放60% 下移10%em
frac = slash->fraction + zero~nine->*.numr + ChainContext [fraction]numr'->dnom

cmap 补齐: U+2070-2079 填7个, U+2080-2089 填10个

#### 🔴 同一个 locl 坑（踩了三次）
locl 先把 zero~nine 换成 glyph63166~63175 (等宽)，所以:
  lookup input 写 one 匹配不上，要写 glyph63167
  mapping 必须同时覆盖两套 input
规律: 任何以数字为 input 的 feature，mapping 都要叠加 locl_tab。

验证(HarfBuzz): 默认123=gid63167(521)  sups=gid43272(241)
  pnum=gid18(363)  numr=gid61925(217)  frac 1/2=[61925,4744,61927]
```
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

### ❌ 已彻底废弃: m_ledge / m_ledge2 / m_ledge3（2026-11-17）

**三轮尝试全部失败，现链 R29 已完全移除该模块。**

```
v1 (MOD29): 1,182 字
v2 (MOD30): 2,636 字，且改坏曲线
v3 (L3)   : 1,511 字，实测误伤 1,456 / 20,992 字
            其中 462 字横向位移 > 100
```

#### 误伤实测（R15无ledge vs R28有ledge3）
```
位移 >100: 462 字   珔518 玸508 玦498 硛497 砍479 殃460 孜449 功431
位移 20~100: 807 字  位移 5~20: 187 字  合计 1,456 字
```

#### 结论与替代方向
```
「横折出头」靠纯轮廓几何判据无法安全实现。若将来重做，必须:
  1. 建立部件级分割（」偏旁 vs 整字」，不是单轮廓判据）
  2. 或改用手工白名单（逐字确认后再改），放弃全库自动检测
```

### m_chufoot 判据（去掉「出」类字的右下伸脚）

用户反馈：「出」右下出脚没去掉。

#### 四家底边实测（400 档）
```
我们  最低边 x[813,895] 宽  82   <- 只有右竖到底（SHS 形态）
SHS   最低边 x[814,895] 宽  81
HOS   最低边 x[804,885] 宽  81
OPPO  最低边 x[118,870] 宽 752  <- 整个底横到底，无伸脚  <<< 目标
```

#### 轮廓结构（400 档）
```
c1（右下竖）x[813,895] y[-79,340]
c3（底横）  (104,-23)->(853,-23)->(853,52)->(187,52)
                        ^^^^^^^ 853 落在右竖 813~895 内 -> 40 单位台阶
```

#### 修法（纯点移动，段数不变）
```python
底横右端 x: 853 -> 813   # 贴住右竖左缘
右竖下端 y: -79 -> -23   # 与底横下缘齐平
```

命中 7 字: 出 屈 拙 咄 础 茁 黜（三档 7/7/7）
效果: 出 底边 宽82 -> 宽791（全宽，与参考一致）

#### 🔴 判据坑: 粗字重笔画变厚
```
400 档竖笔宽  82 -> 阈值 w<130 可过
900 档竖笔宽 164 -> 被 w<130 排除，0 命中
修正: MAXW = {250:110, 400:140, 900:200}
```
### m_seamfix3 判据（闭合轮廓的首末点缝隙）

用户反馈：「永的竖弯钩那里还是有一处错位」——放大看是一个台阶。

#### 定位（逐阶段 + 模块重放，绕了两圈才找对）
```
逐阶段：c4 缺口 3.2 从 T6 起就有，之后 R10/R15/R29/R30 完全不变
重放验证：m_taper ops=3 / m_stepalign ops=0，两者都不改端点，gap 始终 0.0
真正原因：SHS 的「永」是 3 个合并轮廓（一笔贯通 18 段），
         我们的链把它重构成 7 个独立笔画轮廓，
         拆分时首末点各自整数舍入 -> 留下 1~11 单位残差。
```

#### 偏移规律（证明是舍入残差，不是设计偏移）
```
采样 23,214 个缝隙的偏移向量：
  dx 中位 0.00  均值 -0.21  范围 [-4, 11]
  dy 中位 0.00  均值 -0.15  范围 [-7, 5]
最常见：(0,-1) 2512次 / (-1,0) 2397 / (1,0) 2044 / (-2,0) 2012
-> 两轴都以 0 为中心，是纯整数舍入残留
```

#### 规模
```
  我们 20,479 / 20,992 字（97.5%）
  SHS   1,092 字
  HOS     285 字

严重度（400档）：
  >=4 单位:   667 字   大字号可见
  3~4 单位:  2,196 字
  2~3 单位: 13,551 字  0.28% em，正文不可见
  <2 单位:   4,065 字
```

#### 🔴 判据：面积/gap 比值
```
闭合笔画的接缝：首末点接近，但轮廓围成大面积 -> 比值极大
开放笔画的两端：首末点相距远 -> 比值小

判据: area / gap > 1000

对照组验证（必须做，否则会焊死开放笔画）：
  口  ratio 222 / 689   -> skip ✓
  十  897 / 81          -> skip ✓
  一  916               -> skip ✓
  日  205 ~ 561         -> skip ✓
  永 c4  21019          -> HIT  ✓（就是那个台阶）
  丁 c1  28260          -> HIT  ✓
```

#### 🔴 两次失败（几乎毁掉字库）
```
m_seamfix 只用 gap 0.8~8 一个条件 -> 命中 20,468 字 / 96,837 轮廓，
  会把开放笔画（横、撇）的首尾焊成线 -> 立即终止删除。
m_seamfix2 加了面积比，但我误把 20,479 当成脚本 bug，
  没先做对照组验证就下结论 —— 那个数字其实是真实的。
教训: 命中数异常大时先跑对照组（口/日/十/一），别先假设脚本错。
```

#### 修法
```
把末点坐标贴回起点（close_c）。
只移动一个点，段数与操作符不变 -> VF 安全。
```

#### 效果
```
永 250: [(3,2.2),(5,2.2)]                  -> none
永 400: [(2,2.0),(3,3.2),(4,3.2),(5,2.2)]  -> none
永 900: [(3,4.2),(5,4.5)]                  -> none
全库: 20,479 字 / 97,121 缝隙 -> 0 / 0
三档签名不一致: 0
部署版 VF: 永/丁/口/日/一/十/及 全部 seams=NONE
```

#### 新增审计项
```
audit_geom 增加 seam 检查（area/gap>1000，采样 4000 字）
现在几何审计 15 项全通过。
```

### m_spikefix6 判据（撇端点被抬高成尖刺）

用户反馈：「眼字这个还没修复」——艮部右下有细尖上扬。

#### 实测（400 档 c4 轮廓）
```
我们: C c1(451,-67) c2(483,-56) -> (689, 84)   <- 端点被抬到 y=84
SHS : C c1(452,-67) c2(484,-56) -> (690,  0)   <- 平口在 y=0

控制点几乎完全一致（差 1-2 单位），只有端点 y 高了 84。
```

#### 阶段追溯
```
SHS  单轮廓（撇与竖相连，无独立 c4）
T6   c4 出现，尖点 (689, 84)   <- 在这一步产生
MOD / R15 / R29 完全一致
-> 来自 T6 的 m_taper，不是 m_ledge
```

#### 🔴 三档结构不同（关键坑）
```
  250: 尖端在 seg2 (684, 40)，且低于自己的 c2
  400: 尖端在 seg1 (689, 84)，x 是最大值
  900: 尖端在 seg2 (692,111)，但 x=692 < 轮廓最大 698

所以「按 x-max 找尖点 + 各档独立检测」不可行。
```

#### 修法
```
1. 400 档检测，记录 (轮廓索引, 段索引)
2. 三档套用同一索引，各自取该档自己的出向控制点 y
3. 只移动一个端点 y -> VF 安全
```

命中 11 字：眼 根 跟 很 恨 銀 银 限 艰 良 艮

### m_boxrad 判据（闭口偏旁垂直居中 + 拉高）

用户：「口日田目这些部首应该再拉高一些」「相对于右侧主体」居中

#### 关键发现：不是位置偏，是偏旁被压扁了
```
轮廓级实测(400档，左偏旁轮廓组)：
字   R32 左偏旁        SHS 左偏旁        顶差  底差
叫   y[167,745] 578   y[ 79,749] 670    -4   +88
叨   y[165,747] 582   y[ 86,748] 662    -1   +79
叩   y[189,766] 577   y[ 96,766] 670     0   +93
叱   y[182,737] 555   y[ 85,737] 652     0   +97
昨   y[111,766] 655   y[ 30,762] 732    +4   +81
晴   y[118,772] 654   y[ 36,771] 735    +1   +82
-> 顶边几乎不动(-4~+4)，底边需下移 79~97(中位80)。是压矮了，需向下延伸。
```

#### 🔴 切分：x 间隙法失败，改用 y 范围聚类
```
x 间隙法的死穴：「口/日」由 U形主体+左竖组成，两者 x 投影重叠
  「叶」c2 x[115,373] / c3 x[75,145]   115 < 145 -> 无间隙可切
  只在 11/21 字上成功

✅ y 范围聚类(20/21 成功)：同一偏旁的多个轮廓 y 范围完全相同
  「叶」c2 y[173,734] c3 y[173,734]  完全相同
  「昨」c5 y[111,765] c7 y[111,766]  差 1
  做法：按 (y0,y1) 容差 4 聚类 -> 取 x_min 最左的簇
  验证：与 SHS 的 x 范围误差 <=3 单位
```

#### 🔴 两个参数坑
```
1. 宽高比下限 0.45 -> 0.30
   「日」旁宽267 高675，比值0.40，被0.45挡掉10个字
2. 三档独立检测 -> 400档驱动
   独立检测时250档少14字(生僻字笔画细) -> 签名不一致
   改400档检测+三档套同一索引 -> 三档全1,040字
```

#### 效果（17/17 匹配，误差 ±22 单位）
```
叫 h658 c416/SHS h670 c414   昨 h735 c400/h732 c396   晖 h734 c404/h735 c404
叨 h662 c416/h662 c417       晴 h734 c406/h735 c404   昕 h740 c399/h737 c398
叩 h657 c438/h670 c431       暗 h755 c392/h739 c398   叱 h635 c420/h652 c411
```

#### 数据源
```
cjkvi-ids（经 6629 代理下载）；IDS 数据放 /workspace/wdsans2/ref_ids/
⿰ 左右结构 14,558 字 -> 左偏旁为封闭方框 1,075 字 -> 实际改动 1,040 字
```

### m_radfoot 判据（左偏旁底部出脚）

用户：「都」左下的日字形底部右侧出脚还在、没被去掉

```
都 400档: c6 LLLLLL x[147,471] y[-16,374]  「日」外框
         c7 LLL    x[442,514] y[-60,374]  「日」右竖，底低 44
OPPO 该处完整闭合方框无出脚；SHS 同样有出脚（我们继承 SHS）

判据(严格版)：
1. 封闭方框：段数>=5, 宽高比0.35~2.8, 尺寸>=100, 右缘<=字宽55%
2. 竖条：LLL/LLLL, 高>=150, 宽<=高*0.6
3. 竖条 x 与方框右缘重叠
4. 竖条顶端与方框顶齐
5. 竖条底比方框底低 20~90

对照组 12 字(仰似倒假做修代件住你他们) 全部 0 命中

#### 🔴 放宽判据的陷阱
放宽到「任意竖条底低于方框 20~120」-> 命中 571 字
但含 命/可/哉/制/刷 等明显非同构的字
-> 保留严格判据的 11 字：僘厥塑嵞朔槊磊蒴都鬬鬭
结论：宁少勿滥。判据放宽到几百字时必然混入非同构字。

效果：都的出脚 250档 52->0 / 400档 44->0 / 900档 34->0
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

### 🔴🔴 重大事故：曲线全部丢失（2026-11-15）

**用户反馈**: 「汉字字体所有曲线怎么都没了？」曲线占比 42.3% -> 32.7%

#### 两个罪魁祸首
```
1. m_termface (MOD2): C→L 砍掉 8% 曲线
   判据「段长 0.8~1.5×SW 且弯曲比 <0.10」命中范围远超「笔端面」，
   把大量真实弧线也拉直了。

2. m_latinext (MOD6): 硬编码路径 masters_MOD12 导致覆盖 CJK
   复用的「未映射槽位」在 R5 中已被 CJK 占用 -> 直接覆盖真实字形。
   必须用 WDS_SRC / WDS_BASE 环境变量读当前基座。
```

#### 修复
```
用户决定「不要改曲线、之前的曲线就够」
-> 放弃 m_termface / m_termface_v2 / m_taper_v2（都依赖 C→L）
-> 从 MOD 重建链（R1..R16），保留 SHS 原始曲线

效果: 曲线 32.7% -> 42.6%（SHS 42.3%）
     永: LCCC / LLLCCCCC / LLCCC  <- 曲线回来了
     VF 40.4MB -> 41.3MB（+0.9MB 正是曲线数据）
```

#### 关键教训
```
1. 任何「C→L」类模块必须逐字验证，不能只看命中数量。
   8% 的全局曲线损失 = 视觉可察觉的「变方」。
2. 复用「未映射槽位」的模块必须从当前基座读槽位表。
3. 门禁加「曲线占比」: 全库 C/Q/QM 占比相对 SHS 偏差不超过 2%。
```
### 🔴 拉丁宽度与预览子集修复（2026-11-15）

#### 拉丁被 m_latinmat 压窄 5.7% -> 用 m_latinreset 反缩放恢复
```
m_latinmat 把所有拉丁轮廓 x 缩放 0.943（理由是「拉丁竖干比 CJK 粗 5.7%」）
但那是对 SHS 拉丁的测量；我们从 Mona 注入的字形本身已协调。

m_latinreset 做 1/0.943 = 1.0604 反向横向缩放（绕轮廓中心）
486 个拉丁字形，三档全一致
效果: H 550->583 / A 597->635 / W 858->910（与 Mona@400 一致）
```

#### 预览子集裁掉特性目标字形
```
fontTools populate(text=...) 只保留文本里出现的字符，不保留 GSUB 目标。
修复（probe/make_subset.py）:
  1) 收集 WANT = {sups,subs,sinf,numr,dnom,frac,pnum,calt,liga,dlig} 的 lookup 目标
  2) 展开 ChainContext 的 SubstLookupRecord 内部引用
  3) 🔴 排除 lookup#30（SHS 自带谚文 calt，2.4 万目标）只取冒号相关 subtable
  4) 过滤无轮廓的空壳槽位
结果: 7,600 字形 / 4.23MB，GSUB 指向缺失字形 0 条
```
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

#### ❌ 已否决: m_digitmono / m_pnumfix
```
硬阻塞: locl 与 pnum 在同一次 GSUB 传递中互相抵消
  locl:  one -> glyph63167
  pnum:  glyph63167 -> one      <- 又变回原样
除非新建独立的「比例数字」字形（占 10 个槽位），否则 pnum 无法与 locl 共存。
另: 三家实测本身不一致（参考厂商有比例有等宽）-> 保持 SHS 原行为即可。
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

### ✅ 全模块效果审计系统（2026-11-16）

**每次重建链 / 每次部署前必须跑一遍。**

```bash
cd /workspace/wdsans2 && python modules/audit.py
# exit 0 = 全部通过；exit 1 = 有 FAIL
```

#### 为什么需要它
```
连续两轮出现「重建链漏模块」:
  第40轮漏 m_curvflat   -> 撇捺被压得过直
  第41轮漏 m_latinreset -> 拉丁变窄 5.7%
两者都是纯几何模块: 不改拓扑 -> 三档一致性与 VF 构建都不报错,
门禁也全通过, 只能靠视觉或指标测量发现。
```

#### 审计项（表与特性 17 项 + 几何 13 项）
```
表与特性 (audit_all.py):
  latin 宽        与 Mona@400 比应为 1.000 (阈 ±1.5%)  <- 抓 latinreset 遗漏
  shortl          全库无 C-L-C 短段残留
  zerocont        无零面积轮廓
  metrics         fsSelection = 0x0040
  nametable       nameID 1/2 = WDesign Sans / Regular
  nametable.zh    langIDs 含 0x804  <- 抓 post_vf_name 遗漏
  os2range        ulUnicodeRange1 位已置
  numfeats        sups/subs/sinf 在 GSUB
  numfeats2       pnum/numr/dnom 在 GSUB
  frac            frac 在 GSUB
  coloncenter     calt 在 GSUB
  kerning         kern 在 GPOS
  markpos         mark + mkmk 都在 GPOS

几何与排版 (audit_geom.py):
  ledge           顶部横笔平均右余 <= 130 (目标 90)
  latinext        Latin Ext-A >= 120/128
  punct。、，：；  五个句读标点尺寸与目标偏差 < 8%
  featlang.*      sups/subs/sinf/numr/dnom 在 zh-Hans 下生效
  featlang.pnum   SKIP —— pnum 被 locl 抵消是已知正确行为
  coloncenter     12:34 的冒号 gid != a:b 的冒号 gid
```

#### 审计脚本自身的两个坑（都踩过）
```python
# 坑1: Mona 是 VF，必须实例化到 wght=400 才能比
fm = TTFont(MONA, lazy=True)
fm = instantiateVariableFont(fm, {'wght': 400}, inplace=True)   # ✅
# 不实例化会得到 1.082 的假 FAIL

# 坑2: 标点偏差要分别对宽和高算，不能拿高度差去比宽度目标
dw = abs(w - tw) / tw * 100
dh = abs(h - th) / th * 100
# 之前写成 abs(h - tgt)/tgt -> ：124x533 报「偏-330%」的假 FAIL
```

#### 2026-11-16 实测结果（R25b 部署版）
```
表与特性: PASS 17 / FAIL 0 / WARN 0
几何:     PASS 13 / FAIL 0 / SKIP 1
全部审计通过
```

#### 顺带修好的问题：中文 name 记录缺失
```
VF 构建会丢弃 zh-CN(0x804) 记录，必须后处理:
  旧: modules/post_vf_name.py 的 MASTER 硬编码指向 masters_MOD18
  新: modules/post_vf_name2.py 支持 WDS_MASTER 环境变量，
      默认指向当前链尾 masters_R25b

🔴 ID17 (Subfamily) 在 master 里是 'ExtraLight'（因为 master 是 250 档），
   复制到 VF 时必须强制改为 'Regular'。

效果: langIDs ['0x0','0x409'] -> ['0x0','0x409','0x804']
```

### 🔴🔴 事故：m_ledge 误伤 2,033 字（2026-11-17）

**用户反馈**: 「到」字上方横变形

#### 实测
```
到   R15 c3 x[ 70, 585] y[710,777]   <- 「至」的横笔，正确
     R16 c3 x[ 70, 822] y[710,777]   <- m_ledge 拉到 822，盖住右边「刂」
```
顶端 10% 区域墨量: 我们 13103 / SHS 9856 / OPPO 8898（多 33%）

#### 爆炸半径（R15 -> R16 逐字对比）
```
实际改动:      2,645 字
单点位移>150:  2,033 字   <- 全部是误伤
最严重: 覴 601 / 璥 586 / 璈 577 / 瓎 575 / 彲 569
```
**典型误伤**: 左边偏旁（王/石/月/鱼）的横笔被拖到字面右界，盖住右边部件。

#### 根因
```
m_ledge 判据只有两条:
  1. 纯 L 轮廓、宽/高 >= 2.8、宽 >= 300
  2. ymax >= 字形顶 - 150

没有检查「横笔右侧是否还有其它部件」。
左右结构字的左侧偏旁横笔同样满足这两条 -> 被当成整字顶横 -> 拉过界。
```

#### 修法: m_ledge3 增加「右侧阻挡」判据
```python
for j, c in enumerate(C):
    if j == ci: continue
    ox0, ox1, oy0, oy1 = bbox_of(c)
    if oy1 < by0 or oy0 > by1: continue    # y 不重叠
    if ox0 > bx1 + 2: return None          # 横笔右侧有部件 -> 跳过
```

#### 效果
```
命中: 2,645 -> 1,511 字（少改 1,134 字误报）

到  R15 x[70,585]余327 -> R16 x[70,822]余90(错) -> L3 x[70,585]余327  ✓ 修复
理  R15 x[318,967]余0  -> R16 x[45,877]余90(错) -> L3 x[318,967]余0   ✓ 修复
各  R15 x[241,764]余204 -> R16 x[289,878]余90 -> L3 x[289,878]余90   ✓ 保留
冬  R15 x[346,776]余181 -> R16 x[346,867]余90 -> L3 x[346,867]余90   ✓ 保留

我们 VF 顶端墨量: 修前 13103 -> 修后 10167 (SHS 9856)
```

#### 教训
```
「点平移」类模块虽然 VF 安全，但判据漏掉一个维度，误伤面会极大（本例 73%）。
必须做到:
  1. 判据要有「排除条件」，不能只要求命中条件
  2. 上线前逐字抽查「对照组」（口/回/十/中 是天然直角对照）
  3. 用 R前->R后 逐字 diff 统计爆炸半径，超过预期就回头查判据
```

### 数字 9 来源不一致（2026-11-17）

**用户反馈**: 「9 明显比其他数字细一些」

#### 实测（面积/adv）
```
字  我们            Mona400         来源
0   153640/642      155039/642      Mona
1    83142/390       82828/390      Mona
2   137343/544      138306/544      Mona
3   137799/570      139004/570      Mona
4   147733/622      147535/622      Mona
5   152955/576      153457/576      Mona
6   168074/628      167141/628      Mona
7   107818/517      108199/517      Mona
8   172711/600      172049/600      Mona
9   143766/555      167141/628      SHS   <- 唯一漏网
```
0-8 已从 Mona 注入，**只有 9 还是 SHS 原版**，面积小 14%。

#### 🔴 关键坑: Mona 的 nine 是「six 上下翻转」的复合字形
```python
rp = RecordingPen(gs); gs[gn].draw(rp)             # ❌ ops=1 (addComponent)
rp = DecomposingRecordingPen(gs); gs[gn].draw(rp)  # ✅ ops=18 -> 2 个轮廓
```
**这是第三次踩同一个坑**（m_latinext / m_latinmat / m_digitnine）。

#### 修法（m_digitnine）
```
从 Mona 按 250/400/900 实例化取 nine 轮廓，注入三档 master
同步 advance: 250=620 / 400=628 / 900=649
```

### 🔴 海报字体回退事故（2026-11-17）

**用户反馈**: 「等粗、角归正明显比其他字粗很多」

#### 根因
```
海报子集只含 212 个手工挑的字，但页面实际用了 360 个字符
缺失 235 个 -> 浏览器 fallback 到系统字体 -> 那部分字明显偏粗
```

#### 修法: `modules/poster_subset2.py`
```
扫描所有 HTML 的可见文字（去 style/script/标签），
加上常用符号（数字/字母/标点/°×÷ 等），
按实际用字生成子集，并校验「无缺字」。
```

#### 效果
```
212 字 -> 417 字
wd-vf 121KB -> 229KB,  wd-flat 63KB -> 118KB
页面用字 360/360 全覆盖，缺字 0
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

### 3.2b m_taper 的三条硬约束
```
1. 必须 400 档检测，三档套用同一 (ci,k,j) 三元组
   索引要存全三元组；只存 [ci,k] 会让 apply 静默无效（实测只应用 56 字）
   各档独立检测会让 900 档 SW=150 把段长判据变成 [82.5,217.5]，
   三档改动 17380/17405/11823 严重不一致。

2. 不可重复运行（判据不收敛）
   NARROW=0.95 只让端点各收 5%，段长 84.0 -> 79.8 仍在判据内，
   每跑一次继续削细 1.5~2 单位。一条链上只能跑一次。

3. 依赖 m_termface 的 C→L 才有目标
   现链已跳过 termface，故 m_taper 在 R 系列命中很少。
```
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
| 横折出头（厶/廴 结构） | 丝 延 各 | ❌ m_ledge 三轮失败已废弃（误伤1,456字）；需部件级分割或手工白名单 |
| 出字右下伸脚 | 出 屈 拙 咄 | ✅ 已修（m_chufoot，7字，对齐参考形态） |
| 永字竖弯钩台阶 | 永 | ✅ 已修（m_seamfix3，全库 20,479 字闭合缝隙归零） |
| 撇端点尖刺 | 眼 根 跟 | ✅ 已修（m_spikefix6，11 字） |
| 纟旁拐角 | 丝 红 | ✅ 已核查非缺陷 |
| 建字左侧部首 | 建 | 已放弃（多轮 KD_/CT_/DX_ 等 10+ 方案全部回滚） |
| 多字拐角 | 多 | ✅ 已核查非缺陷（短臂假折角，过滤后精确 90°） |
| 闭口偏旁压扁上移 | 叫 昨 晴 暗 | ✅ 已修（m_boxrad，1,040 字，误差 ±22 单位） |
| 左偏旁出脚 | 都 | ✅ 已修（m_radfoot，11 字，出脚归零） |
| 缝隙/碎裂 | 嘴 眠 靡 廖 等 | ✅ 全库 3755 字扫描，墨量差全在 ±2.2% 内 |
