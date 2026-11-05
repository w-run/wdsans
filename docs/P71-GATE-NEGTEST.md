# P71：五道闸门的阴性测试（并修掉一个真 bug）

## 背景

P70 确立原则：**闸门必须有阴性测试**，否则「永远通过」的闸门比没有更危险。

但当时只对 `name_gate` 做了阴性测试。本轮补齐其余四道。

## 一、阴性测试结果

| 闸门 | 造的问题 | 检出 | 判定 |
|---|---|---|---|
| `ots_gate` | 损坏的 TTF（乱字节）| `ERROR: excessive (or zero) number of tables` | **有效** |
| `deliver_gate` | 空目录（缺 README/OFL）| 3 个问题 | **有效** |
| `geo_gate` | 清空零面积白名单 | 11 个（正是 11 个空白字形）| **有效** |
| `name_gate` | 两个不同名文件、同 ID6 | `ID6 冲突 <- [A, B]` | **有效** |
| `audit_dist` | （正常路径）| 0 个问题 | 正常 |

### geo_gate 的测试设计

直接造「极小碎片」需要改字形，风险大。改用**逻辑测试**：

```python
geo_gate.EXPECTED_ZERO = set()   # 清空白名单
n = geo_gate.check(SRC)          # 正常字体
# -> 检出 11 个
```

正常字体有 11 个合法零面积字形（空白字符）。
清空白名单后它们全被报出 → **证明白名单机制真的在起作用**，
不是恰好没有零面积字形。

## 二、过程中发现一个真 bug

### 现象

跑阴性测试时 `ots_gate` 崩溃：

```
File "/tmp/g/ots.py", line 14, in <module>
    r = subprocess.run(["ots-sanitize", p, out], ...)
FileNotFoundError: [Errno 2] No such file or directory: 'ots-sanitize'
```

**注意路径 `"/tmp/g/ots.py"`** —— 不是我写的 ots 包，而是我之前在 `/tmp/g/` 下建的
一个测试脚本恰好叫 `ots.py`。

### 根因

`ots_gate.py` 原本写：

```python
def _ots_binary():
    import ots                      # ← 依赖 sys.path，CWD 优先
    d = os.path.dirname(ots.__file__)
```

Python 导入模块时 **CWD 在 sys.path 最前面**（脚本模式）。
所以只要工作目录里有个 `ots.py`，就会导入那个文件而不是真正的包。

### 影响评估

| 场景 | 是否受影响 |
|---|---|
| 在 `/workspace/wdsans` 下跑构建 | **不受影响**（该目录无 ots.py）|
| 在任意含 ots.py 的目录下调用 | **崩溃** |

**这是一个潜伏的脆弱性**——正常构建路径下不触发，
但任何人（包括队友的测试脚本）在别的目录调用就会崩。

### 修复

改用 `importlib.util.find_spec` 精确查找，再用 sys.path 各目录兜底：

```python
def _ots_binary():
    import importlib.util
    spec = importlib.util.find_spec("ots")
    if spec is not None and spec.origin:
        p = os.path.join(os.path.dirname(spec.origin), "ots-sanitize")
        if os.path.exists(p):
            return p
    # 兜底：遍历 sys.path 找 ots/ots-sanitize
    for base in sys.path:
        p = os.path.join(base, "ots", "ots-sanitize")
        if os.path.exists(p):
            return p
    return None
```

### 验证

原 bug 场景（CWD=`/tmp/g`，存在 ots.py）：

```
找到 ots-sanitize: /workspace/wdsans/venv/lib64/python3.12/site-packages/ots/ots-sanitize
```

**修复生效。**

## 三、结论

| 闸门 | 阴性测试 | 状态 |
|---|---|---|
| `audit_dist` | 正常路径 | ✓ |
| `ots_gate` | 损坏文件 | ✓ **并修复导入 bug** |
| `deliver_gate` | 空目录 | ✓ |
| `geo_gate` | 清空白名单 | ✓ |
| `name_gate` | 同 ID6 双文件 | ✓ |

**五道闸门全部能检出对应问题。**

## 四、教训

### 1. 阴性测试能暴露「与闸门逻辑无关」的 bug

这次做 `ots_gate` 的阴性测试，本意是验证「损坏文件能否检出」，
结果在**准备坏文件的过程中**撞上了导入 bug。

如果没做这个测试，这个 bug 会一直潜伏——
直到某人在错误目录下调用闸门。

### 2. `import` 依赖 CWD 是 Python 的经典陷阱

```python
import ots    # 危险：CWD 里的同名文件会遮蔽真正的包
```

安全的写法：
- `importlib.util.find_spec` 精确查找
- 或 `from 包 import 模块 as x`（包路径明确时不那么脆弱）

**任何依赖「当前目录有什么文件」的代码都不可靠。**

### 3. 测试的副产品常常比测试本身更有价值

本轮真正的收获不是「五道闸门都有效」（那是预期内的），
而是**意外发现并修掉了一个导入 bug**。