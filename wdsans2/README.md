# wdsans2 — WDesign Sans 字形改造流水线

基于 Source Han Sans 2.005 改造成 OPPO Sans 风格的 CJK 字体工程。

## 核心思路

SHS 提供完整覆盖（20,992 CJK）和宽松协议（OFL），
但其笔画里藏着大量装饰性残留（横线出头、台阶、端面凹陷）。
本项目用**模块化几何修复**逐类消除，参考 OPPO/HOS 的字形比例。

## 流水线架构

**400 档驱动**：因为 VF 构建要求三档段数与操作符完全一致，
所有检测只在 400 档做一次，输出索引 JSON，再套用到 250/900。

```
detect(400) → idx_*.json → apply(250/400/900) → gate → VF build → deploy
```

## 模块

| 模块 | 作用 | 规模 |
|---|---|---|
| `m_taper.py` | 撇/提/捺末端收窄 NARROW=0.95 | 45,611 处 |
| `m_stepalign.py` | 相邻轮廓台阶对齐 | 2,947 处 |
| `m_barple.py` | 横线右端对齐撇右界 + 落点下移 + 删回折段 | 6,595 字 |
| `m_termface.py` | 笔端面微弧拉直（C→L） | 19,546 字 |
| `m_bardiag.py` | 横线右端延伸到斜边外缘 | 3,077 字 |
| `m_yanrad.py` | 廴/辶旁顶端尖角消除 | 62 字 |

## 工具

| 工具 | 用途 |
|---|---|
| `glyphview.py` | **唯一渲染入口**：整字/网格/区域裁剪/多字体/可变字重 |
| `crop.py` | 按 bbox 比例裁剪 |
| `labelpts.py` | 锚点编号标注 |
| `labelpath.py` | 轮廓路径 + 锚点编号 |
| `gate.py` | **部署门禁**：零长度段 / 包围盒漂移 / 三档签名 |
| `run_module.py` | 400 档驱动执行器 |
| `run_bardiag.py` | bardiag 三档应用 |
| `run_yanrad.py` | yanrad 三档应用 |

## 部署门禁（缺一不可）

```bash
python modules/gate.py <改前目录> <改后目录>
```

- **G1 零长度段**：改后不得比改前多（防笔画塌缩）
- **G2 包围盒漂移**：每字 ≤ 0.6×SW
- **G3 三档签名**：250/400/900 操作符序列完全一致

> 2026-11-15 事故：bardiag 的 `apply()` 把横线左端点也一起平移，
> 导致 3,076 字横画塌缩成零长度并已部署。回滚后新增 gate.py，
> 用事故版本反测确认 G1 报 3076 字 FAIL。

## 基座链

```
masters_T6    SHS + taper + step-align + 乙乞
masters_MOD   + m_barple    6,595 字
masters_MOD2  + m_termface 19,546 字
masters_MOD4  + m_bardiag   3,077 字
masters_MOD5  + m_yanrad       62 字   ← 当前已部署
```

## 详细规范

见 [AGENTS.md](AGENTS.md)（判据、踩坑清单、验证流程）。

## 许可

字体部分遵循 SIL Open Font License 1.1（继承 Source Han Sans）。
