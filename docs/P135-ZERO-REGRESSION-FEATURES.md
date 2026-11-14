# P135 · 最终方案：17 拉丁特性 + 22 中文特性共存，零退化

日期：2026-11-07
状态：**已解决**。19/19 生效，GPOS/GDEF 完整。

## 我上一轮引入的退化（必须记录）

P134 的方案（纯 feaLib 重建）代价被我低估了。实测：

```
              v8 (P134前)    v10 (P134部署)
GSUB 特性      22 个           17 个
GPOS 特性       8 个            0 个   ← 整个表被删除
GDEF            有             无
。vert 特性     生效            失效
，palt 特性     生效            失效
```

我说「常规横排不受影响」是**错的**：`halt`/`palt` 正是横排标点压缩用的。

## 根因

**`feaLib.builder` 会先删除字体里的 GSUB / GPOS / GDEF，再重建。**
它只重建 FEA 中声明过的东西，所以原有的一切都会消失。

## 正确方案（五步）

```python
# 1. 深拷贝三张表
orig_gsub = copy.deepcopy(f["GSUB"].table)
orig_gpos = copy.deepcopy(f["GPOS"].table) if "GPOS" in f else None
orig_gdef = copy.deepcopy(f["GDEF"].table) if "GDEF" in f else None

# 2. 记录原表每个 script 的「默认可启用」特性 tag 列表
orig_default = {sr.ScriptTag: [orig_tags[i] for i in sr.Script.DefaultLangSys.FeatureIndex]
                for sr in orig_gsub.ScriptList.ScriptRecord
                if sr.Script.DefaultLangSys is not None}

# 3. feaLib 只声明新特性（ss01-ss10 + case）
addOpenTypeFeaturesFromString(f, fea)

# 4. 把原 GSUB 的 Lookup 与 FeatureRecord 合并回新表（索引平移）
base = len(newt.LookupList.Lookup)
for lu in orig_gsub.LookupList.Lookup:
    newt.LookupList.Lookup.append(lu)
old2new = {i: base+i for i in range(len(orig_gsub.LookupList.Lookup))}
for fr in orig_gsub.FeatureList.FeatureRecord:
    nf = copy.deepcopy(fr)
    nf.Feature.LookupListIndex = [old2new[i] for i in nf.Feature.LookupListIndex]
    newt.FeatureList.FeatureRecord.append(nf)

# 5. 恢复 GPOS / GDEF；LangSys 挂「原默认特性 + 新特性」
if orig_gpos: f["GPOS"] = newTable("GPOS"); f["GPOS"].table = orig_gpos
if orig_gdef: f["GDEF"] = newTable("GDEF"); f["GDEF"].table = orig_gdef

for sr in newt.ScriptList.ScriptRecord:
    ls = sr.Script.DefaultLangSys
    idxs = [i for i,tg in enumerate(all_tags)
            if tg in orig_default[sr.ScriptTag] or tg in NEW_TAGS]
    ls.FeatureIndex = idxs
```

### 第 5 步的关键

新特性**必须**挂进 `LangSys.FeatureIndex`，否则 HarfBuzz 不认 `--features=ssNN`。

挂上去**不会**导致它们默认生效 —— HarfBuzz 有内部白名单，
`calt`/`liga`/`ccmp`/`locl`/`kern` 默认开，`ssNN`/`case`/`tnum` 默认关。

我上一轮（v14）之所以把默认数字污染成等宽，是因为把 `aalt` 也塞进了默认集合。
`aalt` 会主动遍历所有替换，把每个字符都换一遍。**只要不碰 aalt 就不会污染。**

## 最终验证

```
GSUB(33): aalt calt case ccmp dlig dnom frac fwid hist hwid liga ljmo locl
          numr pwid ruby ss01-ss10 subs sups tjmo tnum vert vjmo vrt2
GPOS(8):  halt kern mark palt vert vhal vkrn vpal
GDEF:     有

拉丁数字类 6/6  OK
拉丁风格集 11/11 OK
中文 vert   OK   （竖排标点替换）
中文 palt   OK   （横排标点压缩）
中文 vpal   OK   （竖排括号定位，advance -86 -> -40）
默认数字极差 25   （未被污染）
```

## 验证方法学教训

1. **定位类特性（GPOS）只改位置不改 gid**，
   必须比较 advance/offset 而非字形名。
   我一度把 `vpal` 判为 FAIL，实际它正常（`-50,-86` -> `-50,-40`）。
2. **竖排特性要加 `--direction=ttb`**，否则不生效。
3. **「能过 OTS」不等于「行为正确」**，
   必须逐特性做行为对比，且要和改动前的基准比。