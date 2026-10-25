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
