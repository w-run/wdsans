# WDesign Sans · 存档 v261122

日期：2026-11-19
链尾：masters_R37（R36 + m_fbclean），VF 后处理 m_fbclean2
状态：已部署，审计 38 项全通过

---

## 文件

```
WDesignSans-VF.otf               41,335,040 B  cc5b2581...
WDesignSans-FlatApex-Regular.otf 17,915,104 B  846761db...
wd-preview.woff2                  2,247,524 B
wd-poster-vf.woff2                  249,668 B
wd-poster-flat.woff2                127,680 B
masters/ 三档（R37）
```

校验：md5sum -c MD5SUMS.txt（8/8 通过）

---

## 本轮修复（fontbakery 驱动）

### 五处问题，全部由专业工具指出

```
FAIL opentype/font_version   head=2.00499 vs name=Version 1.000
FAIL base_has_width          uni20DD/uni20DE advance=0 被当基底字符
WARN gdef_mark_chars         20+ 组合符号未在 GDEF mark class
FAIL inconsistencies_between_fvar_STAT  9 instance 无 STAT 条目
FAIL no_mac_entries          name 表有 20 条过时 Mac(platform 1) 记录
```

### 修 1 版本号（head 表漏改）

```
m_nametable 只改了 name ID5，漏改 head.fontRevision（仍是 SHS 的 2.00499）
-> head.fontRevision = 1.000
```

### 修 2 GDEF mark class（SHS 继承缺陷，只有 4 个 glyph）

```
这导致 base_has_width 误报:
  uni20DD 是 COMBINING ENCLOSING CIRCLE，advance 本来就该 0
  但不在 mark class -> 被按「基底字符」检查 -> 报零宽错误

修: 按 unicodedata.category 补全
  Mn (非间距) 28 个  -> 标
  Me (包围)    2 个  -> 标
  Mc (间距)    2 个  -> 不标（U+302E/302F 是韩文声调符，adv=250）
  结果 mark 4 -> 30

🔴 迭代: 初版按 Mn/Mc/Me 全标 -> mark=32，fontbakery 立刻报 2 个新 WARN
  gdef_non_mark_chars / gdef_spacing_marks 都指向 U+302E/U+302F
  修正为只标 Mn+Me -> mark=30 -> WARN 消失
```

### 修 3 STAT 表（真实缺陷，影响所有应用）

```
fvar: 9 个 instance（250/300/350/400/500/600/700/800/900）
STAT: 只有 1 个 AxisValue，且 Format=2 无 Value 字段
-> 9 个 instance 全无对应条目，应用读 STAT 无法识别字重名称

修: 为每个 instance 建 Format 1 的 AxisValue，按 AxisIndex+Value 排序
结果 STAT 1 -> 10
```

### 修 4 Mac name 记录（我们引入的）

```
name 表有 20 条 platformID=1（Mac）记录
来源: bvf 脚本里写了 [(3,1,0x409),(1,0,0)] —— 自己加的
SHS 原版只有 platformID=3
fontbakery: Mac 记录已过时，OpenType 规范建议仅用 platform 3
修: 删除所有 platformID=1
```

### 修 5 🔴 回归: zh-CN name 记录全部丢失

```
R37 部署版只有 (1,0x000)+(3,0x409)，zh-CN 0 条
SHS 原版有 3 条 zh-CN

AGENTS.md 早就记录「VF 构建会丢弃 zh-CN，必须 post_vf_name2 修复」，
但 bvf_r37.py 里自写的 name 替换没有加 0x804 -> 回归。

修: 从 master 复制 zh-CN 的 nameID 1/2/4/16/17
    🔴 nameID17 在 master 里是 ExtraLight，必须强制改 Regular
结果 zh-CN 0 -> 5 条
```

---

## 验证

```
三项修复:
  STAT 1 -> 10    name平台 [1,3] -> [3]    zh-CN 0 -> 5    nameID17 = Regular

关键不变项（不能回归）:
  head.rev=1.000  OS/2 v4  GDEF mark=30  glyphs=65535  cmap=45012

HarfBuzz shaping 一致性（R37 vs R38，11 项）:
  永国字体 / 0123456789 / 设置·消息 / Hamburgefonstiv /
  b+acute / d+acute / g+tilde / 一+acute / 12:34 / a:b / 1/2
  -> 0 项不同

fontbakery: FAIL 3 -> 1（只剩 file_size）
            WARN 6 -> 5
```

---

## 剩余 fontbakery 提示（全部不可修）

```
FAIL file_size            CJK 字体 41MB，9MB 限制面向拉丁，不适用
WARN post_table_version   format 3 对可搜索 PDF 有小众影响，CFF2 必需
WARN cjk_chws_feature     缺 chws/vchw，日文压缩间距专用
WARN ligature_carets      缺 LigCaretList（只有 liga/dlig 两个特性）
WARN mandatory_avar_table 缺 avar 表（wght 轴线性，不需要 remap）
WARN math_signs_width     数学符号宽度异常值
WARN ots                  OTS sanitizer 提示
```

---

## 审计 38 项

```
新增第 12 组（VF 元数据）:
  STAT 条目覆盖 fvar instance
  name 只用 platform 3（无过时 Mac 记录）
  含 zh-CN name 记录
  nameID17 (Subfamily) = Regular

负向测试: 注入 Mac 记录 -> exit=1, FAIL 1；恢复 -> exit=0, PASS 38
```

---

## 回滚方式

```bash
cd /workspace/static/wdsans
cp archive/v261122/WDesignSans-VF.otf .
cp archive/v261122/WDesignSans-FlatApex-Regular.otf .
cp archive/v261122/wd-preview.woff2 .
cp archive/v261122/wd-poster-vf.woff2 poster/wd-vf.woff2
cp archive/v261122/wd-poster-flat.woff2 poster/wd-flat.woff2
cp archive/v261122/masters/*.otf /workspace/wdsans2/build/masters_R37/
```

更早版本：v261121（R36）、v261120（R35）、v261119（R34）、v261118（R32）。