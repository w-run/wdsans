# P70：命名唯一性闸门（含阴性测试）

## 为什么需要

P67/P69 连续两轮发现命名冲突：

| 轮次 | 问题 |
|---|---|
| P67 | VF 与静态 Regular 的 ID6 完全相同 |
| P69 | 子集 12 个文件与全库同 ID6，且 3755/6763 互相也撞 |

**这类问题不会自己暴露**——字体能加载、能渲染、OTS 也通过，
只在「同时安装」时才出问题（互相覆盖 / 只显示一个）。

所以必须做成闸门。

## 一、判定口径（关键设计）

**同一个字体的 TTF 与 WOFF2 必须同名**——它们是同一内容的不同封装。

所以唯一性按「内容实体」判断，而非按「文件」：

```
忽略扩展名，同 basename 的 ttf/woff2 视为同一实体
不同 basename 但 ID6 相同  →  冲突
```

这个口径很重要。P69 第一次检查就是错在这里，
把 TTF 和 WOFF2 当两个字体，报出「6/12 重复」的假警报。

## 二、实现

```python
owners = {}   # ID6 -> [(stem, path)]
for p in files:
    id6 = TTFont(p, lazy=True)["name"].getDebugName(6)
    stem = re.sub(r"\.(ttf|woff2)$", "", os.path.basename(p))
    owners.setdefault(id6, []).append((stem, p))

conflicts = []
for id6, items in owners.items():
    stems = {s for s, _ in items}
    if len(stems) > 1:              # 多个不同实体共用同一 ID6
        conflicts.append((id6, sorted(stems)))
```

## 三、阳性结果

```
扫描文件 27 个
唯一 ID6 实体 14 个
命名唯一性: 通过
```

14 = 全库 7 档 + VF 1 个 + 子集 6 档。

## 四、阴性测试（关键）

**「通过」可能是闸门失效导致的假通过。** 必须验证它能抓到真问题。

做法：复制同一个 TTF 成两个不同文件名，ID6 必然相同：

```python
shutil.copy(Regular.ttf, TMP + "/FAKE-A.ttf")
shutil.copy(Regular.ttf, TMP + "/FAKE-B.ttf")
name_gate.check(TMP)
```

结果：

```
!! ID6 冲突: WDesignSansSC-Regular <- ['FAKE-A', 'FAKE-B']
扫描文件 2 个
唯一 ID6 实体 1 个
检出冲突数: 1  ->  闸门有效
```

**闸门确实能抓到冲突，不是摆设。**

## 五、已接入构建

`deliver2.build()` 末尾，现在是**第五道闸门**：

| 顺序 | 闸门 | 检查 |
|---|---|---|
| 1 | `audit_dist` | 产物与母版一致性 |
| 2 | `ots_gate` | 浏览器可加载性 |
| 3 | `deliver_gate` | 交付包完整性 + 版权声明 |
| 4 | `geo_gate` | 几何健壮性（零塌缩/碎片）|
| 5 | **`name_gate`** | **ID6 全局唯一（防安装覆盖）** |

## 六、教训

### 1. 闸门必须有阴性测试

一个「永远返回通过」的闸门，比没有闸门更危险——
它会给人虚假的安全感。

**每个闸门都该问一句：如果真有这个问题，它能发现吗？**

### 2. 静默问题最需要闸门

命名冲突的特点是：
- 字体能加载 ✓
- 能正常渲染 ✓
- OTS 通过 ✓
- **只在「同时安装」时出问题** ✗

越是这种「平时都正常」的问题，越要靠自动化检查兜底。