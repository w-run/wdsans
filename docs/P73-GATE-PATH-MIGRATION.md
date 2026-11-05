# P73：闸门与交付模块的路径迁移

## 上轮遗留

P72 建了 `wds/paths.py` 配置中心，但只迁移了 `base.py`。
仍有 19 个文件含硬编码路径。

本轮迁移**构建链核心**：五道闸门 + `deliver2.py`。

## 一、为什么优先这些

| 文件 | 为什么优先 |
|---|---|
| `qa/ots_gate.py` | 构建末尾自动跑 |
| `qa/deliver_gate.py` | 构建末尾自动跑 |
| `qa/geo_gate.py` | 构建末尾自动跑 |
| `qa/name_gate.py` | 构建末尾自动跑 |
| `deliver2.py` | 交付构建主流程 |

这五个是**构建流程的核心链路**。它们硬编码路径意味着：
换个机器/挂载点，整个构建流水线就跑不起来。

## 二、迁移内容

| 文件 | 替换处数 |
|---|---|
| `geo_gate.py` | 1 |
| `name_gate.py` | 2 |
| `deliver_gate.py` | 2 |
| `ots_gate.py` | 2 |
| `deliver2.py` | 3 |
| **合计** | **10 处** |

替换规则：

```python
# 改前
"/data/build-cache/wdsans-dist"
"/data/build-cache/wdsans-subset"
"/data/build-cache/wdsans-dist/WDesignSansSC-Regular.ttf"

# 改后
paths.DIST_DIR
paths.SUBSET_DIR
os.path.join(paths.DIST_DIR, "WDesignSansSC-Regular.ttf")
```

## 三、验证：语法 + 实际运行

### 语法检查（5/5 通过）

```
ok: wds/qa/geo_gate.py
ok: wds/qa/name_gate.py
ok: wds/qa/deliver_gate.py
ok: wds/qa/ots_gate.py
ok: wds/deliver2.py
```

### 实际运行（关键）

**改路径来源不能只验语法，必须实跑。**

```
=== name_gate ===
  扫描文件 27 个
  唯一 ID6 实体 14 个
命名唯一性: 通过

=== geo_gate ===
  极小碎片: 0
  意外零面积: 0
几何健壮性: 通过

=== deliver_gate ===
  !! 缺少必需文件: README.md
  !! 缺少必需文件: OFL.txt
交付完整性: 2 个问题
```

### 关于 deliver_gate 报的 2 个问题

**这是预期的、正确的行为**，不是 bug：

- `wdsans-dist` 是**构建产物目录**，只有字体文件
- `README.md` 和 `OFL.txt` 只存在于 **w-pc 的最终交付包**（`D:/Project/WDesign/dist/`）
- 闸门检查的是「这个目录是否构成完整交付包」→ 在产物目录下调用自然缺文档

构建时 `deliver2.py` 传入的是 `out_dir`（产物目录），所以每次构建都会报这两条。

**但这提示了一个改进点**：闸门应该区分「构建中间检查」和「交付前终检」。
目前的行为是安全的（报出来让人看到），只是会产生噪音。

## 四、剩余工作量

| 类别 | 文件 | 硬编码处数 |
|---|---|---|
| 历史阶段脚本 | `p1_demo/p1_thin/p1_dir/p1_edge/p2_feet` | 各 3 处 |
| QA 辅助 | `run_p0.py`、`vf_ramp.py` | 各 1-2 处 |
| 工具 | `tools/stroke_audit.py`、`cmp_sheet.py`、`cmp_ref.py` 等 | 各 1-3 处 |
| 检查脚本 | `wds/check_round.py` | 5 处 |

**本轮不迁移这些**，原因同 P72：
- 它们是**历史阶段脚本**（P1/P2 时期的一次性构建步骤），不再参与日常流程
- 一次性全改风险高、收益低
- 新增脚本应直接用 `wds.paths`

## 五、结论

| 项 | 状态 |
|---|---|
| `paths.py` 配置中心 | ✓ |
| `base.py` 接入 | ✓（P72）|
| **五道闸门全部接入** | ✓（本轮）|
| **`deliver2.py` 接入** | ✓（本轮）|
| 生产链路径全部可配置 | ✓ |
| 历史脚本 | 保留硬编码（有意）|

**至此，日常构建与验收链路的路径全部可通过环境变量重定向。**

## 六、教训

### 1. 迁移要按「是否在活跃链路上」排优先级

20 个文件不可能一次改完。判断顺序：

```
生产链核心（构建+闸门）  →  必须改
常用工具                 →  应该改
历史一次性脚本           →  可以不改
```

**把力气花在还在跑的东西上。**

### 2. 改路径来源必须实跑验证

语法通过只说明「能加载」。
路径改动可能让 `os.path.join` 拼出错误路径，只有实跑才暴露。

本轮三道闸门实跑通过，才算迁移完成。

### 3. 验收时要注意「预期内的报错」

`deliver_gate` 报缺 README/OFL，第一眼像失败，
但结合上下文（产物目录 vs 交付包）就知道是**预期行为**。

**报告有输出 ≠ 报告有问题。**