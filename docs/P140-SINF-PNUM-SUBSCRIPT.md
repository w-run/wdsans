# P140 · 补齐 OPPO/HOS 有而我们缺的特性（sinf / pnum / 下标数字）

日期：2026-11-07
状态：已实现并验证，22/22 通过。

## 发现方法

对比四款字体的 OpenType 特性集合，取差集：

```
         GSUB  GPOS
ours      33     8
OPPO      16     3   缺: ordn pnum sinf / mkmk
HOS       21     3   缺: ordn pnum sinf / mkmk
Noto      16     8   缺: 无
```

**我们完整继承了 Noto 的全部特性，但 OPPO/HOS 额外有三个：**

- `ordn` 序数词
- `pnum` 比例数字
- `sinf` 科学下标

## 深挖后发现两个真实缺陷

### 1. `ordn` 是空特性（不是缺陷）

```
OPPO  ordn    0 条
HOS   ordn    0 条
```

两家都注册了 `ordn` 但没有任何映射。**这不是我们需要补的。**

### 2. U+2080-2089 下标数字完全缺失（真实缺陷）

```
ours   U+2080 -> 缺失 ... U+2089 -> 缺失
OPPO   U+2080 -> uni2080 ... U+2089 -> uni2089
```

这是 cmap 缺字，不是特性问题。H₂O 这类文本会显示为缺字方框。

## 修复方案

### 下标数字：复用已有字形

我们已有 `subs` 特性生成的 10 个下标字形槽位（glyph61870 等）。
把它们同时挂到 cmap 的 U+2080-2089 即可，**不新建字形**。

```python
for i, d in enumerate(DIG):          # zero..nine
    target = subs_map[d]             # 复用 subs 的目标字形
    for ct in cmap_tables:
        if ct.isUnicode() and ct.format in (4,12):
            ct.cmap[0x2080+i] = target
```

新增 40 个 cmap 条目（4 张子表 x 10 码位）。

### sinf：数字 -> 下标字形

```fea
feature sinf {
    sub zero by glyph61870;
    sub one  by glyph61871;
    ...
} sinf;
```

### pnum：等宽槽位 -> 默认数字（反向）

OPPO 的 pnum 是 `zero.tf -> zero`（默认等宽，pnum 恢复比例）。
我们默认就是比例宽度（极差 25），所以：

```fea
feature pnum {
    sub glyph13852 by zero;   # tnum 槽位 -> 默认数字
    ...
} pnum;
```

这样 `tnum,pnum` 组合能回到比例宽度，行为正确。

## 验证

```
GSUB(35) GPOS(8) GDEF=True

拉丁 19 项（17 原有 + sinf + pnum）  全部 OK
中文 3 项（vert/palt/vpal）          全部 OK
默认数字极差 25（未被污染）
下标数字 H2O: gid41 + gid61896 + gid48  ✓
OTS: PASS

总计 22/22
```

## 教训

**「对比特性标签集合」只能发现线索，不能确认缺陷。**

`ordn` 在标签层面看是「OPPO/HOS 有而我们缺」，
但实际查映射是 0 条 —— 纯粹的空注册。

真正的缺陷是 **U+2080-2089 cmap 缺字**，
这个在特性对比里完全看不出来，
必须查 cmap 才能发现。

所以完整的对齐检查应该是三层：
1. 特性标签集合（发现线索）
2. 特性的实际映射条数（排除空注册）
3. cmap 码位覆盖（发现缺字）