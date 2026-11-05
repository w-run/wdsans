# P72：路径配置中心（消除硬编码可移植性隐患）

## 起因

P71 修掉一个「import 依赖 CWD」的脆弱性后，我顺着「代码依赖外部环境」这条线继续查。

结果发现更普遍的问题：**21 处硬编码绝对路径，分散在 16 个文件**。

```
"/workspace/wdsans/ref/ops/ops-400.ttf"      8 处
"/workspace/wdsans"                          8 处
"/workspace/wdsans/ref/NotoSansCJKsc-VF.ttf" 7 处
"/data/build-cache/wdsans-subset"            6 处
"/data/build-cache/wdsans-p1"                5 处
...
```

## 为什么这是问题

| 场景 | 后果 |
|---|---|
| 硬盘挂载点变化 | 21 处全要改 |
| 迁移到另一台机器 | 同上 |
| 想在临时目录测试 | 做不到 |
| 新增脚本 | 容易抄错路径 |

**构建/QA 工具恰恰最需要可移植性**——它们要能在任何环境跑。

## 一、设计：paths.py 配置中心

所有路径集中到一个模块，按优先级取值：

```
1. 环境变量（WDSANS_ROOT / WDSANS_CACHE）
2. 默认值（当前部署实际情况）
```

```python
ROOT  = os.environ.get("WDSANS_ROOT",  "/workspace/wdsans")
CACHE = os.environ.get("WDSANS_CACHE", "/data/build-cache")

# 参考字体
NOTO_VF = os.path.join(REF_DIR, "NotoSansCJKsc-VF.ttf")
MONA_VF = os.path.join(REF_DIR, "mona", "MonaSansVF.ttf")
OPPO_DIR = os.path.join(REF_DIR, "ops")
HOS_DIR  = os.path.join(REF_DIR, "hos")

# 构建产物
P0_DIR = os.path.join(CACHE, "wdsans-p0")
P1_DIR = os.path.join(CACHE, "wdsans-p1")
DIST_DIR = os.path.join(CACHE, "wdsans-dist")
SUBSET_DIR = os.path.join(CACHE, "wdsans-subset")
MASTER_VF = os.path.join(P1_DIR, "wdsans-FINAL.ttf")
```

附 `ensure_dirs()`（建目录）和 `summary()`（打印配置，可自检路径是否存在）。

## 二、验证 1：默认路径全部存在

```
[OK ] ROOT         /workspace/wdsans
[OK ] CACHE        /data/build-cache
[OK ] NOTO_VF      /workspace/wdsans/ref/NotoSansCJKsc-VF.ttf
[OK ] MONA_VF      /workspace/wdsans/ref/mona/MonaSansVF.ttf
[OK ] MASTER_VF    /data/build-cache/wdsans-p1/wdsans-FINAL.ttf
[OK ] DIST_DIR     /data/build-cache/wdsans-dist
[OK ] SUBSET_DIR   /data/build-cache/wdsans-subset
```

## 三、验证 2：环境变量真的能覆盖

**这是整个设计的价值所在**——如果环境变量无效，配置中心就只是换了种写法而已。

```bash
WDSANS_ROOT=/tmp/altroot WDSANS_CACHE=/tmp/altcache python -c "..."
```

结果：

```
ROOT  = /tmp/altroot
CACHE = /tmp/altcache
DIST  = /tmp/altcache/wdsans-dist
NOTO  = /tmp/altroot/ref/NotoSansCJKsc-VF.ttf
→ 环境变量覆盖生效
```

不带环境变量时：

```
ROOT  = /workspace/wdsans
DIST  = /data/build-cache/wdsans-dist
→ 默认值正确
```

## 四、验证 3：base.py 迁移后向后兼容

`wds/base.py` 是核心模块，所有脚本都 `from wds.base import SRC`。
改造时必须保证旧写法仍可用。

```python
from . import paths

# 基座路径统一由 wds.paths 提供（P72），可用环境变量 WDSANS_ROOT 覆盖
SRC = paths.NOTO_VF
```

验证：

```
SRC = /workspace/wdsans/ref/NotoSansCJKsc-VF.ttf   存在: True
STOPS: 7 档
WDSANS_ROOT=/tmp/xx → SRC = /tmp/xx/ref/NotoSansCJKsc-VF.ttf
```

**向后兼容 + 环境变量生效，两者都满足。**

## 五、当前进度与后续

| 项 | 状态 |
|---|---|
| `paths.py` 建立 | ✓ |
| 默认路径全存在 | ✓ |
| 环境变量覆盖 | ✓ 已验证 |
| `base.py` 接入（核心）| ✓ |
| 其余 15 个文件 | 待逐步迁移 |

**没有一次性改完 16 个文件**，理由：

- `base.py` 是绝大多数脚本的入口（`from wds.base import SRC`），收益最大
- 其余是历史阶段脚本（p1_*、p2_*），一次性改风险高、收益低
- 后续新增脚本应直接用 `wds.paths`

**关键路径先统一，历史脚本逐步迁移**——这是务实的取舍。

## 六、教训

### 1. 脆弱性往往成群出现

P71 发现「import 依赖 CWD」，顺着「依赖外部环境」查下去，
立刻又发现 21 处硬编码路径。

**同类问题不会只有一处。** 找到一个就该顺着模式搜一遍。

### 2. 配置中心的价值必须验证

如果只是把硬编码挪到另一个文件、仍然写死，那是**假重构**。

所以本轮专门验证：「环境变量能不能真的改变路径」。
能，才算真配置。

### 3. 迁移要保兼容

`base.py` 被十几个脚本依赖。直接改 `SRC` 的定义方式有风险。

做法：保留 `SRC` 这个名字，只改它的**来源**。

```python
# 改前：SRC = "硬编码字符串"
# 改后：SRC = paths.NOTO_VF     ← 名字不变，来源变了
```

所有 `from wds.base import SRC` 无需改动。