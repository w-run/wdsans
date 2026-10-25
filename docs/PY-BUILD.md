# Python 构建链（脱离 Node）

## 为什么

iSH 上 Node 跑 `buildFont()` 约 2000 个字形后进程级崩溃（无错误栈）；
`otfccdump` 处理 8.7MB 字体也 segfault。两者都是 C/运行时层问题，无法在应用层修复。

## 现状

| 模块 | 状态 |
|---|---|
| `GlyphModel.restore` | ✅ 与 JS **逐点一致**（62 点，最大差 0） |
| `ModelFilters` 7 个形变 | ✅ 串联后仍逐点一致 |
| 表构造 | ✅ 用 fontTools FontBuilder，模板继承 GSUB/GPOS/GDEF/BASE |
| `PostFilters`（端点处理） | ❌ 未移植 → 出脚/喇叭口暂未去除 |

## 关键实现点

1. **模型 key 是 `uniXXXX`，模板字形名是 `cidXXXXX`** —— 必须用码位做桥：
   `cp_of[uniXXXX] = 码位` → `tpl_cmap[码位] = cidXXXXX`
2. 模板的表（GSUB/GPOS 等）**只在全量构建时复制**，裁剪模式会因引用缺失字形报 KeyError
3. 坐标与 JS 一致：`restore` 后 `y -= baseline`

## 性能（iSH）

| 操作 | 耗时 |
|---|---|
| 单字形 restore + filter + charstring | 4.2 ms |
| 单个分片（1024 字）完整构建 | 8.4 s |
| 全量 31,962 字（估算） | 约 5 分钟 |

对比 Node 版：云端 135 s/档，iSH 上会崩。

## 用法

```bash
python3 wds_py/build.py \
  --weight Regular \
  --template build/v1/meta/WDesignSans-Regular.otf \
  --out /tmp/py_reg.otf [--shards 07,08] [--limit N]
```

## PostFilters 移植（2026-10-26）

与 JS **逐点一致**（3 轮廓 / 56 点 / 最大差 0）：
- `detect_feet` / `is_left_foot`（7 点窗口 + 镜像检测，含「月」「非」特例）
- `remove_feet` → `sink_feet`（下沉到下沿）
- `stroke_ends_flatten`（末端压平 + 可选删 off 点）
- `soften_dots` / `is_dot` / `hook_tension`
- `round` / `translation` / `scaling` / `merge`

## 性能现实（iSH）

| 项 | 实测 |
|---|---|
| 单字形（restore + 7 filter + post + 编译） | **144 ms** |
| 5120 字（单进程） | ≈ 17 分钟 |
| 全量 31,962 字 | **约 77 分钟/档** |
| fork 多进程 | **无加速**（user 2m44 vs real 17m48，CPU 15%） |

原因：iSH 的 Python 跑在模拟层，GIL + fork 都不能真正并行；`copy.deepcopy` 曾占 54%，
换成手写浅拷贝后降到 144ms。

## 可行的构建规模

| 范围 | 字形数 | 单档耗时 |
|---|---|---|
| GB2312（一级+二级） | 6,763 | ≈ 16 分钟 |
| 常用扩展（gid-07~22） | 16,384 | ≈ 40 分钟 |
| 全量 | 31,962 | ≈ 77 分钟 |

七档全量 = 约 9 小时。建议先出 GB2312 子集（覆盖日常 99.9% 文本），
再加 `unicode-range` 分片按需加载。
