# P40：把产物一致性审计嵌入构建流程

## 背景：同一个错误犯了两次

| 轮次 | 问题 |
|---|---|
| P35 | 改了母版后重建七档，VF WOFF2 漏了 |
| P39 | 改了 fsSelection 后重建 TTF，七档 WOFF2 全漏了 |

P35 时我写了 `wds/qa/audit_dist.py` 做一致性核对，但**没在重建后运行它**。
所以 P39 又漏了。

## 根因

**工具存在 ≠ 工具被使用。**
依赖「我记得跑一下」的方案，在压力下必然失效。

## 修法：嵌入构建收尾

`audit_dist.py` 增加 `check(master, dist)` API（返回不一致数量）：

```python
def check(master_path, dist_dir, verbose=False):
    """返回不一致的产物数量（0 = 全部一致）。供构建流水线调用。"""
    ...
    return bad
```

`deliver2.build()` 末尾自动调用：

```python
    try:
        from .qa import audit_dist
        bad = audit_dist.check(vf_path, out_dir, verbose=False)
        if bad:
            print("!! 产物一致性审计发现 %d 处不一致" % bad, flush=True)
        else:
            print("产物一致性审计：全部一致", flush=True)
    except Exception as e:
        print("!! 审计执行失败: %s" % e, flush=True)
```

这样每次构建都会自动报告，**不通过也不会静默通过**。

## 审计检查的指标

每个产物比对 4 项与母版是否一致：

| 指标 | 说明 |
|---|---|
| cmap 条目数 | 44,905 |
| Latin Ext-A 覆盖 | 125/128 |
| glyphs | 65,535 |
| fvar | 可变性（VF 必须有）|

覆盖 7 档 × (TTF + WOFF2) + VF WOFF2 = **15 个产物**。

## 教训升级

| 层级 | 做法 | 可靠性 |
|---|---|---|
| 差 | 靠记忆检查 | 低 |
| 中 | 有脚本但手动跑 | 中（会忘）|
| **好** | **嵌入流程自动跑** | **高** |

这次是第三次同类问题（P30 gvar、P35 WOFF2、P39 WOFF2），
前两次都只是「写了检查工具」，这次终于改成**强制路径**。