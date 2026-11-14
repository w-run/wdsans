# WDesign Sans 字形改造流水线

基座: `build/masters_T6` — SHS 2.005 + taper + step-align + 乙乞修复（当前部署版）
三档: 250 / 400 / 900。**修改必须三档同步**，否则 VF 构建报 `VarLibCFFPointTypeMergeError`。

## 模块清单

每个模块一个文件，统一接口：

```python
NAME = '模块名'                      # 用于日志
def find(C, sw) -> list[hit]         # C=轮廓列表, sw=StemWidth
def apply(C, hits) -> NEW            # 返回新轮廓列表
```

| 模块 | 文件 | 作用 | 规模 | 状态 |
|---|---|---|---|---|
| 撇捺收窄 | `m_taper.py` | 撇/提/捺末端收窄 NARROW=0.95 | 45,611 处 | 已部署 T6 |
| 台阶对齐 | `m_stepalign.py` | 相邻轮廓边缘微差对齐 | 2,947 处 | 已部署 T6 |
| 乙乞钩 | `m_yiqi.py` | 乙/乞 钩尖越界 | 2 字 | 已部署 T6 |
| 横线撇根 | `m_barple.py` | 横线右端对齐撇右界 + 落点下移 + 删回折段 | ~6,595 字 | 本次 |

## 执行

```bash
export WDS_BASE=/workspace/wdsans2/build/masters_T6
export WDS_OUT=/workspace/wdsans2/build/masters_MOD
for t in 250 400 900; do
  /workspace/wdsans/venv/bin/python -u modules/run_module.py m_barple $t
done
```

单字调试：

```bash
/workspace/wdsans/venv/bin/python -u modules/run_module.py m_barple 400 永
```

## m_barple.py 参数（E3 定稿，RATIO=0）

用户已确认：**不做根部收窄**，只做三步。

```
1. bar 右端 → xR                     横线右对齐到撇右界
2. body 倒数第2段终点 → (xR, bar.bottom)   落点下移到横线右下角
3. 删除回折段
```

其中 `xR` = 横线底边 y 处撇轮廓的最右交点。

**验证通过（11/11）**：永 今 亨 夕 多 了 互 乳 亂 延 各
**未命中（另一结构类）**：丝 — 纟旁拐角，待另立模块

## 关键教训（踩过的坑）

1. **落点必须取倒数第 2 段终点** — 末段是回折段，取其终点会使 dx/dy 全超范围，导致整字漏检。
2. **左边界 j 要排除末段并取最短** — 否则被回折段覆盖，`cap` 变负，补偿完全失效。
3. **容差按横线高度而非 SW** — 250 档 SW=30 时 `0.25*SW=7.5` 过严，改用 `max(0.25*SW, 0.40*横线高)`。
4. **不要移动主边终点** — 会拉细笔画（`了` 字教训），只做横线对齐 + 落点下移。
5. **基座必须用 T6，不能用 T7** — T7 含已被改坏的 `永`，会导致判据只在"已修"状态成立。
