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
masters_R34  = R33 + m_radfoot       11 字 部首出脚
masters_R35  = R34 + m_middotadv     1 字形 中点标点advance
masters_R36  = R35 + m_lineheight     三档行高1.35em
masters_R37  = R36 + m_fbclean        版本号+GDEF mark
     R38 = R37 + m_fbclean2(VF后处理)  STAT/name/zh-CN
     R39 = R38 + chws_tool            GPOS chws/vchw
     R41 = R37 + m_vertend            8579字 撇捺末端垂直平切
     R42 = R41 + m_vertend(0.90)      补 1040 字（含「人」）
     R44 = R42 + m_cff2ttf_multi      三档联动转 TTF，产物化 ← 当前链尾
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
| `m_middotadv` | 中点类标点 advance 205→500 | 1 字形 | 已并入 R35 |

### ❌ 已废弃: m_termface / m_termface_v2（C→L 端面拉直）
```
判据: 段长 [0.8,1.5]×SW 且弯曲偏离 dev/L < 0.10（v2 放宽到 0.16）
废弃: 命中范围远超「笔端面」，把大量真实弧线也拉直了
      全库曲线 38.2% -> 30.0%（-8%），视觉明显「变方」。
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
### m_zerocont / m_shortl / 模块饱和度
```
shortl: L 段长 0.3~min(15,0.20*SW) 且前后都是 C -> 直接删该段
  短L段分类: C-L-C 3523(可删) / L-L-C 2776 / L-L-L 3011 / C-L-L 373
  只处理 C-L-C，其余破坏结构。实测 3,369 字 4,966 段
zerocont: 轮廓面积(鞋带) < 50 em² -> 删除整个轮廓（保证至少留1个）
  实测全库 45 处，全部段数=3 共线三角形
饱和度: barple 1字/stepalign 188字/bardiag 29字 其余全 0

❌ 已否决 m_zeroseg（删零长度段）: 各档独立删 -> 1199 字三档不一致。
  250 档零长度处，在 900 档是真实短边（中位13）。正解: varLib 自行丢弃。
  现有 17 处零长度段属已知无害。
```
### m_latinext（补 Latin Ext-A）
```
从 Mona VF 按 250/400/900 实例化，注入未映射槽位（21,189 个可用）。
效果: Latin Ext-A 30 -> 125/128，cmap 44,853 -> 44,948
🔴 必须用 DecomposingRecordingPen（Mona 多为复合字形，RecordingPen 只拿组件引用）
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
kerning: 从 Mona 提取 77,294 对, KERN_SCALE=0.65（未缩放时 AT/LT/To 过紧）
  坑: buildPairPosGlyphs 第1参数是 dict，返回 subtables list 需自行包 Lookup
markpos: 22 组合符号 x 442 基字母 -> MarkBasePos + MarkMarkPos
  🔴 Coverage 必须按 glyph id 排序，按字形名排序会导致三档顺序不同 -> VF 报错
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

关键位验证: bit2 Ext-A 125字符 / bit40 160 / bit41 128 / bit70 225 / bit86 CJK 20992

**同时修正 ulCodePageRange**: 新增 bit50(936 简体中文) / bit52(950 繁体中文)。

**教训**: 字符集扩张后必须重算 OS/2 分类位，否则字形存在但系统认为不支持。

### m_coloncenter 判据（时间冒号居中）
```
问题: 横排 12:34 的冒号偏低。实测 zero 中心 +364 / colon +258，差 -106。
      OPPO colon.centered 与 HOS colon.ss03 都居中（差 -1）-> SHS 没修。
方案: 复制冒号轮廓上移到数字中心 -> 未映射槽位 -> 数字间 calt 替换。
效果: 12:34 -> gid117(居中)；a:b -> gid27(基线)。

🔴 三次失败:
  1. feaLib addOpenTypeFeaturesFromString 替换整个 GSUB -> 16 features 掉到 1 个
  2. 备份+反向合并破坏 locl 的 script 映射
  3. 手写 ot.Coverage() 读回 Format=None，HarfBuzz 静默跳过
✅ 可行方案: 只把 subtable 追加到已接线的 calt lookup#30（latn feature#68）
  FeatureList/ScriptList 完全不动 -> 原有特性零风险。
验证: lookups 52->54, lookup#30 subtable 1->3, 16 种 feature 全在位。
```
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
locl 先把 zero~nine 换成 glyph63166~63175(等宽)，所以任何以数字为
input 的 feature，mapping 都要叠加 locl_tab（两套 input 都覆盖）。
验证: 默认123=gid63167(521) sups=gid43272(241) frac 1/2=[61925,4744,61927]
### ❌ 已废弃: m_curvflat
**不要使用。** OPPO/HOS 只有 350 条长曲线，我们有 2853 条，该指标不适用。
强行压平使撇捺展开 0.531 -> 0.616~0.629（参考 0.531）。详见「m_curvflat 有害」。

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

"""### 顶点平顶：VF 不可行 / 静态版也已移除（2026-11-19）
```
多档 VF: pathops 布尔运算在三档切出不同拓扑（99.7% 签名不一致）
         -> VarLibCFFPointTypeMergeError。架构级限制，不要重试。
单档静态: 曾实现 1804 字，对照组 10/10 零误伤。
2026-11-19 用户裁定：已删除 FlatApex 与全部相关 UI。
```
"""
### ❌ 已彻底废弃: m_ledge / m_ledge2 / m_ledge3
```
三轮全失败，R29 已完全移除:
  v1(MOD29) 1,182字 / v2(MOD30) 2,636字且改坏曲线
  v3(L3)    1,511字，实测误伤 1,456 / 20,992 字

误伤实测(R15无ledge vs R28有ledge3):
  位移>100: 462字 (珔518/玸508/玦498/硛497/砍479/殃460)
  位移20~100: 807字  位移5~20: 187字  合计 1,456字

根因: 判据只有「纯L横笔+宽高比>=2.8+ymax>=顶部-150」，
      没检查「横笔右侧是否还有其它部件」-> 左侧偏旁的横笔被拉过界。

结论: 「横折出头」靠纯轮廓几何判据无法安全实现。
若重做必须: 部件级分割 或 手工白名单。
```
### m_chufoot 判据（「出」类字右下伸脚）
```
四家底边（400档）: 我们/ SHS / HOS 都只有右竖到底(宽82)，OPPO 整个底横到底(宽752)
结构: c1 右下竖 x[813,895] y[-79,340];  c3 底横右端 853 落在竖内 -> 40 单位台阶
修法: 底横右端 853->813（贴竖左缘）; 右竖下端 -79->-23（与横下缘齐平）
命中 7 字: 出屈拙咄础茁黜（三档 7/7/7）。出 底边 宽82->791
🔴 判据坑: 粗字重笔画变厚 -> MAXW={250:110,400:140,900:200}
```
### m_seamfix3 判据（闭合轮廓首末点缝隙）
```
根因: SHS 的「永」是 3 个合并轮廓，我们的链重构成 7 个独立笔画轮廓，
      拆分时首末点各自整数舍入 -> 留 1~11 单位残差。
      采样 23,214 缝隙 dx/dy 中位都是 0.00 -> 纯舍入，非设计偏移。
规模: 我们 20,479/20,992(97.5%)  SHS 1,092  HOS 285

🔴 判据 area/gap > 1000（闭合接缝比值极大，开放笔画两端比值小）
  对照: 口 222/689 skip | 十 897/81 skip | 一 916 skip | 日 205~561 skip
       永 c4 21019 HIT | 丁 c1 28260 HIT
🔴 两次失败: 只用 gap 0.8~8 -> 命中 20,468 字会焊死开放笔画；
  第二次加了面积比但误把 20,479 当 bug 没做对照组。
教训: 命中数异常大时先跑对照组（口/日/十/一）。
修法: 末点贴回起点，只移动一点 -> VF 安全。全库缝隙 97,121 -> 0。
```
### m_spikefix6 判据（撇端点尖刺）
```
用户：「眼字这个还没修复」——艮部右下有细尖上扬。

实测(400档 c4): 我们 C c1(451,-67) c2(483,-56) -> (689,84)  端点抬高 84
                SHS  同控制点                        -> (690, 0)  平口在 0
控制点几乎一致（差 1-2），只有端点 y 高 84 -> 来自 T6 的 m_taper。

🔴 三档结构不同: 250 尖端在 seg2 且低于自己的 c2;
                400 尖端在 seg1 且 x 最大; 900 尖端在 seg2 但 x<轮廓最大。
  -> 「按 x-max 找尖点 + 各档独立检测」不可行。

修法: 400 档检测记录 (轮廓索引,段索引)，三档套用同一索引，
      各自取该档出向控制点 y，只移动一个端点 y -> VF 安全。
命中 11 字: 眼根跟很恨銀银限艰良艮
```
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

### 🔴🔴 事故：import 模块触发顶层代码，覆盖 masters_R32（2026-11-19）
```
写调试脚本时 `import m_by0align` 只想复用函数，但该模块无 __main__ 保护，
顶层代码立即执行：读 WDS_SRC -> 写 WDS_OUT（默认 masters_R32！）
-> masters_R32/master-ExtraLight-250.otf 被覆盖成 R34 的内容。
发现: 时间戳异常（06:39 vs 其他档 01:34）。恢复: 从 v261118 存档 cp 回，MD5 通过。

根因: 全部 45 个 m_*.py 都没有 if __name__ == "__main__"。
     任何 import 任何模块都可能触发文件写入，系统性隐患。

修复(guard2.py): 找「最后一个 def/class 之后」的第一个非 Assign/Import 语句，
  从那里到末尾才是执行段；纯模块不改；def/class/顶层常量保持模块级可见。
结果 34 个加保护，13 个纯模块跳过。验证: 46 个语法正确 /
  12 个重模块 import 后 masters MD5 不变 / m_boxrad.find 与 m_radfoot.find 仍可用。

🔴 第一版 guard 的错误: 把 def 之后所有内容都包进 __main__，连 def 也包进去，
  导致 find/apply 变成不可见的 __main__ 局部函数。
  发现方式是在 modules_trial 副本先试跑（hasattr(find)=False）。
  教训: 批量改文件必须先 trial 试跑，且必须验证「原有 API 仍可见」，
        不能只看语法和「无副作用」。
```

### ❌ 已证伪：用当前 m_barple 重放能改善撇厚（2026-11-19）
```
假设: MOD 是历史产物，其 seg3 终点 (770,685) 与当前 m_barple 产出 (758,708) 不同，
      用当前模块从头重放，撇厚问题会自动改善。

实测（T6 上重放，WDS_* 全指向临时目录，不碰 masters_*）:
  档    T6(原)  重放barple  SHS   R34(现)   结论
  250     31       33       28      38     改善 5
  400     74       79       71      79     相同
  900    161      171      154     161     恶化 10 <<<

三档方向不一致 -> 重建链只会让 900 档更差。
结论: ❌ 不要为修撇厚而重建链。此方向已证伪。
     根因仍是横笔右端 770 vs SHS 722（「拐角竖直」的固有代价），
     历史 MOD 参数不是主因。
```

### ✅ 六项笔画风格指标完整对照（508字×4字体）
```
字体    比例W/H    中宫%   重心    撇捺展开60/70/80     折角°
我们    360/360   34.1   0.501   0.655/0.665/0.659   90.0
SHS     361/361   34.3   0.499   0.661/0.663/0.663   90.0
OPPO    358/366   31.1   0.501   0.633/0.648/0.652   90.0
HOS     358/359   37.2   0.499   0.664/0.684/0.678   90.0

vs SHS: 比例-1/-1 中宫-0.2 重心+0.002 撇捺±0.006 折角/切角 完全一致
-> 六项全部与基座一致，无一项需改。

🔴 笔末切角专项: 横笔端面倾斜量 dx
  我们 41 处 全 0.0  SHS/OPPO/HOS 各 6 处 全 0.0
  对照组 十一二三工王土地士干平正生目日田口回中申甲
```
### 🔴 交付物虚报修正（2026-11-19）
```
发现: 预览页/README 展示了从未实现的功能，与 AGENTS.md 记录矛盾。

三处虚报:
  1. index.html 指标表「横折出头 右余90 已对齐」
     -> m_ledge 三轮失败已彻底移除，从未上线。已删除该行。
  2. index.html 简介「横折出头…修正了 2,636 个字」
     -> 数字来自有问题的 m_ledge2（破坏曲线+误伤1456字）。已删除。
  3. poster/README.md 开头「...撇捺收锋、顶横出头」
     -> 去掉「顶横出头」，新增「## 尚未实现」章节。

实测真相（顶部横笔右余）:
  中位: 我们143(11字) / SHS216(2字) / OPPO158 / HOS152
  夏 我们45 vs SHS216/OPPO196/HOS192；亨 我们0 vs SHS215/OPPO119/HOS113
  -> 我们的横笔其实更长（继承SHS），不是「已对齐到90」。

教训:
  1. 废弃模块的「命中数」不能当成绩展示 —— 命中 ≠ 正确。
  2. 模块废弃时必须同步清理所有对外表述。
  3. 交付前交叉核对「页面宣称」vs「AGENTS.md 真实状态」。
```

### ✅ 交付物一致性审计 claim_audit.py（已并入主审计）
```
背景: 连续两轮发现展示层与真实状态不符（功能虚报+数字偏差），固化为脚本。
检查 11 项: 文件大小 / 字符数 / 功能虚报 / HTML结构 / 平顶字数
  功能虚报: 正则「关键词+已实现」，黑名单 顶横出头/横折出头；另查废弃 m_ledge2 的 2,636

🔴 第一版正则漏洞（靠负向测试才发现）:
  r"横折出头[^<]{0,40}已对齐" —— 实际 HTML 中间有 </td><td> 标签
  [^<] 无法跨越 -> 注入虚报后仍 PASS（假阴性）
  修正: r"横折出头.{0,300}?已对齐" + re.S

🔴 负向测试（必做）: 注入虚报行 -> exit=1, FAIL 2；恢复后 exit=0, PASS 11

教训: 1) 防虚报的脚本自己也要负向测试 2) 正则匹配HTML不能用[^<]
      3) 已并入 audit.py SCRIPTS，成为第三组审计。
```

### ✅ CJK 笔画跨字重插值验证（2026-11-19）
```
此前只验拉丁 advance（CJK advance 恒定 1000 测不出）。
本轮用 HarfBuzz draw_glyph_with_pen + fontTools BasePen 取真实轮廓。

字   w250→w900 宽    相邻档跳变          备注
十    883 → 919     +4.4 ~ +4.7  均匀
王    883 → 919     +4.4 ~ +4.7  均匀
叫    749 → 872    +14.8 ~ +16.3 均匀  <- m_boxrad 改过
昨    872 → 914     +5.2 ~ +5.3  均匀  <- m_boxrad 改过
晴    864 → 911     +5.8 ~ +6.0  均匀  <- m_boxrad 改过
国    812 → 855     +5.2 ~ +5.7  均匀
永    908 → 964     +7.0 ~ +7.0  完全均匀

-> 7 字全部单调增、跳变均匀。叫/昨/晴 为 m_boxrad 改过的字，
   插值平滑 -> 按字重缩放 BOTTOM_EXTEND(35/80/152) 设计正确。

🔴 方法学: HarfBuzz draw 比实例化文件快 100 倍
  instantiateVariableFont 每字重约 3 分钟（41MB VF）
  HarfBuzz set_variations + draw_glyph_with_pen 只需毫秒
  pen 必须是 BasePen 子类对象，不能传回调函数
```

### ✅ 小字号完整性验证（12/14/16/24px，504字）
```
面向手机 UI，实际用 12-16px，此前测量全在 96px 以上。
与 SHS 差异: 12px 墨-0.50%/块-0.006 | 14px +0.51%/+0.042
            16px +1.57%/+0.232 | 24px -0.76%/+0.010

🔴 16px 块数偏多是测量假象，非缺陷。三重证据:
  1. VF 与 FlatApex 块数几乎相同（数11/11 边10/10 规10/10）-> 与平顶无关
  2. 轮廓级「x 间隙 0~4 单位接缝」扫描: 我们 0 / SHS 0 -> 无笔画错位
  3. 阈值敏感: 我们 t=64/128/192 -> 1/11/21  SHS -> 1/4/19
     t=64 两家都是 1；t=192 时 SHS 逼近我们 -> 抗锯齿灰边被二值化切碎
  另: 8x 超采样后「全」7->1、「京」9->4（干净）
```

### ✅ R35 中点标点 advance 修正（2026-11-19，已部署）
```
发现: 中英混排段落目视对比时看到「设置·消息」的间隔号两侧无留白。
  字符        我们   SHS   OPPO  HOS
  U+00B7 ·    205   1000   500   500
  U+2022 •    205   1000   500  1000
  U+30FB ・   205   1000    -   1000
根因: 四码位共用 periodcentered，advance 从 Mona 继承 205u（Mona@400 = 205），
      中文 UI 需要更宽间隔。从 T6 就存在，非模块改坏。
修正: m_middotadv 改 advance 为 500u，三档 489/500/538
      只改 hmtx 不动轮廓 -> 零视觉风险
效果: 「设置·消息」1641->1759(HOS 1763) 「A·B」603->721(HOS 709)，13标点未动。
🔴 未做: U+2022 • 墨迹 118 vs 参考 229 偏小，属语义问题需新字形。
🔴 designspace 陷阱: wd_mod.designspace 指向 masters_MOD（旧链）!
   构建前必须 sed 生成指向新链的 designspace，否则构建出旧字。
```

### 🔵 U+2022 • 墨迹偏小：裁定不修改
```
实测: 我们 118x126 / HOS 231x230 / OPPO 230x229（面积比 0.28）

🔴 但 SHS 原版也是四码位共用一个字形:
  U+00B7 · / U+2022 • / U+2027 ‧ / U+30FB ・  ->  cid01649（全部共用）
  我们的 118x126 就是 SHS 的设计（只是换了三次曲线）。
  OPPO/HOS 拆分是因为它们自己重新设计了整套标点。

判定: 不是缺陷，是与基座一致的设计选择。
      符合项目原则「骨架继承 SHS，只在具体缺陷上动」。

技术硬约束（尝试过并放弃）:
  font 已达 65,535 字形上限（maxp.numGlyphs 是 uint16）
  -> 无法新增槽位；只能覆写未引用槽位（11,724 个候选）
  -> 但覆写会丢失该槽位原轮廓，若未来特性需要它会拿到错字形
  -> 代价大于收益，不做。

教训: 三次曲线转换本身可行（Mona bullet 4段QM -> MCCCCCCCCZ，
      三档签名一致，墨迹尺寸不变 215/227/259）。障碍只是槽位上限。
```
### 🔵 行高 1.45em 偏大：裁定不修改
```
实测（四字体，同一 100px 字号三行文本）:
  字体   line_h  行高/字号  3行墨迹总高
  我们     145     1.45em      384 px
  SHS      145     1.45em      384 px   <- 同源
  OPPO     132     1.32em      359 px   -9%
  HOS      118     1.18em      329 px   -19%

根因: usWinAscent=1160, usWinDescent=288（SHS 原版值）。
      CJK 墨迹实际最高只到 860，富余 300 单位留给注音/上标。

🔴 但抬高/压低都不行（实测超界字形数）:
  usWinAscent   超界字形数
     1000          20
     1050          16
     1100           4   <- 已是全局最优
     1160           4   <- SHS 现值
     1325           4   （但行高变 1.62em，更高）

1160 是「超界字形最少 + 行高不过分」的折中。

那 4 个超界字形是什么:
  U+302A 〪  IDEOGRAPHIC LEVEL TONE MARK        （注音专用）
  U+302D 〭  IDEOGRAPHIC ENTERING TONE MARK     （注音专用）
  U+3031 〱  VERTICAL KANA REPEAT MARK           （日文竖排专用）
  U+3032 〲  VERTICAL KANA REPEAT WITH VOICED    （日文竖排专用）
  我们与 SHS 数值几乎相同（-303~-118 / -549~1323）
  在中文横排正文中出现概率接近 0。

裁定: 不是缺陷，是 SHS 基座的合理取舍。符合项目原则
      「骨架继承 SHS，只在具体缺陷上动」。

若未来要收紧行高，正确做法是给这几个字建独立 fallback，
而不是动全局 usWin（那样会连带影响所有字符的行距）。
```
### ✅ R36 行高修正 1.45em -> 1.35em（2026-11-19，已部署）
```
问题: hhea/win=1448=1.45em，比 OPPO(1.32)/HOS(1.18) 松 10-19%。
      14px 下 7 行 UI 文本: 我们 142px vs OPPO 129px vs HOS 116px。

为什么不能直接压 hhea/usWin:
  全库极端值（排除 7 个竖排专用符号）: 最高 1069(U+1EB2) 最低 -281(U+FFE8)
  实测各 usWinAscent 超界字形数: 1000->20 1050->16 1100->4 1160->4 1325->4
  压低必然裁切，抬高行高更大 -> 直接改 hhea 是死路

方案: 启用 USE_TYPO_METRICS(fsSelection bit7)
  usWin 保持 1160/288 -> 竖排符号不裁切
  typo 设为 1070/-282 -> 1352 = 1.35em
  🔴 bit7 只在 OS/2 v4+ 定义，我们/SHS 都是 v3
  v3->v4 实测只改 version 字段，42 字段其余不变，文件大小不变

对比: OPPO/HOS 都是 v4 但都没启用 bit7（直接压 hhea）
      我们启用 bit7 是 OpenType 标准做法，能同时保住竖排符号

模块 m_lineheight: 三档 OS/2 v3->v4 + typo(1070,-282,0) + fsSel |= 0x80
效果: 行高 1.45->1.35em，7行 142->132px（OPPO 129px）
      VF 41.3MB glyphs=65535 cmap=45012 cjk=20992（与 R35 一致）

五个产物全部同步 + cache-buster 202611190836 -> 202611191003
审计扩到 28 项（新增第9组: OS/2版本/bit7/行高范围/usWin保守值）
```
### ✅ R37 fontbakery 驱动的质量修复（2026-11-19，已部署）
```
方法转变: 前几轮都是自写脚本测量。本轮改用 fontbakery 1.1.0（Google Fonts 官方
检查器，127 项检查），让专业工具指出问题 —— 避免「自己写工具又自己评判」。

  /workspace/wdsans/venv/bin/fontbakery check-universal <font>
  已装: fontbakery 1.1.0 / uharfbuzz 0.57 / blackrenderer 0.6 / booleanOperations 0.1

R36 报告 3 FAIL + 3 WARN:
  FAIL opentype/font_version   head=2.00499 vs name=Version 1.000
  FAIL base_has_width          uni20DD/uni20DE advance=0
  FAIL file_size               39.4Mb > 9Mb（CJK 必然，不修）
  WARN gdef_mark_chars         20+ 组合符号未在 mark class
  WARN post_table_version      format 3 小众问题（CFF2 必需）
  WARN cjk_chws_feature        缺 chws/vchw（日文专用）

修 1 版本号不一致（真缺陷，我们引入）:
  m_nametable 只改了 name ID5，漏改 head.fontRevision（仍是 SHS 的 2.00499）
  -> head.fontRevision = 1.000

修 2 GDEF mark class 几乎为空（SHS 继承缺陷，只有 4 个）:
  这导致 base_has_width 误报: uni20DD 是 COMBINING ENCLOSING CIRCLE,
  advance 本来就该 0，但不在 mark class -> 被当基底字符检查
  修: 按 unicodedata.category 补全 -> mark 4 -> 30

🔴 迭代: 初版按 Mn/Mc/Me 全标 -> mark=32，fontbakery 立刻报 2 个新 WARN
  gdef_non_mark_chars / gdef_spacing_marks 都指向 U+302E/U+302F
  它们 category=Mc（间距型组合标记）adv=250，SHS 原版也未分类
  修正: 只标 Mn(28个) + Me(2个)，排除 Mc(2个) -> mark=30 -> WARN 消失

效果: FAIL 3->1（只剩 file_size）/ WARN 3->2
      font_version / base_has_width / gdef_mark_chars /
      gdef_non_mark_chars / gdef_spacing_marks 全部通过

🔴 必验证: GDEF 改动不能影响既有 mark 定位。用 uharfbuzz 对比 R36/R37
  （选无预组合字符的组合，强制走 mark 定位）:
    b+acute     R36(-588,364)  R37(-588,364)    完全一致
    d+acute     R36(-612,363)  R37(-612,363)
    g+tilde     R36(-513,-224) R37(-513,-224)
    k+diaeresis R36(-429,-4)   R37(-429,-4)
  中文/数字不受影响: 永国字体 4000 / 0123456789 5740

审计扩到 34 项（新增第 11 组固化 fontbakery 报告项）
五个产物同步 + cache-buster 202611191107
```
### ✅ R38 fontbakery 完整报告驱动的第二批修复（2026-11-19，已部署）
```
🔴 工具用法: fontbakery 必须加 --succinct --skip-network 才跑得完全部 127 项。
   不加参数会卡在第 6 项（CFF2 大文件上部分 check 极慢），只能看到部分结果。

  fontbakery check-universal --succinct --skip-network <font>

R37 完整报告 3 FAIL + 6 WARN，本轮修掉 2 FAIL:

修 1 FAIL inconsistencies_between_fvar_STAT
  fvar 9 个 instance（250/300/350/400/500/600/700/800/900）
  STAT 只有 1 个 AxisValue 且 Format=2 无 Value 字段
  -> 9 个 instance 全无对应条目，应用读 STAT 无法识别字重名称
  修: 每个 instance 建 Format 1 的 AxisValue，按 AxisIndex+Value 排序
  结果 STAT 1 -> 10

修 2 FAIL no_mac_entries（我们引入的）
  name 表 20 条 platformID=1（Mac），SHS 原版只有 platform 3
  来源: bvf 脚本里写了 [(3,1,0x409),(1,0,0)] —— 自己加的
  OpenType 建议仅用 platform 3
  修: 删除所有 platformID=1 -> 50 条降到 30 条

修 3 🔴 zh-CN name 回归（严重）
  R37 部署版 zh-CN 0 条，SHS 原版 3 条。
  AGENTS.md 早已记录「VF 构建丢 zh-CN，必须 post_vf_name2 修复」，
  但 bvf_r37.py 自写的 name 替换没加 0x804 -> 回归。
  修: 从 master 复制 zh-CN 的 nameID 1/2/4/16/17，
      nameID17 在 master 里是 ExtraLight，强制改 Regular。zh-CN 0 -> 5 条。

验证: STAT 1->10 / platforms [1,3]->[3] / zh-CN 0->5 / nameID17=Regular
      不变项 head.rev=1.000 OS/2 v4 mark=30 glyphs=65535 cmap=45012
      HarfBuzz shaping R37 vs R38（11项）0 项不同
      fontbakery FAIL 3->1（只剩 file_size）/ WARN 6->5

剩余 fontbakery 提示（全部不可修）:
  file_size(41MB CJK 必然) / post_table_version(CFF2 必需) /
  cjk_chws_feature(日文专用) / ligature_carets / mandatory_avar_table /
  math_signs_width / ots

审计扩到 38 项（新增第 12 组 VF 元数据: STAT覆盖/platform3/zh-CN/nameID17）
存档 v261122（8 文件 111MB，md5 8/8）
```
### ✅ R39 新增 chws/vchw 东亚标点压缩（2026-11-19，已部署）
```
来源: fontbakery WARN cjk_chws_feature [missing-chws-feature, missing-vchw-feature]

chws = Contextual Half Widths（东亚标点行首/行尾自动压缩半角）
vchw = 竖排版本。符合 JLREQ 与中文标点挤压规范。

工具: chws_tool 1.4.5（Google Fonts 官方推荐）
  pip install chws-tool
  add-chws -o <输出> <输入>
  运行 41 秒，文件 +672 字节

🔴 关键陷阱: chws 加在 GPOS 不是 GSUB
  第一次检查找的是 GSUB -> 特性完全相同、chws 仍为 False，差点误判工具没生效。
  实际逐表对比字节: GPOS 262,178 -> 262,852 (+674)，其他 20 张表完全不变。
  原因: chws 是字距调整（调整标点 advance），不换字形。

实际改动:
  GPOS 特性 9 -> 11（+chws +vchw）  lookups 14 -> 20
  注册到全部脚本（DFLT/cyrl/grek/hang/hani/kana/latn），
  每个含 Default + JAN/KOR/ZHH/ZHS/ZHT -> 中文环境已挂载

效果:
  、。，「」  无chws [1000,1000,1000,1000,1000]
              有chws [ 500, 500, 500,1000,1000]
  竖排 、。   y_advance -1000 -> -500

安全性（chws 是 opt-in，不启用时排版不变）:
  22 个用例零差异（常规文本/中点/数字/拉丁/liga/时间冒号/
  sups subs numr dnom frac pnum/组合符号/CJK/中文标点 + 5 语言）
  表格结构 21->21 无增删
  元数据 rev=1.000 OS2v=4 typo=1.35em STAT=10 zh=5 mark=30 全不变

🔵 重要判断: 三家参考字体（SHS/OPPO/HOS）都没有 chws/vchw。
  所以这不是「缺失的应有功能」，而是可选的现代排版增强。
  加它是「多做正确的事」，不是修补缺陷 —— 与 U+2022/行高 的裁定标准一致。

fontbakery: R38 FAIL1/WARN6 -> R39 FAIL1/WARN5（cjk_chws 已消除）
剩余 6 项全部不可修: file_size / post_table_version / ligature_carets /
                     mandatory_avar_table / math_signs_width / ots

两个字体都加了（VF + FlatApex），子集也保留。
审计扩到 41 项（新增第 13 组）；存档 v261123。
```
### ✅ R44 TTF 产物化 + 三个致命坑（2026-11-19，已部署）
```
用户要求: 最终产物优先 TTF；去掉顶点平顶（静态版和 VF 都没用）。

产物: WDesignSans-VF.ttf  50.1 MB
      (OTF 39.3MB -> TTF 50.1MB；TTF 更大是因为保留了完整 gvar 插值)

## 🔴 坑 1: TTGlyphPen.qCurveTo 隐式合并点 -> 字重丢失
```
现象: 10 个拉丁字形（a b j o p u 0 5 6 9）字重完全不变化
      用户反馈「部分字形字重丢失」

根因: TTGlyphPen.qCurveTo 源码里 for pt in points[:-1]: _addPoint(pt,0)
      对「与上一控制点重合」的点做合并
      -> 同一条逻辑曲线在不同字重下产生不同点数
      -> w250:53点  w400:51点  w900:53点
      -> varLib 报 incompatible masters -> 跳过 -> 无 gvar -> 字重失效

✅ 修复: 直接构造 Glyph 数组，绕过 TTGlyphPen
   g.coordinates = GlyphCoordinates(coords)   # 🔴 必须用 GlyphCoordinates
   g.flags = bytearray(flags)                  # 1=on-curve 0=off-curve
   g.endPtsOfContours = endPts
   g.program = Program()
   传 list 会报 'list' object has no attribute 'calcIntBounds'

验证: 三档点数一致 a:53 b:53 0:58 H:12
      varLib incompatible 警告 36,495 -> 0
```

## 🔴 坑 2: curves_to_quadratic 的参数与返回值
```
签名: curves_to_quadratic(curves, max_errors)
      一次传三档同一条曲线 -> 保证点数一致（这是关键）

输入必须是 4 点 (start, c1, c2, end)
  传 3 点 -> calc_intersect() missing 1 required positional argument: 'd'

返回值是 [start, ctrl1, ctrl2, ..., end]
  qCurveTo 需要 [ctrl1, ..., end] -> 必须去掉首点
  不去首点 -> 'a' 墨差 74.51%；去掉 -> 1.52%
```

## 🔴 坑 3: designspace 必须有 <instances>
```
没有 <instances> -> fvar.instances = 0 -> STAT 无法生成 -> 只有 1 个 AxisValue

且 fontTools DesignSpaceDocument 的 SourceDescriptor:
  s.location={...} 和 s.designLocation={...} 都写不进 XML
  -> varLib 报 'More than one base master found'
✅ 可靠做法: 手写 designspace XML
   <location><dimension name="Weight" xvalue="400"/></location>
```

## 其它 TTF 转换要点
```
静态 OTF->TTF 三个必备修正（m_cff2ttf.py）:
  1. loca 必须用 table__l_o_c_a 实例（glyf.compile 调它的 set()）
     newTable('loca') 没有 set() -> 表被丢弃 -> PIL 报 SFNT missing
  2. sfntVersion 必须改 '\x00\x01\x00\x00'
     OTF 是 'OTTO'(0x4F54544F)，PIL/浏览器拒绝加载
  3. maxp.tableVersion 必须 0x00010000

TTF 反而修正了 OTF 的 lsb 不一致:
  OTF 87% 字形 lsb != bbox.xmin（CFF 允许任意）
  TTF  0.5% （TrueType 要求 lsb == bbox.xmin）
```

## 验收方法（血泪）
```
🔴 「所有字形都有 gvar」不代表 gvar 有效！
   gvar.variations 有 65,535 个键，其中 36,495 个是空的
   必须用 HarfBuzz 实测各字重宽度变化，不能只看键是否存在

🔴 验证样本必须覆盖: 大写/小写/数字/标点/中文
   之前只测「永国字体」+ 拉丁串，恰好漏掉 a/0/5/6/9

🔴 段落渲染对比必须用同一原点/基线
   两次渲染不同原点会误判「字间距变宽」
```

## 顶点平顶已移除
```
删除: WDesignSans-FlatApex-Regular.otf (17.9MB)
      @font-face WDesignFlat（index.html + poster/tokens.css）
      指标表「顶点平顶（人字形）」行
      「顶点平顶专项」panel
      孤儿 CSS: .apex-cmp/.ac-row/.ac-lbl/.ac-wf/.ac-wv/.ac-op/.ac-ho
      poster/wd-flat.woff2
poster_subset2.py 改为只从 TTF 生成 wd-vf.woff2
```
### ✅ 字形覆盖已达合规上限（2026-11-19）
```
cmap: 我们 45,012 / SHS 44,853 / OPPO 28,441 / HOS 29,063
  vs SHS: 缺 0, 多 159   常用 508 字: 缺失 0
所有区块 >= SHS。Latin Ext-A 30/128 -> 125/128（融合 Mona 最大收益）

🔴 与 OPPO/HOS 的 218 个缺口全部无法补:
  其中 SHS 也没有 218（全部），Mona 可供仅 1
  主要缺口: Cyrillic 63 / Greek 27 / Gen Punct 23 / Currency 15
            Latin Ext-B 14 / Super-Sub 11 / Number Forms 9
Mona 仅剩 4 个可补（฿ + 2 笑脸 + 1 PUA）-> 实用性极低，不补。
结论: 覆盖到此为止。再补必须扩大许可来源或换基座。
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
```
用户：「汉字字体所有曲线怎么都没了？」曲线占比 42.3% -> 32.7%

罪魁: 1) m_termface 的 C→L 把大量真实弧线也拉直了
      2) m_latinext 硬编码路径覆盖 CJK
修复: 放弃 termface/termface_v2/taper_v2，从 MOD 重建 R1..R16
效果: 曲线 32.7% -> 42.6%（SHS 42.3%），VF +0.9MB 正是曲线数据

教训: 1) 任何 C→L 类模块必须逐字验证，不能只看命中数量
      2) 复用「未映射槽位」的模块必须从当前基座读槽位表
      3) 门禁加「曲线占比」: 相对 SHS 偏差不超过 2%
```

### 🔴 拉丁宽度与预览子集修复（2026-11-15）
```
拉丁被 m_latinmat 压窄 5.7% -> m_latinreset 反缩放恢复（1/0.943=1.0604，486字形）
  效果 H 550->583 / A 597->635 / W 858->910（= Mona@400）
  两步骤是一对，重建链漏掉 latinreset 会让拉丁窄 5.7%

预览子集需保留 GSUB 目标字形（populate 只保留文本字符）:
  收集 sups/subs/sinf/numr/dnom/frac/pnum/calt/liga/dlig 的 lookup 目标
  + 展开 ChainContext 内部引用 + 排除 lookup#30（谚文 calt 2.4万目标）
  结果 GSUB 指向缺失字形 0 条
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
```
scan_struct (3.5秒): bbox 偏差>15% 的 0 字；轮廓数比 SHS 多 3 个以上 3059 字
  -> 3059 是误报: SHS 用 subr 复用，展开后轮廓边界天然不同
  性能关键: 字体只开一次（每字重开 TTFont 会从 3.5 秒变 5 分钟）

墨量分布扫描（4x4 网格 + L1 距离，3755 常用字）:
  中位28.03 均值29.12 P90=40.60 最大77.50(叶)
  -> 全部高偏差但非缺陷，来自部件位置与比例微小差异

🔴 折角测量陷阱: 短臂假折角
  多 c0: 113.9° 臂长 67/12（短臂仅 12）
  正确判据: 两侧臂都 >=40 且角度 70~110° 才算真实折角
  过滤后全部精确 90°，与 OPPO/HOS/SHS 一致

方法学: 1) 聚合指标必须先做对照组验证（口/回/十/中/申/甲）
        2) 视觉缺陷要放大渲染+逐行墨段扫描，不能只靠单一数值
        3) 扫描工具自身要有性能意识
```

### 🎉 顶点平顶已在单档静态版实现（2026-11-16）
```
为什么单档可以、多档 VF 不行:
  多档 VF: pathops 布尔运算在三档切出不同拓扑(99.7%签名不一致)
           -> VarLibCFFPointTypeMergeError，无解
  单档静态: 没有插值约束，可以做

参考值: HOS 今 平顶宽 76 / OPPO 今 68 / 我们 0（两个独立尖点）

关键判据（5 版才对）:
  v1-v3 只做 pathops 合并 -> 顶宽仍 0
  v4 缺「顶部轮廓要窄」-> 误伤 甲/田
  v5 用全轮廓 bbox 宽度 -> 人字形两笔各占半字宽，命中 0
  ✅ v6 用「顶部 3% 高度带内的墨宽」: 双尖点 0~1 / 横画 700+ / 竖笔端面 70~80

pathops 三个坑:
  difference 需要「轮廓列表」不是 Path 对象，且要 list() 转换生成器
  difference(subject, clip, outpen) 三个位置参数

m_apexflat: APEX_WIN=70 FLAT_DEPTH=28 MAX_TOPW=40
效果: 1811 字，对照组 10/10 零误伤(口回十中申甲田日国目)
  今 0/5->79/4 (HOS 76/3) 令 0/6->77/5 (HOS 77/3) 精确命中
部署: WDesignSans-FlatApex-Regular.otf（VF 版保留，平顶与多档插值不兼容）
```

### ✅ 全库缝隙与碎裂检测（2026-11-16）

新增两个全库扫描工具，补上此前从未检测的「像素级缺陷」维度。

#### 1. scan_gap.py / 2. scan_frag.py
```
scan_gap: 两轮廓本应相接但留 0.5~10 单位微缝。候选 14 字（靡/廖/签/窘/熔等）
  ⚠️ 最小缝隙不能直接比: 我们中位3.64 vs SHS 34.67 —— 测量口径差异
     （SHS 用 subr 复用，展开后轮廓边界更少更整），不能据此判缺陷。
scan_frag: 96px 位图连通块数。3755 字: 中位0.0 均值-0.07
  相同 3236 字(86.2%) / 略好 371 / 略碎 140 / 明显更碎 2（嘴+4 眠+3）
```
#### 3. 最终判定：位图墨量（最可靠）
```
16 个候选字（嘴眠靡廖签窘熔赊秩窝滁愉臆敝捧爵）墨量差全部在 ±2.2% 内,
且约半数为正（我们更饱满）。最大 -2.2%（嘴）/ 最小 +0.1%（爵）。
-> 所谓「缝隙」是轮廓拆分方式不同导致的测量假象，不是真实笔画断裂。
```
### ✅ 全模块效果审计系统（2026-11-16）
```bash
cd /workspace/wdsans2 && python modules/audit.py   # exit 0 = 全部通过
```

为什么需要: 连续两轮「重建链漏模块」（第40轮漏 curvflat，第41轮漏 latinreset）
两者都是纯几何模块，不改拓扑 -> 三档一致性与 VF 构建都不报错，只能靠测量发现。

三组审计: audit_all（表与特性）/ audit_geom（几何与排版）/ claim_audit（交付物）
详见下方「claim_audit.py」与「R38」章节，当前共 38 项。

🔴 审计脚本自身的坑（都踩过）:
  Mona 是 VF，必须实例化到 wght=400 才能比（否则 1.082 假 FAIL）
  标点偏差要分别对宽和高算，不能拿高度差比宽度目标（否则 -330% 假 FAIL）
```

### 🔴🔴 事故：m_ledge 误伤 2,033 字（2026-11-17）
```
用户：「到」字上方横变形。
实际改动 2,645 字，单点位移>150 的 2,033 字全是误伤
  最严重: 覴601 / 璥586 / 璈577 / 瓎575 / 彲569
根因: 判据只有「纯L横笔+宽高比>=2.8+ymax>=顶部-150」，
      没检查「横笔右侧是否还有其它部件」-> 左侧偏旁横笔被拉过界。
修法: m_ledge3 加「右侧阻挡」判据 -> 2,645 降到 1,511 字
  if ox0 > bx1 + 2: return None   # 横笔右侧有部件 -> 跳过

教训: 1) 判据要有「排除条件」，不能只要求命中条件
      2) 上线前逐字抽查对照组（口/回/十/中）
      3) 用 R前->R后 逐字 diff 统计爆炸半径，超预期就回头查判据
```

### 数字 9 来源不一致（2026-11-17）
```
用户：「9 明显比其他数字细一些」
0-8 已从 Mona 注入，只有 9 还是 SHS 原版，面积小 14%
  9  我们 143766/555  vs  Mona400 167141/628

🔴 Mona 的 nine 是「six 上下翻转」的复合字形，必须用
   DecomposingRecordingPen（RecordingPen 只得 addComponent）
这是第三次踩同一坑（m_latinext / m_latinmat / m_digitnine）

修: m_digitnine 从 Mona 按 250/400/900 实例化取 nine 轮廓,
    advance 同步 250=620 / 400=628 / 900=649
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

"""### 3.2b m_taper 三条硬约束
```
1. 400 档检测，三档套用同一 (ci,k,j) 三元组（索引必须存全三元组）
2. 不可重复运行：NARROW=0.95 只收 5%，段长仍在判据内，每跑一次继续削细
3. 依赖 m_termface 的 C->L 才有目标（现链已跳过 termface，命中很少）
```
"""
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
