P12：接入 fontbakery（社区标准 QA）并修复两处真实元数据缺陷

## 为什么引入 fontbakery

objective 要求「社区有好的方案可以参考，而不是照搬」。
fontbakery 是 Google Fonts / 字体行业的标准 QA 工具，规则集比自建检查全面。
安装：pip install fontbakery（968 个检查项）

## 它抓到的 5 个 FAIL —— 只有 2 个是真 bug

### 真 bug 1：head.fontRevision 与 name ID5 不一致
```
head.fontRevision = 2.00399780  (从思源黑体 2.004 继承)
name ID5          = "Version 1.000"
```
→ 已统一为 1.000。

### 真 bug 2：OS/2.fsSelection == 0b0
Regular 档既没置 REGULAR 位(6) 也没置 BOLD 位(5)，
Windows 无法判断这是正体。→ 按样式设置：Regular->bit6，Bold->bit5，其余重量都不置。

### 误报 1：零宽字形（uni20DD 等 13 个）
全部是**组合记号**：gravecomb / acutecomb / uni302A/B/C/D / uni3099/309A / uni20DD/20DE。
组合记号本就该零宽——Noto 基座同样这 13 个是 0。
fontbakery 的 base_has_width 启发式不认识 CJK 组合类。→ 保留原样。

### 误报 2：massive-font（21MB > 9MB）
该限制面向拉丁字族；65k 字形的 CJK 全字库必然超过。→ 接受。

### 已处理：mac-names（建议删除 Mac 平台 name 记录）
42 条 name 记录里有 10 条 platformID=1（Mac）。
现代系统只用 platformID=3，删除后 ID 1/2/5/6/16/17 全部保留、渲染正常。
→ 已删除。注：这是「社区惯例」，不是错误；保留也无害。

## 复验结果

修复后 FAIL 从 5 类降到 3 类，剩余全部是上述已论证的误报/接受项。

## 教训

自建检查（G1-G7 闸门）覆盖了拓扑/结构/命名，但漏掉了：
- 版本号一致性（head vs name）
- fsSelection 位（影响 Windows 样式识别）
- Mac 平台 name 冗余
这类「元数据礼节」正是社区工具最擅长的地方。

新增 wds/meta_fix.py，接入 wds/deliver2.py。