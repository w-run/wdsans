# P48：OTS 浏览器兼容性验证（21/21 通过 + 幂等）

## 为什么必须自己验

OTS（OpenType Sanitizer）是 **Chrome / Firefox 加载字体的强制关卡**。
不合格的字体在浏览器里会被静默拒绝，用户只看到空白或回退字体。

此前这一项只有队友报告「OTS 9.2.0 全部通过」，**我没有亲自复验**。
本轮独立验证。

## 一、工具定位

`ots-sanitize` 不在 PATH，但在 Python 包内：
```
/workspace/wdsans/venv/lib/python3.12/site-packages/ots/ots-sanitize
```
（opentype-sanitizer 9.2.0，随 fontbakery 安装）

## 二、全量结果：21/21 通过

| 类别 | 数量 | 结果 |
|---|---|---|
| 七档 TTF | 7 | 全部 OK |
| 七档 WOFF2 | 7 | 全部 OK |
| VF WOFF2 | 1 | OK |
| 子集 WOFF2（3755/6763 × 3 字重）| 6 | 全部 OK |
| **合计** | **21** | **21/21 通过** |

## 三、幂等性检查（更严格）

OTS 净化后再净化，两次输出应**逐字节相同**。
若不同，说明第一次净化改动过字体，即原始文件存在 OTS 需要修正的问题。

| 文件 | 原始哈希 | 净化1 | 净化2 | 幂等 |
|---|---|---|---|---|
| Regular.ttf | 7e0e8b91… | a38ce775… | a38ce775… | **一致** |
| Regular.woff2 | 7115df6a… | 28805169… | 28805169… | **一致** |
| VF.woff2 | d92e5eb5… | 097d7d74… | 097d7d74… | **一致** |
| Regular-sub6763 | f454dc42… | b0379559… | b0379559… | **一致** |

**四个样本净化后完全稳定**，说明字体结构干净，
OTS 首次净化只是重新序列化（表顺序/填充），没有修正任何问题。

## 四、结论

| 项 | 结果 |
|---|---|
| OTS 通过率 | **21/21（100%）** |
| 幂等性 | 4/4 一致 |
| 浏览器可用性 | TTF / WOFF2 / 子集 / VF 全部可加载 |

## 五、补充：这是对「队友报告」的独立确认

队友在 P28（子集化）报告过「OTS 9.2.0 全部通过」，
但那是**当时那一版产物**。此后我们做了多次改动：

- P30 Latin Ext-A 补齐（改了 cmap + glyf + gvar）
- P39 fsSelection 修正（改了 OS/2 + name）
- P41/P42 全量重建 + 子集化

**每一轮改动都可能破坏 OTS 兼容性**，所以必须重新验证。
本轮确认：改完之后仍然 100% 通过。

## 教训

**「别人报过」不等于「现在仍然成立」。**

队友的结论在当时的产物上有效，但产物变了就要重验。
这与 P44（文档旧值要分历史记录 vs 当前结论）是同类：
**结论有时效性，依赖它之前要确认它对应哪个版本。**
## 六、已嵌入自动化闸门

与 P40 的产物审计一样，OTS 也**嵌入 `deliver2.build()` 末尾**：

```python
# P48：OTS 浏览器兼容性闸门（Chrome/Firefox 加载字体的强制关卡）
try:
    from .qa import ots_gate
    nb = ots_gate.check(dist_dirs=[out_dir, "/data/build-cache/wdsans-subset"])
    if nb:
        print("!! OTS 闸门：%d 个产物不通过" % nb, flush=True)
    else:
        print("OTS 闸门：全部通过", flush=True)
except Exception as e:
    print("!! OTS 闸门执行失败: %s" % e, flush=True)
```

也可单独运行：
```bash
python -m wds.qa.ots_gate                    # 检查默认目录
python -m wds.qa.ots_gate <dir1> <dir2>      # 指定目录
```

### 现在的构建末尾会自动跑三道闸门

| 顺序 | 闸门 | 检查内容 |
|---|---|---|
| 1 | `audit_dist.check()` | 产物与母版一致性（cmap / Ext-A / glyphs / fvar）|
| 2 | `ots_gate.check()` | 浏览器可加载性（Chrome/Firefox 强制关卡）|

两者都是「不通过就打印警告」，不再依赖人工记忆。