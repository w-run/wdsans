# P50：许可证全文缺失 —— README 引用了不存在的文件

## 发现过程

P49 收尾时我在 README 里写了：
> 许可证全文见 `OFL.txt`（SIL Open Font License 1.1）

**但当时并没有核实这个文件是否存在。** 本轮第一件事就是查：

```
$ ls dist/
README.md
WDesignSansSC-Bold.ttf     ... (27 个字体文件)
subset/

OFL.txt 存在: false        ← 引用了不存在的文件
```

## 为什么这是问题

SIL OFL 1.1 第 2 条明确要求：

> Original or Modified Versions of the Font Software may be bundled,
> redistributed and/or sold with any software, provided that **each copy
> contains the above copyright notice and this license.**
> These can be included either as stand-alone text files, human-readable
> headers or in the appropriate machine-readable metadata fields...

即：**分发时必须附带许可证全文**，可以是独立文本文件，也可以内嵌到字体元数据。

现状分析：

| 要求 | 状态 |
|---|---|
| 版权声明（copyright notice）| ✅ 已完成（P49，name ID 0）|
| 许可证全文（this license）| ❌ **缺失** |

字体里已有 `name ID 13`（License 描述）和 `ID 14`（LicenseURL），
但那只是一句「本字体以 OFL 1.1 授权」的**摘要**，不是许可证**全文**。

严格按 OFL 字面要求，需要完整正文。

## 修复

生成 `OFL.txt`，包含：
1. 两个上游来源的版权声明（Noto/Adobe、Mona/GitHub）
2. 本项目的修改声明
3. 保留字体名称（Reserved Font Name）说明
4. **SIL OFL 1.1 完整正文**

### 关键：正文必须逐字一致

第一版我手写了许可证正文，结果 MD5 与上游不一致：

```
上游: a4b07ee14dff3c5628dee889b800246a
我的: 7ea7040d242144a5ca831f35053050db   ← 不同！
```

diff 看差异，全是**换行位置不同**和被改写的符号：

```
< or substituting — in part or in whole — any of the components of the   ← 上游用 em-dash
> or substituting -- in part or in whole -- any of the components of the  ← 我写成 --
< requirement for fonts to remain under this license does not apply
< to any document created using the fonts or their derivatives.
> requirement for fonts to remain under this license does not apply to any   ← 换行位置不同
> document created using the fonts or their derivatives.
```

虽然语义等价，但**法律文本不应改写**。

**正确做法：直接从上游 `ref/mona/LICENSE.txt` 截取正文嵌入，不手打。**

修复后：
```
上游: a4b07ee14dff3c5628dee889b800246a
最终: a4b07ee14dff3c5628dee889b800246a   ✓ 完全一致
```

## 验证

| 项 | 结果 |
|---|---|
| 许可证正文与上游逐字一致 | ✓ MD5 相同 |
| 关键条款完整（PREAMBLE/DEFINITIONS/PERMISSION/TERMINATION/DISCLAIMER）| ✓ 8/8 |
| 1)~5) 五个条件齐全 | ✓ |
| README 引用的文件真实存在 | ✓ |
| 文件大小 | 5511 字节 / 122 行 |

## 教训

**「写了引用」≠「引用的东西存在」。**

这只是个低级错误，但它揭示了一个更大的问题：

**文档里提到某个文件时，应该自动检查该文件是否存在。**

这和 P44（文档里的旧数字要区分历史 vs 当前）是同一类：
**文档与产物的一致性需要主动验证，不能靠写的时候记得。**

## 另一个教训：法律文本不要手打

我第一次手写许可证时觉得「语义一样就行」，
但换行和 em-dash 都被我无意改动了。

**任何法律/协议文本，一律从权威来源逐字复制，并校验哈希。**
手打的版本可能看起来很对，但已经不是你声称的那份协议了。