# P125 · OpenType 拉丁特性移植：6 成功 / 6 未解决

日期：2026-11-06
状态：6 个特性已实现并验证；6 个（ss 类）未解决

## 已实现且验证生效（6 个）

判据：hb-shape 前后 gid 必须变化（不是只看 advance）。

```
0123456789 + tnum -> 全部 advance=59（等宽）  PASS
1/2        + frac -> gid 变化                   PASS
123        + numr -> gid 变化                   PASS
123        + dnom -> gid 变化                   PASS
123        + sups -> gid 变化                   PASS
123        + subs -> gid 变化                   PASS
```

实现要点：

1. 字形来源：Mona Sans 的 frac/numr/dnom/sups/subs/tnum 变体
2. 存放位置：字体中 1356 个完全未被引用的空槽位（非新增，零风险）
3. tnum 等宽修正：Mona 的 zero.tf=582，其余=593，统一改 593
4. gvar 必须先清再换字形，否则旧 delta 与点数不匹配 -> 反序列化断言失败
5. Mona 的 .tf 是复合字形，必须用 glyphSet + DecomposingRecordingPen 展平

## 未解决（6 个）：ss01 ss02 ss03 ss04 ss05 case

现象：feature 已注册、mapping 正确、已挂到全部 7 个 script 的 DefaultLangSys，
但 hb-shape 指定该 feature 时 gid 不变。

### 已排除的假设（全部被实验证伪）

| # | 假设 | 证伪方式 |
|---|---|---|
| 1 | Coverage 域缺失 | 官方 buildSingleSubstSubtable 同样返回 Coverage=None，
|   |                  | 而 tnum 的 Coverage 也为 None 却正常工作 |
| 2 | FeatureIndex 未排序 | 实测为升序，且无重复 |
| 3 | 源字形解析错误 | 改为 a->b（两者都是已存在的正常字形）仍无效 |
| 4 | 手写 otTables 有误 | 改用官方 otlLib builder 仍无效 |
| 5 | LangSys 未引用新 feature | 确认 latn 的 FeatureIndex 含新增索引，仍无效 |
| 6 | 新槽位字形有问题 | 见假设 3，用原字形同样无效 |

### 关键线索（未验证完）

```
hb-shape --features=ss05       ab -> gid66 gid67   不生效
hb-shape --features=ss05,aalt  ab -> gid59111 gid59112  有变化
```

但 aalt 自身是 type 3 AlternateSubst，其 mapping 含 a -> [uniFF41, glyph63229]。
所以 ss05,aalt 的输出可能是 aalt 的结果而非 ss05 的结果，此线索尚未排除混淆。

## 教训

1. 验证必须用 gid 变化，不能用 advance。数字类特性会因文本含数字而误判成功。
2. 不要用 getattr(subtable, "Coverage") 探测——它是编译期派生字段，
   Python 层拿不到不等于文件里没有。我在这个假信号上浪费了 3 轮。
3. 「结构看起来一致」不等于语义一致。两段 GSUB 在 Python 对象层完全相同，
   行为却不同，说明差异在二进制序列化层面，必须 dump XML/hex 才能看见。