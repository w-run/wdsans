# 工具链

> 目标：**先保证预览可信，再谈改字**。
> v2.0 · 2026-10-23 · 已清除全部废弃脚本，只保留 7 个

---

## 一、为什么不用浏览器预览

早期预览用浏览器 `@font-face` 加载子集字体。子集里少了测试字时，
浏览器会**静默回退到系统字体（PingFang）**，四列字全变成同一个字体，
页面上完全看不出来——由此得出过多个错误结论（包括"旧版更轻"这个反了 13% 的判断）。

现在的做法：**字体轮廓 → SVG → PNG（rsvg-convert）**。
路径数据直接来自字体文件，不经过字体加载，不存在回退。

---

## 二、两套画框（并存，各有用途）

### ① 预览画框：1040 单位见方

所有**看图**工具共用，不可随意改：

```
em 坐标（1000 upm）
  x ∈ [-20, 1020]      宽 1040
  y ∈ [900, -140]      高 1040
  → 8×8 网格，每格 130 单位
  → 列 a–h（左→右），行 1–8（上→下）
```

**任何字体、任何字形都用这一套**，所以 `d2` 在所有图里指同一块物理区域。

### ② 测量画框：1024 单位见方

只用于 `glyph_svg.py`，**1 设计单位 = 1 像素**，方便直接量：

```
x_px = x_em + 12           em x ∈ [-12, 1012]
y_px = 900 - y_em          em y ∈ [-124, 900]，基线在 y_px = 900
→ 8×8 网格，每格 128 px
```

> 两套画框宽度不同（1040 vs 1024），**格号不能跨工具直接对照**。
> 要把预览图里的 `d2` 换算到测量图，先乘 1040/1024 再映射。

---

## 三、看图工具

### 1. `glyph_view.py` — 单字形预览

```bash
# 整字 + 网格
python3 tools/glyph_view.py --font ref/shs/shs-350.otf --glyph 永 --out 永.png --grid

# 只看 d2 到 f3 这一块
python3 tools/glyph_view.py --font ref/shs/shs-350.otf --glyph 永 \
    --out 永_d2f3.png --crop d2-f3 --grid

# 导出 SVG（预览画框，供浏览器查看）
python3 tools/glyph_view.py --font ref/shs/shs-350.otf --glyph 永 --out 永.svg --svg
```

### 2. `glyph_suite.py` — 批量单字形

**每字体 × 每字形 → 一张独立 1024px 图**，并生成逐格墨水占比索引。

```bash
python3 tools/glyph_suite.py \
  --fonts "shs=思源350=ref/shs/shs-350.otf,ops=OPPO=ref/ops/ops-400.ttf" \
  --glyphs 永国回 --outdir /tmp/preview/A
```

产出：

```
A/shs_永.png          整字 + 网格
A/shs_永_index.txt    每格墨水占比
```

索引长这样，用来**定位细节在第几格**：

```
a1=0.00  b1=0.00  c1=0.27  d1=0.26 ...
a2=0.00  b2=0.00  c2=0.02  d2=0.27 ...
```

对比两个字体的索引，**差值最大的格子就是差异所在**，
然后 `--crop` 到那一块放大。

### 3. `hb_render.py` — HarfBuzz 渲染（交叉验证 + 密排）

`hb-view` 直接读字体文件渲染，**不经过浏览器**。两个用途：

```bash
# 交叉验证：SVG 与 hb-view 的墨占比差太多，说明有一边出问题
python3 tools/hb_render.py --out x.png --glyph 永 --size 640 \
  --fonts "s=思源350=ref/shs/shs-350.otf,o=OPPO=ref/ops/ops-400.ttf"

# 密排正文（12–16px）：--glyph 支持多字字符串
python3 tools/hb_render.py --out dense.png \
  --glyph "永和九年岁在癸丑暮春之初" --size 14 \
  --fonts "s=思源350=ref/shs/shs-350.otf"
```

会打印每格图的 `ratio`（墨占比）与 `bbox`，**出现 None 就是该字体缺字**。

---

## 四、测算工具

### 4. `glyph_svg.py` — 单字 SVG（量化测算用）

输出 1024×1024 SVG，**1 设计单位 = 1 像素**，打开就能量。

```bash
# 带网格 + 基准线 + 节点标记
python3 tools/glyph_svg.py --font ref/shs/shs-350.otf --glyph 永 \
    --out 永.svg --grid --refs --points

# 只要坐标文本（不依赖任何渲染环境）
python3 tools/glyph_svg.py --font ref/shs/shs-350.otf --glyph 永 \
    --out 永.txt --coords
```

叠加层含义：

| 元素 | 含义 |
|---|---|
| 浅灰网格 + `a1`…`h8` | 8×8 分区，每格 128 px |
| 红实线 | 基线（y=0） |
| 蓝虚线 | asc 880 / desc −120 |
| 灰虚线 | y=800 参考 |
| 红方块 | on-curve 节点（笔画拐点） |
| 白圈 | 曲线控制点（off-curve） |
| 编号 `0.3` | 轮廓 0 的第 3 个节点 |

`--coords` 每行输出：

```
0.3   (  567.0,  691.0)  px=( 579.0, 209.0)  off ctrl
```

设计坐标 / 像素坐标 / 节点类型。**测算角度、弧度、笔画宽度用这份数据**，
纯文本，不依赖任何渲染环境。

---

## 五、渲染工具（改造用）

| 工具 | 用途 |
|---|---|
| `transforms.py` | 四算子核心：笔画分解、内外侧偏移、中宫调整 |
| `p0_pipeline.py` | VF 重建管线（插值一致性闸门） |
| `canonical_cff.py` | CFF2 输出规范化（避免二次量化） |

> 这三个是**生产工具**，改动会影响出字结果，动之前先跑一遍闸门。

---

## 六、工作流程（推荐）

1. `glyph_suite.py` 批量出图 + 索引
2. 打开 `*_index.txt`，比较两个字体**同一格**的数值
3. 挑差值最大的 2–3 格，`glyph_view.py --crop` 放大
4. 要精确数字 → `glyph_svg.py --coords`
5. 改算子 → 重跑 1

> 意义：**先用数字定位，再用眼睛判断**。
> 反过来（先扫全字再看）会漏掉局部差异，整字缩略图里 10 单位差别看不出来。

---

## 七、已删除的工具

2026-10-23 清理，以下脚本产生的结论全部作废：

| 已删 | 原因 |
|---|---|
| `render.py` / `render_glyph.py` | 早期 LibreOffice/FreeType 路线，已被 SVG 路线取代 |
| `raster.py` | 自写扫描线光栅化，与 rsvg/HarfBuzz 结果不一致 |
| `compare.py` / `specimen.py` | 依赖 `raster.py`，同上 |
| `specimen_html.py` | 浏览器渲染，会静默回退系统字体 → 密排改用 `hb_render.py` |
| `detail_view.py` / `detail_multi.py` | 浏览器 canvas，已被 `glyph_view.py --crop` 取代 |

---

## 八、已知限制

- **画框会裁字**：预览画框 1040 见方，超出 -20..1020 / -140..900 的部分被裁。
  汉字一般不会超出，生僻字可能会有，届时改 `X0/X1/Y_TOP/Y_BOT` 常量。
- 所有工具都要求字体里**真的有这个字形**，缺字直接报错，不静默替换。
- `glyph_svg.py` 的 SVG 里用到 `<text>`，已装 `font-dejavu` + `fontconfig`，
  `rsvg-convert` 能正常渲染（此前是豆腐块）。
