# TTF 转换与平顶移除（2026-11-19）

## 用户新要求

1. 最终产物优先 TTF
2. 去掉顶点平顶（静态版和 VF 都没用，不如统一）

## 一、平顶已移除（完成）

```
删除内容:
  WDesignSans-FlatApex-Regular.otf  (17.9MB 字体文件)
  @font-face WDesignFlat             (index.html)
  指标表「顶点平顶（人字形）」行
  「顶点平顶专项」整个对比 panel（含 4 行对比 + 5 行数据表）
  孤儿 CSS 规则 .apex-cmp/.ac-row/.ac-lbl/.ac-wf/.ac-wv/.ac-op/.ac-ho

验证: index.html 17979 -> 15933 字节
      残留 WDesignFlat/顶点平顶/FlatApex 全部为 0
      div 73/73 配对，table 1/1 配对
      headless Chrome 渲染正常
```

## 二、TTF 转换（部分完成）

### 静态 TTF 转换：成功

```
工具: m_cff2ttf.py (TTGlyphPen + Cu2QuPen)
速度: 65,535 字形 55 秒，0 失败
输出: 21.5MB (OTF 17.9MB -> TTF 21.5MB，TTF 更大是正常的)

🔴 三个必须修的坑:
  1. loca 必须用 table__l_o_c_a 实例（glyf.compile 会调它的 set()）
  2. sfntVersion 必须改成 '\x00\x01\x00\x00'
     从 OTF 复制来的是 'OTTO'(0x4F54544F)，PIL/浏览器直接拒绝
  3. maxp.tableVersion 必须是 0x00010000（TrueType v1.0）

渲染一致性: 平均墨差 -0.18%，最大 0.46%（曲线转二次的正常精度损失）
```

### 可变 TTF：构建成功但有缺陷

```
产物: WDesignSansVF.ttf  22.8MB
  表: BASE GDEF GPOS GSUB HVAR OS/2 STAT VVAR cmap fvar glyf gvar
      head hhea hmtx loca maxp name post vhea vmtx
  sfnt 0x00010000  fvar wght 250-900  GPOS 11 特性(chws/vchw 保留)
  OS2 v4 typo=1.35em bit7=ON  glyphs 65535  cmap 45012

验证通过:
  HarfBuzz advance 全部与 OTF 一致（w250/400/700/900）
    Hamburgefonstiv 7782/7975/8335/8577 完全匹配
  CJK advance 恒定 4000（正确）
  默认字重 400 下渲染与 OTF 一致（墨差 ±0.2%）
  字形尺寸随字重变化正确（A 250=602 -> 400=635）
```

### 🔴 已知缺陷：60,946 个字形缺 gvar 插值

```
现象: varLib 报 'glyph X has incompatible masters; skipping'
      dollar/percent/ampersand/zero/A/a 等大量字形被跳过

原因: cu2qu 逐档独立转换时，三档的点数可能不同
      （曲线转二次的点数取决于该档曲线形状）
      varLib 需要三档点数完全一致才能插值

影响: 这些字形在默认字重 400 下正常，但非默认字重时不变形
      实测 advance 仍然正确（因为 hmtx 不变）

🔴 正确做法（下一轮）: 用 cu2qu 的 fonts_to_quadratic()
   三档一起转换，它会保证点数一致（compatible）
   而不是像我现在这样逐档独立转
```

## 当前状态

```
部署: 7f10bcf2 -> 70cc3146 (R42, OTF 可变，仍为主要产物)
      38.4MB -> 41.2MB? 实际 VF_R42g 是 41.2MB
待办: TTF 变体需要重做（用 fonts_to_quadratic 三档联动）
      TTF 就绪后切换页面引用，并把 OTF 降为备用
```

## 文件

```
modules/m_cff2ttf.py        静态 OTF->TTF 转换器（已可用）
modules/m_build_ttf_vf.py   TTF VF 构建脚本（designspace 部分需修）
build/ttf_masters/          三档 TTF master（21.3/21.7/21.4 MB）
build/WDesignSansVF.ttf     可变 TTF（有 gvar 缺陷）
build/ttf.designspace       TTF designspace（手写，已可用）
```