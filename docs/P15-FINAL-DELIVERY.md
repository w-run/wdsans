P15：最终交付重建 + 全量验收（149 轮修复收官）

## 交付产物

/data/build-cache/wdsans-dist/（重建耗时 2145s）

| 文件 | 大小 |
|---|---|
| WDesignSansSC-{Thin,Light,Normal,Regular,Medium,Bold,Heavy}.ttf | 20.93~21.00 MB |
| 对应 .woff2 | 7.49~7.94 MB |
| WDesignSansSC-VF.woff2 | 20.04 MB |

母版：/data/build-cache/wdsans-p1/wdsans-FINAL.ttf（50,323,956 B，已含 P13 复合字形修复）

## 终检验收（全部通过）

```
档位      A宽   Á宽   wClass  H adv  H目标  rev   fsSel      判定
Thin     618   618   250     690    690    1.0   0b0        OK
Light    621   621   300     691    691    1.0   0b0        OK
Normal   631   631   350     694    694    1.0   0b0        OK
Regular  636   636   400     696    696    1.0   0b1000000  OK
Medium   649   649   500     700    700    1.0   0b0        OK
Bold     667   667   700     706    706    1.0   0b100000   OK
Heavy    684   684   900     712    712    1.0   0b0        OK
```

- H advance 单调递增 690→712，与 Mona×0.895 逐档吻合
- A/Á 宽度七档全部相等（复合字形内联正确）
- head.fontRevision 统一 1.0（P12 修复保留）
- fsSelection 仅 Regular(bit6) / Bold(bit5) 单独置位
- 曾错位的 10 个复合字形：静态与 VF 逐档一致，0 处不符
- VF 斜坡：H 690/696/712，中文「国」恒为 1000（未受拉丁合并影响）

## fontbakery 复验

FAIL 从 **5 类降到 2 类**：
```
FAIL zero advance width: uni20DD    <- 组合记号，本就零宽（Noto 同样）
FAIL massive-font 21MB > 9MB       <- 65k 字形全字库必然
```
`head version mismatch` 与 `fsSelection Regular flag` 均已消失。

## 视觉验收

docs/img/p13-textsample.png：12/16/24/48px 四档样张
- 12px 正文清晰，中文小字不糊
- 16px 中英混排节奏均匀
- 48px 大字 `i j 9 : ;` 间距正常（P13 修复的直接验证）

## 本轮（P12~P15）修掉的三个真缺陷

1. **head.fontRevision 与 name ID5 不一致**（2.004 vs 1.000）
2. **OS/2.fsSelection == 0b0**（Windows 无法识别 Regular）
3. **138 个复合字形 advance 未按 0.895 缩放**（400 档偏差恒为 -12/-13）

## 同时否决的一个错误建议

队友建议移植 Mona 的 kern 表。实测间距我们**优于 Noto 原版**、接近 Mona，
「比 Mona 紧 15 units 以上」的字对为 0/8。详见 P14。