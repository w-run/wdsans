# 曲线退化根因（2026-10-27）

## 现象

「岁」的撇渲染成折线；抽样 3000 字里有 41.8% 曲线数量减少。
与参数无关：`endsremoval` / `counter` / `flattenends` 怎么调都一样；
与 `align` 无关；与 `removeOverlap` 无关（Python 版根本没有它）。

## 定位过程

1. 模型直接重建（无任何变换）→ 已经是折线 → 问题在模型或重建
2. 打印 on/off 序列：
   - SHS 原始：`OOOO..O..O..OO..`（有曲线控制点）
   - 模型重建：`OOOOOOOOOOOO..O.`（12 个连续 on）
3. 统计模型里每个 on 点挂的 off 数量：`{1: 8 个, 2: 6 个}`
   → 三次贝塞尔每段必须 2 个 off，出现 1 个就是错配

## 根因

`src/cv/glyph_model.py` 的 `_build_glyph_model`：

```python
if previous_on:
    off_on_indices.append(len(on_pts) - 1)   # 第 1 个 off → 当前 on
elif pt_index == len(contour) - 1:
    off_on_indices.append(first_on_index)
else:
    off_on_indices.append(len(on_pts))       # ← 第 2 个 off → 下一个 on（错）
```

对 `on, off, off, on` 这段三次曲线：
- 第 1 个 off 正确指向当前 on
- 第 2 个 off 被指向 `len(on_pts)`，即**下一个 on 点**

`toGlyph` 重建时按 `offOnIndices[i] === onIndex` 连续取两个 off，
第二个来自下一段曲线 → 控制点错配 → 曲线被拉直。

`offOffsets` 也随之算错（相对下一个 on 点而不是当前）。

## 影响

全库所有含曲线的字形，曲线控制点均错配。
这解释了 41.8% 曲线丢失、以及「岁」「业」「丽」等字变形。

## 修复

```python
last_on = -1
for pt_index, pt in enumerate(contour):
    if pt['on']:
        last_on += 1
        ...
    else:
        off_on_indices.append(last_on)   # 两个 off 都归同一个 on
```

注意 contour 以 off 点开头的情况（曲线跨越起点），需单独处理：
首尾相接的 off 点应归到最后一个 on 点。

## 后续

修复后必须**重跑 CV**（模型提取），因为模型数据本身已经错了。
CV 需要 OpenCV + scikit-image，iSH 上不稳（segfault），当前只能在云端跑一次。
