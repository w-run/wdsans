# P113 · 【已撤回】GPOS lookup 类型"损坏" —— 实为 Extension 合法解包

日期：2026-11-06
状态：**误判，已撤回。原结论错误。**

## 我错了什么

上一版本文档声称：`thin_proportional_hv` 破坏了 GPOS，
palt/vpal 从 type 9 降为 type 1 是"数据被误读"。

**这个判断是错的。**

## 真实情况

```
Noto 原始 palt: lookup[7] type=9
    sub[0] class=ExtensionPos
        ExtSubTable class=SinglePos
        ExtensionLookupType=1
```

OpenType 的 **Lookup Type 9 (Extension)** 本身就是一个转发壳：
它的子表只存「真实 lookup 类型 + 偏移」。
Noto 用 type 9 包装 SinglePos，仅仅是为了突破 16 位偏移上限
（palt 有 11 个子表，数据超过 65535 字节）。

fontTools 的 instancer 在实例化时**自动把 Extension 解包**：
type 9 + ExtSubTable(SinglePos) → type 1 + 11 个 SinglePos 子表。

**这是语义完全等价的合法优化，不是损坏。**
子表数量变化也印证了这一点：

| Lookup | Noto | v5 | 说明 |
|---|---|---|---|
| palt | t9, 11 子表 | t1, 11 子表 | 子表数不变，只是解包 |
| vpal | t9, 10 子表 | t1, 10 子表 | 同上 |
| vkrn | t9, 1 子表 | t2, 1 子表 | 解包后是 PairPos |

## 我的"修复"造成的实际损害

我把 Noto 的 GPOS **整表移植**进静态档，并连带移植了 GDEF。
但 Noto 的 GDEF 含 **ItemVariationStore**（可变字体专用），
而静态档**没有 fvar 表** —— 两者矛盾，字体结构被破坏：

```
ERROR: Variations: Required fvar table is missing
ERROR: Variations: Failed to parse variation region list
ERROR: GDEF: Invalid item variation store
```

OTS 结果对比：

```
v5 (未"修复"): pass=15 fail=0    ← 本来就对
v6 (我"修复"): pass=1  fail=14   ← 被我弄坏
```

## 教训（比原结论重要得多）

1. **内部表示 ≠ 文件表示。**
   fontTools 加载后看到的 LookupType 是解包后的语义类型，
   不能直接和原始二进制里的类型号比较。
   我用"类型号变了"推断"数据损坏"，是拿表示层当语义层。

2. **差异必须区分「等价变换」与「真实损坏」。**
   判据应该是：子表数量、子表语义、以及**渲染结果**是否一致，
   而不是 lookup 类型号是否逐字相同。

3. **移植整表前必须检查表间依赖。**
   GDEF 可以被 GPOS 引用，但 GDEF 自身还依赖 fvar。
   给无 fvar 的静态档塞进带 ItemVariationStore 的 GDEF = 必坏。

4. **"闸门通过"和"OTS 通过"都不能证明我改对了。**
   v5 一直是 15/15 通过，我却去"修"它，修完变成 1/15。
   改动前应先确认原状态是否真的有问题。
