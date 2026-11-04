# P7：复合字形内联（修掉「同字母有/无重音不同形」）

> 2026-11-05 · P6 合并后暴露的一致性缺陷。三次尝试，前两次分别撞上「组件没码位」和「numGlyphs 已到上限」两道墙。
> 本文数字全部可复算，命令见 §7。

---

## 1. 结论速览

| 项 | 结果 |
|---|---|
| 缺陷 | P6 之后**同一字母的无重音版是 Mona、有重音版仍是 Noto**，同字母两种字形 |
| 硬约束 | 本字体 `numGlyphs == 65535`（TrueType 上限），**一个新字形都加不了** |
| 采用方案 | **v8 内联**：用 `DecomposingRecordingPen` 把复合字形的组件展开成**单一简单轮廓**，不消耗新槽位 |
| 成功率 | **136 / 136（100%）**，0 跳过 |
| 一致性 | A/Á、a/á、E/É、N/Ñ、o/ö、u/ü **宽度差全部 0.0%**（墨宽与 advance 双重验证） |
| 字重响应 | hb-shape 实测 H 的 advance 663 / 684 / 713 / 730（250/400/700/900），**单调递增** |
| 粘连 | 15/15 通过（YAW / xxx / Av / Wy / waw × 250/400/900，段数 ≥ 字母数） |
| 中文结构 | glyph 65,535、cmap 44,810、GSUB 483 features / 52 lookups、GPOS 296 / 13 —— **全部不变** |
| 产物 | `/data/build-cache/wdsans-p1/wdsans-p8c.ttf`（50.3 MB） |

---

## 2. 缺陷：同一个字母，两种字形

P6 只合并了 Mona 的**非复合**字形（117 个），带重音的复合字形（`Aacute` 等）没搬。
结果是无重音版换成了 Mona、有重音版还是 Noto —— **同一个字母在一个字体里出现两种设计**。

### 2.1 实测（P6 产物 `wdsans-p7-latin-final.ttf`，墨宽 bbox）

| 对照 | 无重音（Mona） | 有重音（Noto） | 差 |
|---|---|---|---|
| A / Á | 569 | 594 | **+4.4%** |
| a / á | 417 | 415 | −0.5% |
| E / É | 448 | 426 | **−4.9%** |
| N / Ñ | 514 | 515 | +0.2% |
| o / ö | 436 | 490 | **+12.4%** |
| u / ü | 390 | 424 | **+8.7%** |

**o / ö 的 +12.4% 肉眼可见**——同一段文字里 ö 比 o 明显胖一圈。

### 2.2 advance 也错（hb-shape 实测，wght=400）

| 对照 | 无重音 | 有重音 |
|---|---|---|
| A / Á | 624 | 608 |
| a / á | 535 | 563 |
| E / É | 558 | 589 |
| N / Ñ | 677 | **723** |
| o / ö | 532 | **606** |
| u / ü | 521 | **607** |

偏差有正有负、量级到 +86 单位 —— 不是统一缩放能修的，**只能让两侧来自同一套轮廓**。

---

## 3. 三次尝试

### v6：按「码位」映射组件 —— 只成功 67/136

**做法**：遍历复合字形的组件引用，按**码位**去 Mona 里找同名组件再导入。

**结果**：v6 只成功 **67 个**，其余 158 个报 `component-missing`。

> 口径澄清（两个数都对，范围不同）：
> - **512** = Mona 全字体的复合字形总数（含希腊/西里尔等，P6 §7 引的是这个数）；
> - **225** = 其中落在**拉丁区**（`≤U+024F` + 标点区）的；
> - **136** = 再筛「我们 cmap 里也有」之后的实际目标数。
>
> 所以**实际目标是 136 个**（latin6 实测 `composite_map${BT} 遍历 225 个、其中落进我方 cmap 的 136 个）。
> 512 / 225 / 136 是三级漏斗，不是三个互相矛盾的数。

**根因**：`i` / `j` / `dieresis` / `cedilla` / `acute` 这些是**纯组件，本身没有码位**。
码位映射表里查不到它们，于是所有引用它们的复合字形全部失败。
**「有码位的字形」和「能当组件的字形」是两个集合，不能拿前者的索引去找后者。**

### v7：按「组件名」导入缺失组件 —— 撞上 numGlyphs 硬上限

**做法**：改用组件**名**解析，把缺的组件从 Mona 逐个导入。

**结果**：直接崩在编译期：

```
struct.error: 'H' format requires 0 <= number <= 65535
```

**根因**：本字体 `numGlyphs` **已经是 65,535**，正好是 TrueType 的 `numGlyphs` 字段上限（`H` = uint16）。
**一个新字形都加不进来** —— 这不是实现 bug，是格式的硬约束。

> 这是本轮最重要的认知：**基座是 65,535 字形的满编字体，任何「新增字形」的方案从第一步就不可能成立。**
> 想扩充组件，只有两条路：削掉别的字形（违反「不删 cmap」铁律），或者**不新增字形**。

### v8：内联（展开组件，零新增槽位）—— 136/136 全成功

**做法**：把复合字形的组件**在绘制阶段就展开**，直接写成一个简单轮廓：

```python
gs  = mona_400.getGlyphSet()
pen = DecomposingRecordingPen(gs)      # 遇到组件自动递归展开
gs[mname].draw(pen)
tp  = TTGlyphPen(None)
pen.replay(TransformPen(tp, Transform(sx, 0, 0, sy, 0, 0)))
glyph = tp.glyph()                     # 单一简单轮廓，numberOfContours > 0
```

**为什么这次成立**：

| 约束 | v8 如何满足 |
|---|---|
| 不能新增字形 | 码位仍映射到**原来那一个**字形，组件被「画进去」而不「引用进来」 |
| 要保住 VF | 在 **250 / 400 / 900 三处展开同一结构**，点数天然一致，再按 P6 的方法重建 gvar deltas |
| 视觉必须与 Mona 一致 | 展开是几何等价变换，轮廓位置一个单位不差（实测 bbox 逐字吻合） |

结果：**136 个复合字形全部成功，0 跳过**；产物中**复合字形数量 = 0**（全部变成简单字形）。

---

## 4. 验证：必须用 hb-shape，不能用 instancer

> ⚠️ **这是本轮最贵的坑，由 verify-latin 队友发现：用 `fontTools` 的 `instancer` 测 advance 会得到错值。**

### 4.1 为什么错

`fontTools.varLib.instancer` 实例化时会：

1. 应用 gvar 的 **phantom 点** delta 到 `hmtx`；
2. **把 HVAR 表整个丢掉**（实例化后的产物表清单里没有 HVAR）。

于是它给出的 advance **只包含 gvar phantom 那一份**，与真实排版引擎的结果不一致。
真实引擎（HarfBuzz）**优先用 HVAR** 算 advance。

### 4.2 实测差异（本字体 `wdsans-p8c.ttf`，字形 H）

| 来源 | wght 250 | 400 | 700 | 900 |
|---|---|---|---|---|
| `instancer` → `hmtx` | 678 | 684 | 694 | 700 |
| **hb-shape（真值）** | **663** | **684** | **713** | **730** |

400 档两者相同（幻影 delta 为 0），**越是极端字重差得越多**：250 档差 −15、900 档差 +30。

### 4.3 正确测法

```bash
hb-shape --variations="wght=900" --no-glyph-names --output-format=json \
         /data/build-cache/wdsans-p1/wdsans-p8c.ttf "Hnoxoa"
# 读每个 run 的 "ax" 字段 = advance
```

**规则**：凡是「测最终用户看到的宽度」，一律 hb-shape。
`instancer` 只适合「测轮廓几何」（点数/坐标/bbox），不适合测 advance。

---

## 5. 结果

### 5.1 一致性（hb-shape 真值，advance）

| 对照 | wght 400 | wght 900 |
|---|---|---|
| A / Á | 624 / 624 → **0** | 676 / 676 → **0** |
| a / á | 535 / 535 → **0** | 578 / 578 → **0** |
| E / É | 558 / 558 → **0** | 599 / 599 → **0** |
| N / Ñ | 677 / 677 → **0** | 718 / 718 → **0** |
| o / ö | 532 / 532 → **0** | 563 / 563 → **0** |
| u / ü | 521 / 521 → **0** | 568 / 568 → **0** |

**全部 0.0%**。墨宽同步归零（P6 的 +4.4% / +12.4% 全部消失）。

### 5.2 字重响应（hb-shape 真值）

**单字独立测量**（无 kerning 干扰，这才是字宽本身）：

| wght | H | n | o | x | a | e |
|---|---|---|---|---|---|---|
| 250 | 663 | 500 | 518 | 451 | 516 | 473 |
| 400 | 684 | 521 | 532 | 495 | 535 | 492 |
| 700 | 713 | 552 | 552 | 559 | 562 | 519 |
| 900 | 730 | 569 | 563 | 595 | 578 | 534 |

**单调递增，无冻结**（P6 v4 那个「250 和 900 都是 675」的死值已彻底解决）。

> 口径提醒：把 `"Hnoxoa"` 整串 shape 会叠上 kerning，
> 得到的 x 是 438/476/532/563 而非上表的 451/495/559/595。
> **测「字宽」用单字，测「排版效果」用整串**，两者不能混着比。

### 5.3 粘连（段数 ≥ 字母数才算不粘）

```
YAW  250/400/900 → 3/3  OK      xxx  250/400/900 → 3/3  OK
Av   250/400/900 → 2/2  OK      Wy   250/400/900 → 2/2  OK
waw  250/400/900 → 3/3  OK      合计 15/15
```

### 5.4 结构零损失

| 检查 | 结果 |
|---|---|
| numGlyphs | 65,535（未增未减） |
| cmap | 44,810（未增未减） |
| GSUB | 483 features / 52 lookups —— 不变 |
| GPOS | 296 features / 13 lookups —— 不变 |
| 复合字形数 | **0** |
| 拉丁区总覆盖 | 253 个槽位：**252 个已来自 Mona**，1 个（`periodcentered`）仍为 Noto，2 个空白（`space`） |

---

## 6. 已知限制（重要，下一轮必须处理）

1. **HVAR 仍是 Noto 的旧数据 —— 最终 advance 被它覆盖，最高偏 +45 单位。**
   实测：本字体 HVAR 的 advance delta 与合并前 Noto **逐字形完全相同**（抽样 200 个全等），
   而 `hmtx` base 已经换成 Mona 值。真实渲染 = Mona base + **Noto 的 delta**：

   | 字形 | base(Mona×0.895) | HVAR 后 @900 | 应为(Mona@900×0.895) | 误差 |
   |---|---|---|---|---|
   | H | 684 | 730 | 700 | **+30** |
   | T | 576 | 617 | 572 | **+45** |
   | W | 890 | 947 | 915 | +32 |
   | o | 532 | 563 | 539 | +24 |
   | i | 215 | 261 | 271 | −10 |

   `wds/hvar_fix.py` 已经把修复函数（按 Mona 250/900 采样重建 HVAR delta）写好了，
   **但没有任何构建脚本调用它**（`grep -r rebuild_hvar` 只有定义处）。
   → 必须接进构建，否则拉丁的 advance 曲线既不是 Noto 也不是 Mona。
2. **无视觉验收图** —— 与 P6 同，仍只有量化。AGENTS.md 铁律 6 未满足。
3. **`OS/2.sxHeight` 仍 543 / `sCapHeight` 仍 733** —— 与实测拉丁 529 / 732 不符（P6 §7-4 未动）。
4. **OFL 署名仍缺** —— name ID 0 无 GitHub（Mona）版权声明（P6 §7-3 未动）。
5. **`wdsans-dist` 未从本产物重出** —— 七档 TTF/WOFF2 还是合并前的（拉丁 H 墨宽 520 = Noto 原样）。
6. **`periodcentered` 未合并** —— 253 个槽位里唯一一个仍是 Noto 的拉丁标点（取整误差导致匹配失败，见 P6 §6.3）。

---

## 7. 复算命令

```bash
cd /workspace/wdsans
P=/data/build-cache/wdsans-p1/wdsans-p8c.ttf

# 1) 一致性：无重音 / 有重音 的 advance 必须相等（hb-shape 真值）
for pair in "A:Á" "a:á" "E:É" "N:Ñ" "o:ö" "u:ü"; do
  a=${pair%%:*}; b=${pair##*:}
  ra=$(hb-shape --variations="wght=400" --no-glyph-names --output-format=json $P "$a" |
       grep -o '"ax":[0-9]*' | cut -d: -f2)
  rb=$(hb-shape --variations="wght=400" --no-glyph-names --output-format=json $P "$b" |
       grep -o '"ax":[0-9]*' | cut -d: -f2)
  echo "$a=$ra  $b=$rb"
done

# 2) 字重响应必须单调
for w in 250 400 700 900; do
  echo -n "wght=$w: "
  hb-shape --variations="wght=$w" --no-glyph-names --output-format=json $P "Hnoxoa" |
    grep -o '"ax":[0-9]*' | tr '\n' ' '; echo
done

# 3) 对照：instancer 给的 advance 与上面不一致（证明不能用它测 advance）
./venv/bin/python -c "
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
for w in (250, 400, 900):
    f = instancer.instantiateVariableFont(TTFont('$P'), {'wght': w},
          inplace=True, updateFontNames=False, optimize=False)
    print('instancer wght', w, 'H adv', f['hmtx']['H'][0])
    print('   tables:', 'HVAR' in f, '(False = HVAR 被丢弃)')
"

# 4) 结构：复合字形必须为 0
./venv/bin/python -c "
from fontTools.ttLib import TTFont
f = TTFont('$P', lazy=True)
print('composites:', sum(1 for n in f.getGlyphOrder()
                         if f['glyf'][n].numberOfContours < 0))
print('glyphs', len(f.getGlyphOrder()), 'cmap', len(f.getBestCmap()))
"
```

---

## 8. 下一轮

- [ ] **接上 `wds/hvar_fix.py`**（当前最关键：拉丁 advance 被 Noto 旧 delta 污染，误差最高 +45）
- [ ] 出中英混排样张 + 12px 正文，**实看**（P6/P7 都欠这张图）
- [ ] `OS/2.sxHeight` → 529、`sCapHeight` → 732
- [ ] name ID 0 补 GitHub / Adobe 双版权（OFL）
- [ ] 从 `wdsans-p8c.ttf` 重跑七档静态 + WOFF2，regen `wdsans-dist`
- [ ] 补齐 `periodcentered`
- [ ] G3/G4 闸门纳入拉丁段

---

## 9. 方法论收获

**三条，都是本轮被墙撞出来的：**

1. **组件解析必须按「名字」，不能按「码位」。**
   `i`/`acute`/`dieresis` 是纯组件、无码位。用码位索引去查组件，158 个复合字形直接查不到。
   两个集合不等价，这个错误在数据上表现成「神秘缺失」，不看组件表根本想不到。

2. **先查 `numGlyphs`，再设计「导入」类方案。**
   `struct.error: 'H' format requires 0 <= number <= 65535` 这条报错本身完全没提「字形满了」，
   只说了字段溢出。**65,535 是满编字体，任何「新增字形」的路线在第一步就不成立**——
   正确方向只有「内联（展开、复用同一槽位）」。

3. **测 advance 必须用 hb-shape。**
   `instancer` 会丢掉 HVAR，只算 gvar phantom，极端字重差 15–30 单位。
   而且它会**静默给出一个自洽的错值**——单看 instancer 的数字，曲线是单调的、看着完全正常。
   这类「工具本身说谎」的坑，只有拿第二个独立工具（HarfBuzz）交叉验证才能发现。

> 这条与 P3/P4/P6 的教训连成一条线：
> **P3** 目视会看出不存在的特征；**P4** 推理会被实测推翻；**P6** 单档渲染看不出 VF 丢失；
> **P7** 连测量工具本身都可能给出自洽的错值。
> 结论不是「不要相信工具」，而是**任何关键数字都要有第二个独立来源**。
