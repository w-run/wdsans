# WDesign Sans

**v3.0.261120** · 中文可变字体 · 65,535 字形 · wght 100–900

现代中文无衬线可变字体。

## 特性

```
字符数        45,012（CJK 20,992）
字重轴        100 ~ 900，9 个命名实例
字形数        65,535
格式          TTF / WOFF2 / WOFF（可变与静态）
表            22（含 GSUB 490 特性, GPOS 11 特性, STAT, HVAR, VVAR）
竖排          支持（vhea / vmtx / vert / vrt2）
```

## 字重体系

```
100  Thin
200  ExtraLight
300  Light
400  Regular
500  Medium
600  SemiBold
700  Bold
800  ExtraBold
900  Black
```

## 文件说明

### 可变字体

| 文件 | 大小 | 说明 |
|---|---|---|
| `WDesignSans-VF.ttf` | 49.9 MB | 完整可变字体，全部 45,012 字符 |
| `WDesignSans-VF.woff2` | 5.6 MB | Web 子集，常用 3,500 字 + 拉丁 |
| `WDesignSans-VF-full.woff2` | 10.1 MB | Web 全字库（GB2312） |
| `WDesignSans-Latin.woff2` | 0.5 MB | 仅拉丁字母与符号 |

### 静态字体

| 文件 | 大小 | 说明 |
|---|---|---|
| `WDesignSans-Thin.ttf` | 21.7 MB | wght=100 全字符 |
| `WDesignSans-Light.ttf` | 21.7 MB | wght=300 全字符 |
| `WDesignSans-Regular.ttf` | 21.7 MB | wght=400 全字符 |
| `WDesignSans-Bold.ttf` | 21.7 MB | wght=700 全字符 |
| `WDesignSans-Black.ttf` | 21.6 MB | wght=900 全字符 |
| `WDesignSans-Regular-web.ttf` | 2.5 MB | wght=400 常用子集 |

### 分片 Web 字体（推荐用于网页）

```
slices/           59 个 woff2 分片，共 33.3 MB
wdesign-sans.css  59 条 @font-face 声明，含 unicode-range
```

按 Unicode 码位区间切分，**浏览器只下载页面实际用到的分片**。
典型中文页面命中 2–4 片，约 1–2 MB（对比全量 5.6 MB，节省 60–80%）。

用法：

```html
<link rel="stylesheet" href="wdesign-sans.css">
```

```css
body { font-family: 'WDesign Sans', sans-serif; }
h1   { font-weight: 700; }
```

## 排版特性

```
frac   分数        1/2 → ½ 形式（分子右上/分母左下）
sups   上标        0123456789
subs   下标        0123456789
numr   分子        numr/dnom 组合
dnom   分母
pnum   比例数字    （默认已是比例）
chws   标点压缩    中日韩标点挤压
vert   竖排替换
vrt2   竖排旋转
kern   字距调整
mark   组合音标定位
calt   上下文替换  时间冒号居中
```

使用示例：

```css
.fraction { font-feature-settings: 'frac' 1; }
.sups     { font-feature-settings: 'sups' 1; }
```

## 许可

SIL Open Font License 1.1（见 `OFL.txt`）

## 许可与归属

本字体为衍生作品，基于以下开源字体构建：

### Source Han Sans（思源黑体）

```
Copyright 2014-2021 Adobe (http://www.adobe.com/)
SIL Open Font License 1.1
https://github.com/adobe-fonts/source-han-sans

Designers:
  Ryoko NISHIZUKA 西塚涼子 (kana, bopomofo & ideographs)
  Paul D. Hunt (Latin, Greek & Cyrillic)
  Sandoll Communications 산돌커뮤니케이션, Soo-young JANG 장수영 & Joo-yeon KANG 강주연 (hangul)
  Masataka HATTORI 服部正貴 (production)

Project architect: Dr. Ken Lunde
```

### Mona Sans

```
Copyright 2022 GitHub Inc.
SIL Open Font License 1.1
https://github.com/github/mona-sans
```

本字体为上述开源字体的衍生作品，经大幅度修改。

## 保留字体名

本字体使用 `WDesign Sans` 作为族名，未占用 `Source` 或 `Mona` 保留名，符合 OFL 1.1 要求。

## 版本

```
v3.0.261120  2026-11-20
  字重轴重新标号 250-900 → 100-900（OpenType 标准命名）
  修复 frac 分母未下移（ChainContext 只覆盖 1 个字形）
  拉丁字形全面重建（i/j/带音标，439 字形）
  横折拐角垂直过渡 + 落点对齐底边
```

## 项目

```
https://w-run.com
https://github.com/w-run/wdsans
```