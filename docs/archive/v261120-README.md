# WDesign Sans · 存档 v261120

日期：2026-11-19
链尾：masters_R35（R34 + m_middotadv）
状态：已部署，审计 24 项全通过

---

## 文件

```
WDesignSans-VF.otf               41,335,436 B   可变字体 wght 250-900
WDesignSans-FlatApex-Regular.otf 17,915,460 B   静态 400 档 + 顶点平顶
wd-preview.woff2                  2,247,204 B   预览页子集 3,903 字
wd-poster-vf.woff2                  249,380 B   海报子集（可变）
wd-poster-flat.woff2                127,784 B   海报子集（静态）
masters/master-ExtraLight-250.otf               250 档
masters/master-Regular-400.otf                  400 档
masters/master-Heavy-900.otf                    900 档
```

校验：`md5sum -c MD5SUMS.txt`（8/8 通过）

---

## 相对 v261119 的唯一变更

### 中点类标点 advance 205 -> 500

```
实测（upm 1000，四码位共用 periodcentered）:
  字符        我们   SHS   OPPO  HOS
  U+00B7 ·    205   1000   500   500
  U+2022 •    205   1000   500  1000
  U+30FB ・   205   1000    -   1000
```

根因：四个码位共用 `periodcentered`，advance 从 Mona Sans 继承 205u
（Mona@400 的 U+00B7 就是 205）。但中文 UI 需要更宽的间隔，
否则「设置·消息」的间隔号会紧贴前后字。

该问题从 T6 代就存在，不是后期模块改坏的。

修正：`m_middotadv` 把 advance 改为 500u（取参考字体最低值，保守）
- 三档：250→489 / 400→500 / 900→538（按字重微缩放）
- 只改 hmtx，不动字形轮廓 → 零视觉风险
- 命中 1 个字形，影响 4 个码位

效果：
```
「设置·消息」  1641 -> 1759 px   （HOS 1763）
「A·B」        603 ->  721 px   （HOS  709）
其余 13 个标点（、。，：；！？—…「」（））全部未动
```

---

## 本轮同时修复的部署一致性问题

R35 只更新 VF 时，另外四个派生产物仍是旧字（·adv=205）：

```
WDesignSans-FlatApex-Regular.otf   205 -> 500（从 R35 400 档重建平顶）
poster/wd-vf.woff2                 205 -> 500
poster/wd-flat.woff2               205 -> 500
```

FlatApex 重建验证：截平 1,811 字（上版 1,804），
10 个平顶字高度与上一版完全相同，10 个对照组全部一致。

---

## 验证

```
VF 构建    313s / 41.3 MB / glyphs=65535 cmap=45012 cjk=20992
审计       PASS 24 / FAIL 0 / SKIP 1
           含 5 个字体文件 ·advance 一致性检查（全部 500）
HTTP       全部 200
页面渲染   「无限字重 · 一套统一」间隔号间距正常
```

---

## 未实现项（诚实说明）

**横折出头**（顶部横笔右端延伸）
三轮自动判据均误伤左侧偏旁横笔，最大一次误伤 1,456 / 20,992 字。
已放弃自动方案，当前继承思源黑体原始形态。

**横折撇偏粗**（多、及、予 等）
250 档撇厚 38 vs SHS 28（+10 单位 ≈ 1% em，正文与海报字号不可见）。
根因是横笔右端 770 vs SHS 722（「拐角竖直」的固有代价）。
三条路径全部证伪并记录。

**U+2022 • 墨迹偏小**
本版墨迹 118 vs 参考 229（不到一半）。属语义问题（项目符号应明显大于
间隔号），需新建字形占槽位，本版只修 advance 未动轮廓。

---

## 回滚方式

```bash
cd /workspace/static/wdsans
cp archive/v261120/WDesignSans-VF.otf .
cp archive/v261120/WDesignSans-FlatApex-Regular.otf .
cp archive/v261120/wd-preview.woff2 .
cp archive/v261120/wd-poster-vf.woff2 poster/wd-vf.woff2
cp archive/v261120/wd-poster-flat.woff2 poster/wd-flat.woff2
cp archive/v261120/masters/*.otf /workspace/wdsans2/build/masters_R35/
```

更早版本：v261119（R34）、v261118（R32）。