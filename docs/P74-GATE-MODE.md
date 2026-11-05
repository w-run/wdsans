# P74：deliver_gate 双模式（并修掉自己在模式化中引入的漏洞）

## 起因

P73 迁移路径时发现一个噪音问题：`deliver_gate` 每次构建都报
「缺少 README.md / OFL.txt」，但那是**预期行为**（产物目录不含文档）。

噪音的危害：**真问题会被淹没在例行的假警报里**。

## 一、加 mode 参数

交付目录有两种形态，检查项应该不同：

| mode | 场景 | 检查项 |
|---|---|---|
| `"build"` | 构建产物目录（只有字体）| 字体存在性 + 版权声明 |
| `"package"` | 最终交付包（含文档）| 全部（默认）|

```python
def check(dist_dir, subset_dir=None, verbose=False, mode="package"):
```

CLI 也支持：
```bash
python -m wds.qa.deliver_gate --build      # 中间检查
python -m wds.qa.deliver_gate              # 终检
```

## 二、第一轮验证：两种模式都对

```
build 模式（产物目录）    → 交付完整性: 通过
package 模式（产物目录）  → 2 个问题（缺 README/OFL）  ← 预期
```

看起来改得很成功。

## 三、但进一步测发现一个漏洞

我接着测「build 模式会不会漏掉真问题」，构造了空目录：

```
正常字体 build 模式: 0 个问题
空目录   build 模式: 0 个问题     ← **这里不对！**
```

**空目录也报 0 个问题。**

### 根因

为了消除噪音，我把「必需文件检查」整个塞进了 `if mode == "package"`。

但 `REQUIRED` 里除了 README/OFL，还隐含了「目录里总得有字体」这个前提。

build 模式跳过整块检查后，**连「一个字体都没有」都发现不了**。

### 这是我自己引入的漏洞

改之前 `deliver_gate` 在空目录下会报 2 个问题（缺文档），
虽然理由不对，但**至少报了**。

改之后报 0 个——**为了消除噪音，把信号也一起删了**。

## 四、修复

加一条**两种模式都执行**的检查：

```python
# 0. 两种模式都要求：至少存在一个字体文件
fonts_here = sorted(glob.glob(os.path.join(dist_dir, "*.ttf"))) + \
             sorted(glob.glob(os.path.join(dist_dir, "*.woff2")))
if not fonts_here:
    problems.append("目录内没有任何字体文件: %s" % dist_dir)
```

## 五、修复后验证

```
正常产物 build   : 0 个问题           ← 噪音消除
空目录   build   : 1 个问题           ← 真问题仍能发现
空目录   package : 3 个问题           ← 文档 + 字体双重检查
```

三种情况都正确。

## 六、构建流程改用 build 模式

```python
# wds/deliver2.py
np = deliver_gate.check(out_dir, paths.SUBSET_DIR, mode="build")
```

构建时不再刷出「缺文档」的假警报。

## 七、教训

### 1. 消除噪音时，要检查是否连信号一起删了

这是本轮最重要的教训。

我的改动逻辑是「package 才查必需文件」——听起来合理。
但 `REQUIRED` 这个检查**混装了两种性质**：

| 项 | 性质 |
|---|---|
| README.md / OFL.txt | **交付包专属**，build 时不该查 |
| 「目录里得有字体」 | **通用前提**，任何模式都该查 |

把它们打包进同一个 `if`，就把通用前提一起跳过了。

**降噪的前提是分清「哪些是真噪音、哪些是信号」。**

### 2. 改完要测「反向用例」，不只测「正向用例」

我的第一轮验证只测了：
- build 模式 + 正常目录 → 通过 ✓
- package 模式 + 正常目录 → 报缺文档 ✓

**两个都是「预期内的正常情况」。**

直到测「build 模式 + 空目录」才暴露漏洞。

**新功能的验证必须包含「它应该报错的情况」。**
这是 P70/P71 阴性测试原则的又一次应用——
只不过这次，漏做阴性测试的是我自己刚写的改动。