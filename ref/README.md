# ref/ — 参照字体

> 只放**参照用**字体。基座与参照的区别见 [../docs/DESIGN.md](../docs/DESIGN.md)。
> 这些文件**不进 git**（总体积约 300MB），用 `fetch.sh` 重新获取。

## 命名约定

```
ref/<family>/<family>-<weight>.{otf,ttf}     静态字重
ref/<family>/<family>-vf.{otf,ttf}           可变字体
```

`<weight>` 用**该字体自己声明的实际数值**（1–1000），不是档位序号。

| 缩写 | 全名 | 角色 |
|---|---|---|
| `shs` | Source Han Sans SC | **基座**（唯一可改造对象） |
| `hos` | HarmonyOS Sans SC | 参照（只看不改） |
| `ops` | OPPO Sans | 参照（主参照） |
| `wdo` | WDesign Sans 旧版 | 历史版本，用于对比 |

---

## 现状清单

### shs — Source Han Sans SC（基座，OFL 1.1，RFN "Source"）

| 文件 | 大小 | 字形 | CJK | 说明 |
|---|---|---|---|---|
| `shs-vf.otf` | 31.7MB | 65535 | 20992 | **wght 250–900**，CFF2 |
| `shs-250.otf` | 14.2MB | — | — | ExtraLight |
| `shs-300.otf` | 15.7MB | — | — | Light |
| `shs-350.otf` | 15.8MB | — | — | Normal |
| `shs-400.otf` | 15.8MB | — | — | Regular |
| `shs-500.otf` | 15.8MB | — | — | Medium |
| `shs-700.otf` | 15.8MB | — | — | Bold |
| `shs-900.otf` | 16.8MB | — | — | Heavy |

来源：`adobe-fonts/source-han-sans` 2.005R 的 `01_SourceHanSans.ttc.zip`（静态）+ `Variable/OTF/SourceHanSansSC-VF.otf`

### hos — HarmonyOS Sans SC（参照，免费商用但不开放修改）

| 文件 | 大小 | 字形 | CJK | 说明 |
|---|---|---|---|---|
| `hos-vf.ttf` | 20.6MB | 29824 | 20992 | **wght 40–900** |
| `hos-250/300/400/500/700/900.ttf` | ~8MB/个 | 29221 | 20902 | 静态 |

来源：`kanami09/HarmonyOS-Sans-Font`（VF）、`ajacocks/harmonyos-sans-font`（静态）

> ⚠️ VF 与静态的字形数不同（29824 vs 29221），说明它们不是同一次构建。
> **做参照测量时优先用 VF**，静态只用于交叉验证。

### ops — OPPO Sans（参照，主参照）

| 文件 | 大小 | 字形 | CJK | 说明 |
|---|---|---|---|---|
| `ops-300.ttf` | 2.3MB | **7718** | **6763** | ⚠️ 精简版，只有 GB2312 一级字 |
| `ops-400.ttf` | 10.2MB | 28488 | 20902 | 完整 |
| `ops-500.ttf` | 10.1MB | 28488 | 20902 | 完整 |
| `ops-700.ttf` | 9.9MB | 28488 | 20902 | 完整 |
| `ops-900.ttf` | 2.2MB | **7718** | **6763** | ⚠️ 精简版 |

来源：`cooingwu/OPPO-Sans`

> ⚠️ 两个坑：
> 1. **L / H 是精简版**（只 6763 字），R / M / B 才完整。不能用 L/H 做全字库统计。
> 2. 所有文件的 `OS/2.usWeightClass` 都写成 **400**，和文件名不符。
>    按字重筛选时不要信这个字段，以文件名为准。
> 3. 没有 CJK 可变字体。`OPPOSans3-VF.ttf` 只有拉丁（826 字符、无 CJK），不建议放进来。

### wdo — WDesign Sans 旧版（历史版本，仅供对比）

| 文件 | 大小 | 字形 | CJK |
|---|---|---|---|
| `wdo-250/300/350/400/500/700/900.ttf` | ~10MB/个 | 31916 | 20972 |

来源：`/var/minis/shared/wdsans202506/`（已废弃项目）

> 全部为静态 TTF，**没有可变字体**（这正是它被放弃的原因之一）。
> 字形数为 31916 但实际可用 CJK 20972，其余是符号与扩展区。

---

## 重新获取

```bash
sh ref/fetch.sh
```

脚本会按上面的来源重新下载/导出。**shs 的静态字重需要本地已有 TTC**，
没有时会先从 Release 下载 95.8MB 的合集包。

---

## 使用约定

1. **只有 shs 可以被改造**；hos / ops 只做测量与目视对照。
2. 任何跨字体的量化统计，**先确认两边 CJK 覆盖率一致**（用 `shs` 与 `ops-400/500/700` 比；
   `ops-300/900` 只适合抽样）。
3. 拿 VF 做统计时，先实例化到固定字重再量，不要直接量 VF 的默认实例。
