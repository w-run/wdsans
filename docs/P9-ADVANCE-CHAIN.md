P9：advance 链路修复（hmtx base + gvar phantom + HVAR 三处一致）

## 三个叠加的 bug（全部由实测发现）

1. **base advance 取错档位**
   Mona Sans 的默认字重是 wght=200，本产物是 400。
   latin5 用 `m["hmtx"]` 取到的是 Mona **默认实例（200 档）** 的 advance，
   不是 400 档。T 的 base 因此是 576，而 400 档应为约 489。

2. **instancer 读 advance 不应用 HVAR**
   `instancer.instantiateVariableFont` 只应用 gvar，不应用 HVAR：
       instancer  H@900 = 782   vs   hb-shape  H@900 = 796
   因此用它构造的 HVAR delta 一开始就是错的。

3. **HVAR delta 仍是 Noto 的**（doc-sync 队友发现，我复核确认）
   逐字形比对：final 与 Noto 的 HVAR Item 数组完全相同（H/T/o/x/a/n/A/V/W/Y 10/10 相同），
   而 hmtx base 已换成 Mona → 真实 advance = Mona base + Noto delta，两者都不是。

## 一个额外陷阱：gvar phantom 与 HVAR 不能同时写

实测 Noto 基座的约定：**gvar 的 4 个 phantom 点 delta 全为 0，advance 变化只走 HVAR**。
我一度两边都写，结果叠加两次（T 的 advance 在所有字重恒为 592）。
修正为：phantom 归零，只写 HVAR。

## 另一个陷阱：长串 shape 会错位

把多个码位拼成一个字符串用 hb-shape 测，结果按段 zip 回码位列表时，
遇到零宽字形或 mark 合簇会错位。T 因此拿到了 o 的 advance（o 各档恒为 582 → delta 0）。
改为**逐字符单独 shape**。

## 最终验证

逐字符对照 Mona×0.895（H T o x a n A V W Y e w m × 250/400/900 = 39 项）：
**偏差全部为 0，0 项超差。**

回归：结构无丢失、glyph 65535、cmap 44810、GSUB 483/52、GPOS 296/13；
CJK advance 逐字对比完全未变（的一是不国口永 全部 1000）；
粘连测试 18 组（YAW/xxx/Av/Wy/waw/Hamburg × 3 档）全部通过。

## 工具分工（已确立为项目规则）

| 用途 | 工具 | 原因 |
|---|---|---|
| 轮廓几何 / xMin / 点数 | instancer | 应用 gvar，HVAR 与轮廓无关 |
| advance / 字宽 | hb-shape | 应用 HVAR，instancer 不应用 |
| 单字测量 | 逐字符 shape | 长串会因零宽/mark 错位 |

## 产物

/data/build-cache/wdsans-p1/wdsans-FINAL.ttf（= FINAL5，50.3 MB）
新增 wds/advance_fix.py、wds/advance_fix2.py（前者失败版保留记录）