P11：修复静态实例 advance 冻结（instancer 不应用 HVAR）

## 缺陷（实测发现）

七档静态实例的 H advance 全部为 696，完全不随字重变化：
  Thin/Regular/Bold/Heavy 四档 hmtx[H] 与 hb-shape[H] 都是 696
而 VF 真值是 690 / 696 / 706 / 712。

## 根因

deliver.build_static 用 instancer.instantiateVariableFont 生成静态实例。
**instancer 只应用 gvar，不应用 HVAR。**

本字体的约定是：gvar 的 4 个 phantom 点 delta 全为 0（与 Noto 基座一致），
advance 的变化**全部承载在 HVAR 里**。所以 instancer 输出必然拿到默认档的 advance。

这与 P9 里修 VF 时遇到的是同一个坑，只是这次发生在「VF → 静态实例」这一步：
  P9：VF 内部 hmtx/HVAR 不一致（构建时）
  P11：VF → static 时丢掉了 HVAR（导出时）

## 修复

新增 wds/deliver2.py：
  1. 仍用 instancer 取轮廓（gvar 正确应用）
  2. 用 hb-shape 从 VF 测该字重的真实 advance（HVAR 正确应用）
  3. 逐字形回写 hmtx.advance（保留原 lsb）

每档修正 44,806 个字形。

## 验证（hb-shape 实测）

| 档位 | H advance | 目标(Mona×0.895) | 偏差 |
|---|---|---|---|
| Thin 250 | 690 | 690 | 0 |
| Light 300 | 691 | — | — |
| Normal 350 | 694 | — | — |
| Regular 400 | 696 | 696 | 0 |
| Medium 500 | 700 | — | — |
| Bold 700 | 706 | 704 | +2 |
| Heavy 900 | 712 | 712 | 0 |

单调递增 690→691→694→696→700→706→712，A/Á 宽度七档全部一致。

## 结论

这是「同一类坑换个环节再犯一次」。
已确立规则：**任何涉及 advance 的环节，都必须用 hb-shape 验证，不能信 instancer。**

产物 /data/build-cache/wdsans-dist/（7 TTF + 7 WOFF2 + VF WOFF2，重建耗时 2062s）