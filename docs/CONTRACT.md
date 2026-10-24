# 双产物契约（A 静态族 / B 可变字体）

> 目标：**一套参数 → 两套产物 → 调用方可替换**。
> 本文是这条路的唯一权威。与 DESIGN.md 冲突时，设计细节看 DESIGN.md，接口/验收看本文。

---

## 0. 为什么必须分两个后端

| | **A · gfx 后端** | **B · nodes 后端** |
|---|---|---|
| 字形来源 | glow-sans CV 管线（栅格化 → 骨架 → **重描边**） | 思源黑 VF master **节点位移** |
| 输出 | 7 个静态字体 | 单个 VF |
| 跨档拓扑 | 各档独立生成（实测仅 6.2% 一致） | 天然一致（插值成立） |
| 交付速度 | 快（产物已在） | 慢（数周） |
| 用途 | Web/App 立即上线、VF 失败时兜底 | 真可变、连续轴、单一文件 |

**结论：VF 不可能由 gfx 后端产出。** 重描边意味着每档轮廓点数由图像分割决定，跨档必然漂移——这不是精度问题，是方法问题（POSTMORTEM 1.1）。所以两条腿必须分开走，共享的只能是**参数、度量、特性表**，不能共享字形实现。

A 与 B 的同档字形**必然有差异**。契约定义的是「允许差多少」，不是「必须一样」。

---

## 1. 共享层（唯一真源，两个后端都读）

```
contract/
  axis.json       轴定义
  metrics.json    排版度量目标
  features.json   特性表来源与白名单
params/
  design.tsv      语义参数（10 项左右，人工维护）
  derive.py       语义参数 → 81 档数值（确定性，无随机）
```

### 1.1 axis.json

```json
{
  "family": "WDesign Sans",
  "upm": 1000,
  "axes": [
    {"tag": "wght", "min": 250, "max": 900, "default": 400,
     "stops": [250, 300, 350, 400, 500, 700, 900],
     "names": ["Thin","Light","Normal","Regular","Medium","Bold","Heavy"]}
  ]
}
```

- stops 顺序即 `usWeightClass` 取值，两套产物**必须完全一致**
- B 的 `fvar` instance 与 A 的 7 个文件一一对应
- 预留 `wdth` 轴位；A 现阶段只有 width=100，B 的首版也只做 wdth=100

### 1.2 metrics.json

| 项 | 值 | 来源 |
|---|---|---|
| upm | 1000 | SHS |
| cap height | 733 | 与中文对齐（DESIGN §5） |
| x-height | 529 | Mona 原值 × 1.0055（不拉齐思源 543） |
| typo asc/desc/gap | 880 / -120 / 0 | SHS |
| win asc/desc | 1160 / 288 | SHS |
| hhea asc/desc/gap | 1160 / -288 / 0 | 现有 7 档实测已统一 |
| vhea | 与 SHS 一致 | — |

现有 7 档产物在上表除 cap/x-height 外**已经统一**，可直接沿用。

### 1.3 参数层重构（关键）

**当前状态的问题**（实测 `parameters/normal.tsv`）：

| 现象 | 数据 | 后果 |
|---|---|---|
| `weight` 曲线非单调 | 0.82 → 1.08 → 0.92 → 0.88 → 1.08 → 0.96 → 0.98 → 0.95 → 1.05 | 逐档人肉凑数，200 和 500 都跳 1.08 |
| 源字重索引复用 | `shs: 0,0,1,2,3,4,5,6,6` | 100 和 200 用同一个源字重 |
| 全档硬编码 | `latinscale` 1.08、`baseline` 120、`flattenends` 0.75、`endsremoval` TRUE | 旧版「全局 45° 斜切」与「cap 784」的直接来源 |
| 81 个 JSON 手填 | `parameters/glow/*.json` 47 个 + 其余宽度系列 | 改一个设计决策要同步 81 处，必然漂移（旧版：参数写 `raleway`，产物是 Mona） |

**新做法**：只维护语义参数 + 派生规则，81 档由脚本生成，且生成结果进 git（可 diff、可复现）。

```toml
# params/design.toml（示意）
[weight]                    # 字重补偿：单调、连续、可解释
formula = "1.0 + 0.06 * tanh((w - 400) / 180)"   # 形状待标定，不手填
[counters]                  # 中宫：基准档 + 线性斜率
at_400 = 0.960
per_100 = -0.003
[hooktension]               # 笔钩张力
at_250 = 0.40
at_900 = 0.70
[ends]
flattenends = 0.0           # 目标值 = 不额外生出角（DESIGN §4.1）
endsremoval = false
[latin]
source = "mona"
cap_target = 733
xheight_target = 529
```

**硬约束**：任一派生曲线必须单调或单峰，不许出现「相邻档反向折返」。这条能自动校验——曲线不合法直接构建失败。

---

## 2. Mona Sans 适配（gfx 后端）

glow-sans 的拉丁是**预采样 JSON**（`samples/Raleway-v4020-*.json`，约 39KB/档），build 时直接读轮廓、不经 CV。所以加 Mona **不用碰字形核心**，只加采样入口。

### 2.1 改动清单

| # | 文件 | 改动 |
|---|---|---|
| 1 | `scripts/sample-mona.js`（新增） | 由 `sample-raleway.js` 派生，约 30 行 |
| 2 | `encoding/cmaps/mona.json`（新增） | 拉丁 cmap → gid 映射 |
| 3 | `src/font-build/res/params.js` | typedef 增加 `latin?: {source, wght}`，保留 `fira`/`raleway` 兼容 |
| 4 | `parameters/*.tsv` | `fira` 行 → `mona` 行，值改为 **wght 轴值**（不是 gid 索引） |
| 5 | `src/font-build/res/features.js` | 白名单补 `case` / `calt` / `tnum`（DESIGN §6 要求数字、冒号居中） |
| 6 | `package.json` | 新增 `sample-mona` 脚本 |

### 2.2 四个必须处理的坑

1. **数字 gid 硬编码**：`sample-raleway.js` 里有
   `if (char >= '0' && char <= '9') gid = 'glyph' + (726 + parseInt(char))`
   这是 Fira/Raleway 的 dump 序约定。Mona 必须走 `font.cmap['U+0030']`，否则数字全错且**不会报错**。
2. **Mona 只发 VF**：`MonaSansVF[wdth,opsz,wght].ttf`。采样前必须先实例化：
   `fonttools varLib.instancer -o out.ttf MonaSansVF.ttf wght=<w> wdth=100 opsz=<默认>`。
   三个轴都要定，否则 opsz 会随默认值漂移，字重采样出来不是设计值。
3. **cap 与 x-height 不能靠单一 scale 同时满足**：
   - cap 对齐：733 / 729 = **1.0055**
   - x-height 对齐：529 / 517 = **1.0232**
   - 单一 `latinscale = 1.08`（旧值）两项都超，cap 冲到 784。
   → 拆分两个参数：`latin_cap_scale` 走横向+纵向整体，`latin_xh_bias` 只对 x-height 区做纵向补偿。
   不能同时对齐时**以 cap 为准**，x-height 差额记录在样张里人工确认。
4. **`latinscale` 是源相关的绝对值**：换拉丁源必须重算，不能沿用 1.08。这条要写进构建断言——`latinscale` 与 `latin.source` 绑定校验，源变了值没变就直接报错。

### 2.3 Mona 的 `wdth` 轴

glow 的宽度系列（compressed/condensed/normal/wide/extended）与 Mona 的 wdth(75–125) 不是一一对应。首版**只锁 wdth=100**，宽度系列留到 VF 阶段统一处理，避免两条轴互相干扰。

---

## 3. 调用方接口（"能替换"的定义）

### 3.1 元数据必须先修（实测问题）

现有 7 档的 name 表是**分裂**的：

| 文件 | nameID 1 | nameID 2 | nameID 16/17 |
|---|---|---|---|
| Thin / Light / Normal / Medium / Heavy | `WDesign Sans Thin` 等 | `Regular` | 有（16=`WDesign Sans`） |
| Regular / Bold | `WDesign Sans` | `Regular` / `Bold` | **缺** |

后果：现代应用/浏览器会把 `WDesign Sans` 当成只有 Regular+Bold 两档的家族，其余 5 档是「别的家族」——`font-family:"WDesign Sans"; font-weight:300` **匹配不到**。这直接破坏 A 的可用性。

必修：
- nameID 1 = `WDesign Sans`（除 Regular/Bold 外可用 legacy 名，但必须成对一致）
- nameID 2 = 档名（`Thin`/`Light`/…）
- nameID 16 = `WDesign Sans`，nameID 17 = 档名，**7 档全部补全**
- 新增 **STAT** 表（现有 7 档没有），声明 wght 轴与 7 个命名实例
- `fsSelection` 保持位 7 (USE_TYPO_METRICS) 一致

### 3.2 CSS 契约

```css
/* 两套产物共用这一段，只换 @font-face 源 */
.wdsans {
  font-family: "WDesign Sans", system-ui, sans-serif;
  font-synthesis: none;   /* 必须：否则 A 下浏览器会给 Thin 假加粗，与 B 不一致 */
}
```

- A：7 个 `@font-face`，各自 `font-weight: 250 250` 等单点区间；`font-weight: 375` 由 CSS 就近匹配
- B：1 个 `@font-face` + `font-weight: 250 900`；`375` 精确插值
- **切换只改一个 CSS 文件，调用方零改动**；视觉差异 = 「就近档」vs「精确插值」

#### 实测结论（2026-10-24，WebKit）

CSS Fonts 4 §5.2 的匹配规则**不是"就近"**：

| 请求 | 实际命中 | 方向 |
|---|---|---|
| 325 | 300 | 小于 400 → 向下取档 |
| **375** | **350** | 向下 |
| 450 | 500 | 400–500 区间 → 向上 |
| 600 | 700 | 大于 500 → 向上 |

后果：**A 的中间值永远偏向"薄的一侧"（<400）或"厚的一侧"（>500），不会落在中间。**
所以 A 只能承诺 7 个离散档位；一旦调用方使用任意 weight，A 与 B 的视觉差异会明显到不可忽略。
→ 这是 A 不能替代 B 的硬边界，也是必须做 B 的理由。

---

## 4. OpenType 特性保留

实测 7 档产物：

| 表 | 结论 |
|---|---|
| GSUB | **字节级完全相同**（11 lookups / 10 features / 仅 DFLT script）→ 取一份 |
| GDEF | 完全相同（1112 base / 95 lig / 11 mark）→ 取一份 |
| cmap | 完全相同（31914 字形）→ 取一份 |
| GPOS | 结构相同，仅 `palt`/`vpal` 的 coverage 差 1–10 个字形（Thin 138 vs Regular 137；Heavy 298 vs 288）→ **锁 Regular 一套** |
| OS/2 | 各档不同，正常（字重参数） |

### 4.1 三条闸门

1. **构建前 diff**：字节 hash + 语义指纹（lookup type / format / coverage 数量 / feature→lookup 索引），白名单只放行 `palt`/`vpal` coverage 与 OS/2。白名单外差异 → 构建失败。
   > `varLib.build` 会**静默丢弃**非 base master 的 GSUB/GPOS/GDEF，不报错。这道闸门就是防这个。
2. **构建后断言**：GSUB / GPOS / GDEF / BASE / vhea / vmtx / STAT / fvar 都在；instance 数与 stops 一致；name 表 instance 名完整。
3. **行为级回归（唯一算数的标准）**：`hb-shape` 跑固定语料 × 每个 instance，与对应静态字体逐字节比对。语料必须覆盖：
   - 竖排：`vert` / `vrt2` / `ruby`
   - 全半角：`fwid` / `hwid` / `pwid` / `halt` / `palt`
   - 替代：`aalt` / `ccmp` / `liga` / `dlig`
   - 定位：`kern` / `vkrn` / `vhal` / `vpal`
   - 已知限制：VF 里 GPOS 的 XAdvance **不能随轴变化**，`palt`/`vpal` 只能锁一档。这是 OpenType 固有限制，思源黑 VF 同样如此。

---

## 5. 等价性验收（A ↔ B 可替换的硬保证）

| 层级 | 判据 | 阈值 |
|---|---|---|
| 结构 | 同 stop 的字形轮廓数、绕向、bbox 一致 | **必须全等** |
| 几何 | 轮廓面积比、墨量、笔画宽、cap/x-height | 面积差 ≤ 2%，笔画宽差 ≤ 1.5% |
| 渲染 | 12/16/24/48px 同字同尺寸像素 diff | ≤ 3% 偏差像素，差异需人看 top-20 字形 |
| 行为 | `hb-shape` 输出 | **必须逐字节相同** |
| 度量 | hmtx advance 全表 | 差 ≤ 1% 的字形占比 < 0.1% |

阈值不是拍脑袋：A 是 CV 重描边，±1 单位抖动是方法自带的；B 是位移，理论上应严格一致。**B 内部的一致性要求严格，A↔B 之间按上表放宽。**

---

## 6. 阶段

| 阶段 | 内容 | 产物 | 环境 |
|---|---|---|---|
| **P0 ✅** | 契约 + 轴/度量冻结 + name/STAT 修复（2026-10-24 完成） | `contract/*.json`、`tools/fix_meta.py`、`build/meta/*.ttf`、`build/preview.html` | iSH |
| **P1** | gfx 后端接 Mona：采样脚手架 + 1 档（400/normal）跑通 | 单档样张 | CloudStudio |
| **P2** | 参数层重构（语义参数 → 7 档派生）+ 7 档重出 | A 交付：TTF/WOFF2 + CSS + demo | CloudStudio |
| **P3** | nodes 后端出 VF，跑 §4/§5 闸门 | B 交付 | CloudStudio / iSH |
| **P4** | A↔B 等价性比对、替换测试 | 双产物发布 | — |

### P0 验收记录（2026-10-24）

- `fix_meta.py` 处理 7 档，**31,916 字形坐标零差异**、`glyf`/`loca`/`hmtx`/`vmtx`/`GSUB`/`GPOS` 字节长度不变
- `cmap` 重编译后编码差 256 字节，**映射内容逐条相同**（32089 条，子表结构一致）
- name 1/2/16/17 全部补全，name 5 的 `FontCreator 15.0.0.2927` 指纹已抹除
- STAT 注入成功：wght 轴 + 7 个命名实例，Regular 带 elidable 标志
- `fc-scan` 确认 7 个文件归入同一家族 `WDesign Sans`，style 各为 Thin/Light/Normal/Regular/Medium/Bold/Heavy
- 浏览器实测 7 档按 weight 正确匹配（见 §3.2 实测结论）

### 环境约束（实测）

glow-sans 依赖 `opencv-python 3.4.7` / `scikit-image 0.14.2` / `numpy 1.17.2` / `canvas`(native) / `otfccdump`：

- **iSH 跑不了**（musl aarch64 没有对应 wheel，canvas 需 cairo 原生编译）
- **w-box 不借用**（其他项目占用中）
- **CloudStudio 是当前选择**：腾讯云工作空间，x86_64，按规格可选 4C8G/8C16G；需在其中用 **Docker 锁 python 3.7 旧环境**，否则 opencv 版本变化会让 CV 分割结果漂移，破坏「同参数 → 同产物」
- 存储不是瓶颈（iSH 侧 `/var/minis` 有 593GB 可用），瓶颈只有 CPU 架构与依赖版本

---

## 7. 已决与待决

**已决（2026-10-24）**

- [x] **严格 7 档**，不引入 ExtraLight(200)
- [x] glow-sans **独立维护**（上游已停更，不跟随）
- [x] 构建环境走 **CloudStudio**（w-box 被其他项目占用）
- [x] `wdth` 轴首版不上，锁 100

**待决**

- [ ] A 交付是否需要 woof2 分片（按 `unicode-range`：GB2312 / 常用扩展 / 全字集）——影响首屏策略
- [ ] `useTypoMetrics`（fsSelection bit7）是否开启：开 → 行高 = 1.0em 更可控；关 → 保持现有行为（win 1160/288，行高 1.448em）。两套产物必须一致，选了就不能单边改
- [ ] 版本号策略（现暂用 `0.9.1`，是否沿用 `YYYY.NNN` 旧格式）
- [ ] CloudStudio 用现成的 `mkit-build-2`（4C8G，已存在、STOPPED）还是新建专用工作空间
