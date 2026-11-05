# P49：SIL OFL 合规缺陷 —— 版权声明 ID0 缺失

## 发现过程

本轮本想验证 Windows ClearType 兼容性，检查 name 表时发现：

```
我们 Regular  name 表: {(3, 1): 32}   ← 只有 Windows Unicode
Noto VF       name 表: {(1, 0): 15, (3, 1): 43}
OPPO 400      name 表: {(1, 0): 11, (1, 25): 8, (3, 1): 19}
鸿蒙 400      name 表: {(1, 0): 9, (1, 25): 3, (3, 1): 15}
```

**三款参照字体都保留 Mac 平台记录，只有我们全删了。**

追查代码，发现是 `deliver2.py:112`：
```python
inst["name"].names = [n for n in inst["name"].names if n.platformID != 1]
```

这是 P12 时按 fontbakery 的 `mac-names` 建议做的。

## 一、Mac 记录删除：可接受的取舍

`no_mac_entries` 检查在 **typesetwork / googlefonts profile** 里，
面向**云端字体分发**。我们的场景是内网自用，Windows/macOS/iOS 现代系统
都优先读 platformID=3（Windows Unicode），删 Mac 记录不影响渲染。

**判断：保留现状，不改。**（Noto 保留 Mac 记录也无妨，但非必需）

## 二、真正的缺陷：ID0 版权声明缺失

继续检查 nameID 覆盖，发现：

| nameID | 含义 | 我们 | Noto |
|---|---|---|---|
| **0** | **Copyright** | **缺** | 有 |
| 7 | Trademark | **缺** | 有 |
| 13 | License | 有 | 有 |
| 14 | LicenseURL | 有 | 有 |
| 16 | Typographic Family | **有** | 缺 |
| 17 | Typographic Subfamily | 有 | 有 |

### 这是合规问题，不是可选项

SIL OFL 1.1 第 1 条明确要求：
> 分发时必须保留原作者的版权声明（copyright notice）

本字体同时继承两套 OFL 字体：
- **Noto Sans CJK**（Adobe，OFL 1.1）
- **Mona Sans**（GitHub，OFL 1.1）

**我们删掉了 ID0，等于删掉了 Adobe 和 GitHub 的版权声明，违反 OFL。**

## 三、修复

新增 `meta_fix.fix_legal()`：

```python
COPYRIGHT = (
    "Copyright 2014-2021 Adobe (http://www.adobe.com/), "
    "with Reserved Font Name 'Source'. "
    "Copyright 2022 The Mona Sans Project Authors "
    "(https://github.com/github/mona-sans), with Reserved Font Name 'Mona'. "
    "WDesign Sans modifications Copyright 2026 WDesign."
)
TRADEMARK = ("Source is a trademark of Adobe in the United States and/or other countries.")
```

同时写入 platformID=3（Windows Unicode）和 platformID=1（Mac Roman），
不覆盖已有记录（幂等）。

并接入 `deliver2.build()`：
```python
meta_fix.fix_fsselection(inst, style)
meta_fix.fix_legal(inst)   # P49: OFL compliance (ID0/ID7)
```

## 四、验证

单档试运行：新增 4 条记录（ID0/ID7 × 两个平台）。

修复后：
```
ID0   Copyright   = Copyright 2014-2021 Adobe (http://www.adobe.com/), 
                    with Reserved Font Name 'Source'. 
                    Copyright 2022 The Mona Sans Project Authors ...
ID7   Trademark   = Source is a trademark of Adobe ...
ID13  License     = This Font Software is licensed under the SIL OFL 1.1 ...
ID14  LicenseURL  = http://scripts.sil.org/OFL
```

## 五、教训

**「工具建议」不等于「对我的场景也成立」。**

P12 时我完全照搬了 fontbakery 的 `mac-names` 建议，
连带把版权声明一起删掉了——因为那个过滤条件是
`platformID != 1`，而 ID0/ID7 恰好也有 Mac 记录。

**根因：用平台过滤删记录时，没检查被删的 nameID 是什么。**

正确的思路应该是：
1. 先问「这条建议针对什么场景」（Google Fonts 云端分发）
2. 再问「我的场景是否相同」（内网自用，不同）
3. 删记录时按 **nameID 白名单**，而不是按平台一刀切

这与 P34/P36/P47 是同一个方法：**先判断语境，再看是否适用。**
## 六、修复后的回归验证

### 排版行为零影响（预期，但仍要验）

name 表改动理论上不影响排版，但必须实测确认：

| 用例 | 修补前 | 修补后 | 判定 |
|---|---|---|---|
| 中文 国永 | 2段/2000 | 2段/2000 | ✓ |
| locl 骨（繁）| 1段/1000 | 1段/1000 | ✓ |
| 竖排 （ | 1段/0 | 1段/0 | ✓ |
| 连字 fi | 1段/600 | 1段/600 | ✓ |
| kern AV | 2段/1253 | 2段/1253 | ✓ |
| Latin Ąą | 2段/1159 | 2段/1159 | ✓ |

**六项完全一致，零回归。**

### OTS 仍然通过

修改 name 表后重新跑 OTS（P48 的闸门）：

```
七档 TTF: 7/7 OK
```

说明写入长版权字符串（251 字符）不会破坏浏览器兼容性。

### 最终 nameID 覆盖

```
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 16, 17, 256-265]
```

对比修复前多了 **0（Copyright）** 和 **7（Trademark）**。

`ID0 = Copyright 2014-2021 Adobe ... Copyright 2022 The Mona Sans Project Authors 
... WDesign Sans modifications Copyright 2026 WDesign.`（251 字符）

## 七、为什么这个缺陷以前没被发现

因为**从没有人检查过「我们删掉的记录里有没有重要的」**。

P12 的验证只做了：
- 「删除后 ID 1/2/5/6/16/17 是否仍在」→ 在
- 「渲染是否正常」→ 正常

但没做：
- **「被删掉的记录本身是什么」**

这是个普遍盲区：**验证「保留的东西还好」，但不验证「删除的东西该不该删」。**