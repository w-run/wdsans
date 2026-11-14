# P112 · 拉丁 advance 基准错配（两处连环 bug）

日期：2026-11-06
状态：已修复并验证

## 症状

拉丁字母 advance 在 7 档字重间**完全不变**（H 恒为 754），
而 Mona Sans 原版 250→900 递增 25（757→782）。

## 根因一：phantom point delta 全为 0

`wds/latin4.py` 的 `merge()`：

```python
d900 = [(hi[i][0]-b[i][0], hi[i][1]-b[i][1]) for i in range(n)] + [(0,0)]*4
d250 = [(lo[i][0]-b[i][0], lo[i][1]-b[i][1]) for i in range(n)] + [(0,0)]*4
```

真Type phantom point 语义：

| 索引 | 含义 |
|---|---|
| n+0 | pp1 左边界 |
| n+1 | pp2 右边界（advance = pp2.x - pp1.x） |
| n+2 | pp3 上边界 |
| n+3 | pp4 下边界 |

代码把 4 个 phantom 的 delta 全设为 0，假设「advance 由 HVAR 提供」。
但 HVAR 里只有中文字形的 advance 数据，Mona 拉丁从未写入 HVAR，
因此拉丁 advance 完全冻结。

**修法**：把 pp2.x 的 delta 写成 advance 差值，pp1.x 保持 0。

## 根因二：基准字重错配

修完根因一后，advance 跨度对了（25），但整体比 Mona 低 10~12。

原因：
- 轮廓取自 `inst_at(MONA, 400, ...)`（Mona wght=400）
- advance 却取自 `m["hmtx"]`（原始表 = Mona **默认字重 200** 的值）

| 项目 | 值 |
|---|---|
| Mona fvar 默认 | wght=200（不是 400） |
| Mona hmtx['A'] | 670（= wght 200 的值） |
| Mona wght=400 时 A | 697 |

轮廓与 advance 基准不一致，整体偏窄 4%。

**修法**：hmtx 改用 `inst_at(MONA, 400, ...)["hmtx"]`（HVAR 应用后的真实值）。

## 验证

```
        250    400    700    900
Mona    757    764    773    782
修复前   754    754    754    754    ← 跨度 0
修复后   757    764    776    782    ← 与 Mona 吻合
```

## 教训

1. **VF 的默认字重不一定等于你要用的字重。** 取实例化轮廓时，
   hmtx 也必须取同一实例的值，不能混用原始表。
2. **phantom point delta 全 0 只在有 HVAR 覆盖时才安全。**
   跨字体合并时必须补写 pp2.x。
3. 「代码改了」≠「行为变了」。本轮第一次修完 advance 从 754 变 747，
   看起来"修好了"，但其实是修错了方向（无 base 对齐），
   必须拿目标值逐档比对才能发现。
