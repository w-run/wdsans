# 可变 TTF 构建成功（第二轮，修复 qCurveTo）

## 修复的 bug

```
🔴 curves_to_quadratic 返回 [start, ctrl1, ctrl2, ..., end]
   qCurveTo 需要 [ctrl1, ctrl2, ..., end]  <-- 必须去掉首点

错误写法: pen.qCurveTo(*op[1], op[2])
  -> 参数里 start 和 end 都出现两次
  -> 'a' 的墨差 74.51%

正确写法: pen.qCurveTo(*op[1][1:])
  -> 参数正确，'a' 墨差 1.52%
```

## 当前产物

```
WDesignSansVF2.ttf  34.0MB
  表: BASE GDEF GPOS GSUB HVAR OS/2 STAT VVAR cmap fvar
      glyf gvar head hhea hmtx loca maxp name post vhea vmtx
  sfnt 0x00010000  fvar wght 250-900  gvar 65535 字形
  GPOS 11 特性（chws/vchw 已注入）
  OS2 v4 typo=1.35em bit7=ON  glyphs 65535  cmap 45012

三档 TTF master: 21.8 / 22.2 / 21.8 MB
转换: 65,491 成功 / 44 跳过（全是空字形）
```

## 渲染验证（400 默认档）

```
字    TTF 墨量    OTF 墨量    墨差     起点偏移
永      37173       37258   -0.23%   (+2,0)
国      58119       58005   +0.20%   (+3,0)
A       25064       25043   +0.08%   (-8,0)
a       20483       20177   +1.52%   (+4,0)
$       26868       26813   +0.21%   (+7,0)
%       26161       26186   -0.10%   (-5,0)
设      43011       43215   -0.47%   (+4,+1)

全部在 ±1.6% 内（曲线转二次的正常精度）。
```

## 🔵 重要发现：TTF 修正了 OTF 的 lsb 不一致

```
OTF(R42):   2598/2992 字形 lsb != bbox.xmin  (87%)
TTF(multi):   14/2992 字形 lsb != bbox.xmin  (0.5%)

样例:
  !  OTF lsb=97  bbox.xmin=82  (差 -15)
  $  OTF lsb=68  bbox.xmin=51  (差 -17)
  %  OTF lsb=46  bbox.xmin=58  (差 +12)

这是 SHS 上游遗留：CFF 字体的 lsb 可以有任意值，
但 TrueType 要求 lsb == bbox.xmin。fontTools 转换时自动校正。

效果: TTF 的字形会相对 OTF 平移 1-8 单位（0.1%-0.8% em），
      这是修正，不是缺陷。字体渲染位置本就应由 lsb 决定。
```

## advance 验证

```
HarfBuzz 全字重（250/300/400/500/600/700/800/900）对 OTF:
  永国字体 / Hamburgefonstiv / 0123456789 / $%&@ / 设置·消息
  差异总数: 0

字形宽度随字重递增（插值有效）:
  H extents: 250=554  400=583  700=628  900=658
```

## 待完成

1. 注入 full_post 的后处理（STAT/name/zh-CN/GSUB 排序）
   当前 TTF 只有 chws/vchw，缺 STAT=10 / name platforms=[3] / zh-CN=5
2. 页面切换到 TTF（用户要求优先 TTF）
3. 子集重建 + woff2
4. 归档

## 文件

```
modules/m_cff2ttf_multi.py   三档联动转换器
build/ttf_masters_multi/     三档 TTF master（21.8/22.2/21.8 MB）
build/ttf2.designspace       TTF designspace
build/WDesignSansVF2.ttf     可变 TTF 34.0MB
```