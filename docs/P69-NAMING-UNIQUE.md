# P69：命名唯一性修复（VF + 子集）

## 问题回顾

P67 修了 VF 与静态 Regular 的命名冲突（加 "VF" 后缀）。
但**子集 12 个文件也有同样问题**，当时我判断「可暂不改」。

本轮重新审视，发现那个判断**不成立**。

## 一、子集命名的实际状况

| 文件 | ID1 | ID6 | 子集标识 |
|---|---|---|---|
| Regular-sub3755 | WDesign Sans | **WDesignSansSC-Regular** | **无** |
| Regular-sub6763 | WDesign Sans | **WDesignSansSC-Regular** | **无** |
| Medium-sub3755 | WDesign Sans Medium | WDesignSansSC-Medium | **无** |
| Medium-sub6763 | WDesign Sans Medium | WDesignSansSC-Medium | **无** |
| Bold-sub3755 | WDesign Sans | WDesignSansSC-Bold | **无** |
| Bold-sub6763 | WDesign Sans | WDesignSansSC-Bold | **无** |

### 为什么「可暂不改」是错的

我上轮的推理是：「子集是 Web 用，@font-face 显式指定路径，同名不冲突」。

**但这只在「一次只用一档」时成立。** 有两个真实风险：

1. **桌面安装**：用户若把子集也装进系统，会与全库版本同 ID6 冲突
2. **字体管理工具/设计软件**：按 name 表索引，同 ID6 会被判为重复安装，只显示一个

而且 3755 与 6763 **两档彼此也同名**——即便不考虑全库，这两档自己就撞。

## 二、修复

| ID | 修改规则 | 示例（Regular-sub3755）|
|---|---|---|
| 1 | 族名 + 标识 | WDesign Sans → **WDesign Sans sub3755** |
| 4 | 全名 + 标识 | → **WDesign Sans sub3755** |
| 6 | PS 名 + `-` + 标识 | WDesignSansSC-Regular → **WDesignSansSC-Regular-sub3755** |
| 16 | 排版族名 + 标识 | → **WDesign Sans sub3755** |
| 3 | 唯一标识串 | → WDesignSansSC-Regular-sub3755;2026.100;WDGN;... |

12 个文件全部处理完毕。

## 三、验证（含一次口径纠错）

### 第一次检查：报「6/12 重复」

脚本按「ID6 是否出现过」判断，结果 TTF 与 WOFF2 成对报重复。

**这是口径错误**：同一个字体的 TTF 和 WOFF2 是**同一份内容的不同封装**，
name 表理应完全相同——否则反而是错的。

### 正确口径：按「字重 + 子集档」判断

```
ID6 种类: 6
  WDesignSansSC-Bold-sub3755      <- [ttf, woff2]   同字体不同封装
  WDesignSansSC-Bold-sub6763      <- [ttf, woff2]
  WDesignSansSC-Medium-sub3755    <- [ttf, woff2]
  WDesignSansSC-Medium-sub6763    <- [ttf, woff2]
  WDesignSansSC-Regular-sub3755   <- [ttf, woff2]
  WDesignSansSC-Regular-sub6763   <- [ttf, woff2]
```

### 跨类别检查

```
跨类别同名（dist 与 subset 撞名）: 0
全部 ID6 种类: 14
```

**全库 7 档 + VF 1 个 + 子集 6 档 = 14 个唯一 ID6，零冲突。**

### OTS 复验

```
12/12 通过
```

## 四、最终命名体系

| 类别 | ID6 示例 | 数量 |
|---|---|---|
| 静态全库 | WDesignSansSC-Regular | 7 |
| VF | WDesignSansSC-VF | 1 |
| 子集 | WDesignSansSC-Regular-sub3755 | 6 |
| **合计唯一 ID6** | — | **14** |

## 五、教训

### 1.「可暂不改」需要验证，不能凭直觉

我上轮的推理（Web 用不到 name）在**单一场景**下正确，
但漏掉了桌面安装和字体管理工具两个场景。

**判断「某个不一致是否有害」，要穷举使用场景。**

### 2. 检查口径又一次出错

第一版检查报「6/12 重复」，因为把 TTF 和 WOFF2 当作两个独立字体。

**同一个字体的不同格式必然同名，否则才是不一致。**

判定唯一性应该按「内容实体」而非「文件」计数。