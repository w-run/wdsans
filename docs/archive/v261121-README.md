# WDesign Sans · 存档 v261121

日期：2026-11-19
链尾：masters_R36（R35 + m_lineheight）
状态：已部署，审计 28 项全通过

---

## 文件

```
WDesignSans-VF.otf               41,335,436 B  可变字体 wght 250-900
WDesignSans-FlatApex-Regular.otf 17,915,460 B  静态 400 + 顶点平顶
wd-preview.woff2                  2,247,636 B  预览页子集
wd-poster-vf.woff2                  249,312 B  海报子集（可变）
wd-poster-flat.woff2                127,952 B  海报子集（静态）
masters/master-ExtraLight-250.otf
masters/master-Regular-400.otf
masters/master-Heavy-900.otf
```

校验：md5sum -c MD5SUMS.txt（8/8 通过）

---

## 相对 v261120 的唯一变更：行高 1.45em -> 1.35em

### 问题

```
实测四字体，同一 100px 字号三行文本:
  字体   line_h  行高/字号
  我们     145     1.45em
  SHS      145     1.45em   <- 同源
  OPPO     132     1.32em   -9%
  HOS      118     1.18em   -19%

14px 下 7 行 UI 文本: 我们 142px vs OPPO 129px vs HOS 116px
```

### 为什么不能直接压 hhea/usWin

```
全库字形极端值（排除 7 个竖排专用符号）: 最高 1069 最低 -281
实测各 usWinAscent 的超界字形数:
  usWinAscent   超界字形数
     1000          20
     1050          16
     1100           4
     1160           4   <- SHS 现值
     1325           4   （但行高变 1.62em）
压低必然裁切字形，抬高行高更大 -> 直接改 hhea 是死路。
```

### 采用方案：USE_TYPO_METRICS

```
OpenType 的设计意图就是让 typo 独立于 usWin:
  usWin 保持 1160/288  -> 竖排符号不额外恶化
  typo  设为 1070/-282 -> 1352 = 1.35em（接近 OPPO 1.32）

bit7 只在 OS/2 v4+ 定义，我们/SHS 都是 v3。
实测 v3->v4 只改 version 字段，42 个字段其余不变，文件大小不变。
```

### 安全性验证（全部通过）

```
全部 44,996 字符 在 typo 行框 (-282~1070) 内:  超高 0 / 超低 0
全部 20,992 CJK  在行框内:                    超高 0 / 超低 0
常用 500 字      在行框内:                    超出 0
三档 w250/w400/w900 度量完全一致
VF 与 FlatApex 度量一致
```

### 唯一副作用（可接受）

```
4 个竖排/注音专用符号与相邻行的重叠量增加 96 单位（0.096em）:
  U+3031 〱 竖排假名重复符    R35 超 424 -> R36 超 520
  U+3032 〲 竖排假名浊音符    R35 超 424 -> R36 超 520
  U+302A 〪 注音声调符号       R35 超  15 -> R36 超  21
  U+302D 〭 注音入声符号       R35 超  15 -> R36 超  21

这些字符本来就已经超出（R35 就超 424），且仅日文竖排/注音使用，
中文横排正文出现概率接近 0。浏览器不裁切行框外字形，仅表现为轻微重叠。
```

### 效果

```
行高      1.45em -> 1.35em
7行@14px  142px  -> 132px   (OPPO 129px)
页面字重阶梯从「显示到 500」变为「显示到 700」
```

---

## 五个产物全部同步

```
WDesignSans-VF.otf                 5c4dfaad...
WDesignSans-FlatApex-Regular.otf   e49e2894...
wd-preview.woff2 / poster 两个子集  重新生成
cache-buster                        202611191003
```

---

## 验证

```
VF 构建   41.3 MB / glyphs=65535 cmap=45012 cjk=20992（与 R35 一致）
审计      PASS 28 / FAIL 0 / SKIP 1
HTTP      全部 200
页面渲染  行高收紧，字重阶梯延伸至 700 Bold
```

---

## 未实现项（诚实说明）

**横折出头**（顶部横笔右端延伸）
三轮自动判据均误伤左侧偏旁横笔，最大一次误伤 1,456 / 20,992 字。
已放弃自动方案，当前继承思源黑体原始形态。

**横折撇偏粗**（多、及、予 等）
250 档撇厚 38 vs SHS 28（+10 单位 ≈ 1% em，正文与海报字号不可见）。
根因是横笔右端 770 vs SHS 722（「拐角竖直」的固有代价）。三条路径全部证伪。

**U+2022 • 墨迹偏小**（118 vs 参考 229）
SHS 原版也是四码位共用一字形，非我们引入。
字体已达 65,535 字形上限，无法新建槽位，放弃。

---

## 回滚方式

```bash
cd /workspace/static/wdsans
cp archive/v261121/WDesignSans-VF.otf .
cp archive/v261121/WDesignSans-FlatApex-Regular.otf .
cp archive/v261121/wd-preview.woff2 .
cp archive/v261121/wd-poster-vf.woff2 poster/wd-vf.woff2
cp archive/v261121/wd-poster-flat.woff2 poster/wd-flat.woff2
cp archive/v261121/masters/*.otf /workspace/wdsans2/build/masters_R36/
```

更早版本：v261120（R35）、v261119（R34）、v261118（R32）。

注意：若要回滚到 v261120，行高会恢复为 1.45em（OS/2 v3 + bit7 off）。