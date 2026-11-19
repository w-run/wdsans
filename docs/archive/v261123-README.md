# WDesign Sans · 存档 v261123

日期：2026-11-19
链尾：masters_R37 + m_fbclean2 + chws_tool
状态：已部署，审计 41 项全通过

---

## 文件

```
WDesignSans-VF.otf               41,335,712 B  462a9ea3...
WDesignSans-FlatApex-Regular.otf 17,915,780 B  b2376d8c...
wd-preview.woff2                  2,247,512 B
wd-poster-vf.woff2                  249,760 B
wd-poster-flat.woff2                128,332 B
masters/ 三档（R37）
```

校验：md5sum -c MD5SUMS.txt（8/8 通过）

---

## 相对 v261122 的唯一变更：新增 chws / vchw 特性

### 问题

```
fontbakery check-universal 报告:
  WARN cjk_chws_feature [missing-chws-feature, missing-vchw-feature]

chws = Contextual Half Widths，东亚标点的上下文半角压缩
vchw = Vertical Contextual Half Widths，竖排版本
作用: 让「、。」「（）」等在行首/行尾自动压缩为半角，
      符合 JLREQ（日文排版需求）与中文标点挤压规范。
```

### 工具

```
chws_tool 1.4.5（Google Fonts 官方推荐工具）
  pip install chws-tool
  add-chws -o <输出> <输入>

运行 41 秒，文件 +672 字节
```

### 🔴 容易误判的地方：chws 加在 GPOS 不是 GSUB

```
第一次检查我找的是 GSUB，结果「特性完全相同、chws 仍为 False」，
误以为工具没生效。

实际逐表对比字节发现:
  GPOS: 262,178 -> 262,852 (+674 字节)
  其他 20 张表完全不变

原因: chws 是字距调整（GPOS），不是字形替换（GSUB）。
      调整标点 advance，不换字形。
```

### 实际改动

```
GPOS 特性: 9 -> 11（新增 chws + vchw）
GPOS lookups: 14 -> 20（+6）

注册范围（全部脚本的 DefaultLangSys + 各 LangSys）:
  DFLT / cyrl / grek / hang / hani / kana / latn
  每个都含 Default + JAN + KOR + ZHH + ZHS + ZHT
  -> 中文环境（hani/ZHS）已正确挂载
```

### 效果（HarfBuzz 实测）

```
、。，「」  无chws [1000,1000,1000,1000,1000]
            有chws [ 500, 500, 500,1000,1000]   3/5 个压缩
（）《》    有chws 1/4 个压缩
竖排 、。   y_advance -1000 -> -500（vchw 生效）
```

### 安全性验证（关键）

```
chws 是 opt-in 特性 —— 不启用时排版完全不变。

22 个用例零差异:
  永国字体设计 / 设置·消息·相机 / 0123456789 /
  Hamburgefonstiv minimum / fifi ffl office / 12:34 a:b /
  123(sups) / 123(subs) / 123(numr) / 123(dnom) /
  1/2 3/4(frac) / 123(pnum) / b́ d́ g̃ / 一́ / ABCDEFGHIJ /
  、。，：；！？ / 「测试」「引用」
  + 5 种语言（zh-hans/zh-hant/ja/ko/en）

表格结构: 21 张表 -> 21 张表，无新增无删除
关键元数据: rev=1.000 OS2v=4 typo=1.35em STAT=10 zh=5 mark=30
            glyphs=65535 cmap=45012 —— 全部不变
```

### 参考字体对照

```
字体        GSUB特  GPOS特  有chws  有vchw
我们 R38       23       9    False   False
我们 +chws     23      11    True    True
SHS            16       8    False   False
OPPO           16       3    False   False
HOS            21       3    False   False

-> 三家参考字体都没有 chws/vchw。
   所以这不是「缺失的应有功能」，而是可选的现代排版增强。
   加它是「多做了正确的事」，不是修补缺陷。
```

---

## fontbakery 最终状态

```
R38: FAIL 1 / WARN 6
R39: FAIL 1 / WARN 5
     cjk_chws_feature 已消除

剩余（全部不可修）:
  FAIL file_size            CJK 字体 41MB，9MB 限制面向拉丁
  WARN post_table_version   format 3 对可搜索 PDF 有小众影响，CFF2 必需
  WARN ligature_carets      缺 LigCaretList（只有 liga/dlig）
  WARN mandatory_avar_table 缺 avar（wght 轴线性，不需要 remap）
  WARN math_signs_width     数学符号宽度异常值
  WARN ots                  OTS sanitizer 提示
```

---

## 审计 41 项

```
新增第 13 组（chws/vchw）:
  含 chws 特性
  含 vchw 特性
  原有 GPOS 特性完好（kern/mark/mkmk/palt 不能被挤掉）
```

---

## 回滚方式

```bash
cd /workspace/static/wdsans
cp archive/v261123/WDesignSans-VF.otf .
cp archive/v261123/WDesignSans-FlatApex-Regular.otf .
cp archive/v261123/wd-preview.woff2 .
cp archive/v261123/wd-poster-vf.woff2 poster/wd-vf.woff2
cp archive/v261123/wd-poster-flat.woff2 poster/wd-flat.woff2
cp archive/v261123/masters/*.otf /workspace/wdsans2/build/masters_R37/
```

更早版本：v261122（R38）、v261121（R36）、v261120（R35）、
          v261119（R34）、v261118（R32）。