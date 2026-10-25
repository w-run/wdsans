# 字形指纹质检（qa/fingerprint.py）

## 为什么需要它

视觉判断能**发现问题**，但不能**验证问题**。所有"看着不对"必须先翻译成可计算量：

| 视觉感受 | 可计算量 |
|---|---|
| 变形/歪了 | 控制点坐标 diff、段方向角序列 |
| 曲线变硬 | 显著曲线（控制点偏离弦 >5 单位）的数量 |
| 出脚/喇叭口 | 端点区域面积、端点法向与笔画走向夹角 |
| 粗细不均 | 沿骨架的笔宽标准差 |
| 字面大小 | bbox 中位数、墨面积占比 |
| 断开/穿孔 | 轮廓数、绕向、孔洞奇偶 |

## 用法

```bash
python3 qa/fingerprint.py \
  --ref ref/shs/shs-400.otf \
  --cur build/v1/meta/WDesignSans-Regular.otf \
  --limit 3000 --report build/qa/regular.json
```

指纹字段：`contours / lines / curves / sharp / area / winding / bbox / w / h`

**`sharp` 是关键**：只数"控制点偏离弦 > 5 单位"的曲线。近直线被优化掉是无损的，
不算退化。不加这个判据，异常率会虚高（55.67% vs 54.43%）。

## 首轮实测（SHS 400 vs 我们的 Regular，3000 字）

```
total 3000 | critical 423 (14.1%) | warn 1210 (40.3%) | ok 1367 (45.6%)
异常率 54.43%
类型分布: 显著曲线丢失 1342 | bbox 300 | 轮廓数 166 | 面积差 42
```

最严重：`业 4→0`、`丫 4→1`、`丯 10→4`、`丽 10→6`

## 根因定位

`src/font-build/glyph-filters.js` → `model2Glyph()` 的最后一步：

```js
const merged = caryllShapeOps.removeOverlap(transformed,
  fillRule = caryllShapeOps.fillRules.nonzero);
```

**`removeOverlap` 是轮廓布尔运算，clipper 用多边形近似曲线**——曲线就是在这一步被展平的。

已验证与参数无关（`endsremoval=false`、`counter=1.0` 产出的字形完全一样）。

## 待验证的修复

代码已改为：

```js
const merged = process.env.WDS_NO_MERGE
  ? transformed
  : caryllShapeOps.removeOverlap(...);
```

**下一步**（环境恢复后）：

```bash
WDS_NO_MERGE=1 WDS_OUT=build-nm node scripts/wds_build.js 400
python3 qa/fingerprint.py --ref ref/shs/shs-400.otf \
  --cur build-nm/WDesignSans-Regular.otf --limit 3000
```

预期：显著曲线丢失大幅下降。若成立，说明 41.8%/54.43% 主要是这一个操作造成的，
A 路线的定位要重估。

风险：SHS 原字形若有重叠轮廓，不合并会导致非零填充规则下出现实心块。
需要抽查有重叠的字（如「辶」「廴」类）确认。
