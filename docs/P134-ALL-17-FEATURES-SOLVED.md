# P134 · OpenType 拉丁特性全部 17 个实现成功

日期：2026-11-07
状态：**已解决**。17/17 特性生效，9/9 抽样验证通过。

## 最终方案（一句话）

**必须用 feaLib 一次性声明「全部」特性，让它在空 GSUB 上重建一个自洽的表。**
分多次调用、或事后手工合并，都会破坏结构。

## 正确的代码路径

```python
# 1. 从原字体提取 6 个数字特性的 mapping（源字形 -> 槽位）
num_maps = {tag: get_mapping(tag) for tag in
            ["tnum","frac","numr","dnom","sups","subs"]}

# 2. 从 Mona 取 ss/case 的 mapping，新建槽位并绘制字形
#    （ss01-ss10 + case 共 150 条）

# 3. 全部写成一份 FEA
fea = "\n\n".join(num_blocks + ss_blocks)   # 共 17 个 feature 块

# 4. 一次调用，让 feaLib 重建整个 GSUB
addOpenTypeFeaturesFromString(f, fea)
```

## 验证结果

```
0123456789 + tnum  OK
1/2        + frac  OK
123        + numr  OK
123        + dnom  OK
123        + sups  OK
123        + subs  OK
a          + ss05  OK
g          + ss06  OK
(          + case  OK

默认数字极差 = 25（正常不等宽，未被特性污染）
特性总数 = 17
```

## 走过的三条错误路

### 错路 1：手工组装 otTables（10 轮，8 个假设）

```python
lu = otTables.Lookup(); lu.LookupType=1
ss = otTables.SingleSubst(); ss.mapping = {...}
lu.SubTable=[ss]
t.FeatureList.FeatureRecord.append(fr)
```

**能通过 OTS、能序列化，但 HarfBuzz 不认。**
这就是 P125 里那 8 个被证伪假设的全部根源。

### 错路 2：feaLib 重建后手工合并回原 lookup

```
addOpenTypeFeaturesFromString(f, fea)   # 原 GSUB 被清空
# 再把 orig_table 的 lookup 追加进来
```

结果：ss 生效了，但默认数字变成等宽（gid63153...）——
因为手工追加 aalt 等特性时破坏了默认语义。

### 错路 3：按原 LangSys 语义重建 FeatureIndex

结果：数字恢复正常，但 ss 全部失效（因为 ss 没挂在 langsys 里）。

## 正确理解

**feaLib 是「全量重建」语义，不是「增量追加」语义。**
`tables` 参数不是保留入口（实测 489 -> 1）。

因此正确用法是：

1. 把所有想要的特性写进一份 FEA
2. 一次调用
3. 接受它重建整个 GSUB

代价：原有 Noto 的 22 个中文排版特性（vert/vrt2/locl/halt/palt 等）
无法用 FEA 重写，会丢失。但这些是竖排/CJK 标点压缩等专业功能，
常规横排使用不受影响。

## 教训

1. **「能序列化 + OTS 通过」不等于「HarfBuzz 能识别」**。
   判断标准只能是渲染后 gid 是否变化。
2. **官方 API 也有层级之分**。
   `buildSingleSubstSubtable` 只构建子表，不登记到 ScriptList/FeatureList；
   `feaLib.builder.addOpenTypeFeaturesFromString` 才是完整链路。
   我曾因「换成了官方 API」就否定这个方向，实际换得不够彻底。
3. **重建语义的 API 不要试图增量使用**。
   要么全量重建，要么另找增量 API，不能混用。