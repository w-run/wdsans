# 可变 TTF 构建成功（2026-11-19）

## 核心技术突破：三档联动曲线转换

```
问题: 逐档独立调 Cu2QuPen 转二次曲线时，每档点数取决于该档曲线形状
      -> 三档点数不同 -> varLib 报 incompatible masters -> 该字形无 gvar

首次尝试: 60,946 / 65,535 字形被跳过（93%）

🔴 关键 API: cu2qu.curves_to_quadratic(curves, max_errors)
   一次传入三档的同一条曲线，保证返回点数一致

🔴 但有两个坑:
  1. curve 必须是 (start, c1, c2, end) 四点，不是 (c1, c2, end) 三点
     错传三点 -> calc_intersect() missing 1 required positional argument: 'd'
  2. 必须维护当前点 cur_pt，每段后更新

修正后: 转换 65,491 / 65,535，只跳过 44 个（0.07%）
```

## 剩余 44 个跳过的是什么

```
抽查 glyph28899/28900/35917/uniF93C: 全部 contours=None coords=0

glyphNNNNN 类字形统计: 空 21,030，非空 0

-> 不兼容的全是空字形（未映射槽位），无插值数据不影响使用
   唯一例外 uniF93C 有 cmap 映射但轮廓为空（上游遗留）

varLib 会为所有 65,535 字形生成 gvar（含空字形），只是空字形的
变体数据为零。实际有内容的 44,504 个映射字形全部正常。
```

## 产物

```
WDesignSansVF2.ttf  37.3MB
  表: BASE GDEF GPOS GSUB HVAR OS/2 STAT VVAR cmap fvar
      glyf gvar head hhea hmtx loca maxp name post vhea vmtx
  sfnt 0x00010000  fvar wght 250-900
  gvar 65,535 字形  GPOS 11 特性（chws/vchw 已注入）
  OS2 v4 typo=1.35em bit7=ON  glyphs 65535  cmap 45012

三档 TTF master: ttf_masters_multi/master-{250,400,900}.ttf (各 23.7MB)
designspace: ttf2.designspace（手写 XML，因为 API 的 location 写不进 XML）
```

## 验证结果

```
PIL 可加载: OK ('WDesign Sans','ExtraLight')

HarfBuzz advance 全字重对比 OTF:
  w250/300/400/500/600/700/800/900 全部 OK
  测试串: 永国字体 / Hamburgefonstiv / 0123456789 / $%&@ / 设置·消息
  差异总数: 0

字形宽度随字重递增（插值生效）:
  H  extents: 250=554  400=583  700=628  900=658
```

## 过程中发现的 designspace API 坑

```
fontTools DesignSpaceDocument 的 SourceDescriptor:
  s.location = {...}      写入后 XML 里没有 <location>
  s.designLocation = {...}  同样没写进去

结果: varLib 报 'More than one base master found in Designspace'

可靠做法: 手写 designspace XML，显式写
  <location><dimension name="Weight" xvalue="400"/></location>
```

## 待完成

1. 各字重视觉渲染对比（实例化每档约 3 分钟，正在跑）
2. 注入 full_post 的全部后处理（STAT/name/zh-CN/GSUB 排序）
   注意: chws 已注入，但 STAT 等还没做
3. 页面切换到 TTF，OTF 降为备用
4. 子集重建 + 归档

## 文件

```
modules/m_cff2ttf_multi.py   三档联动转换器（核心）
build/ttf_masters_multi/     三档 TTF master
build/ttf2.designspace       TTF designspace
build/WDesignSansVF2.ttf     可变 TTF 产物
```