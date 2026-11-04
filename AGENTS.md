# AGENTS.md — wdsans 项目操作规约

> 本文件供 AI Agent 在本项目内操作时遵守。与 `docs/DESIGN.md` 冲突时，设计看 DESIGN，操作看本文。
> 本轮重构的完整背景与决策见 `docs/REBUILD-PLAN.md`。

---

## 0. 一句话

**WDesign Sans 是一套原生 TrueType 可变字体**：基座 Noto Sans CJK SC VF，拉丁 Mona Sans，
靠「只改 gvar 增量」实现形变 —— 绝不重建轮廓。

---

## 1. 铁律（违反即构建失败）

| # | 铁律 | 原因 |
|---|---|---|
| 1 | **只移动节点，绝不增删点** | 点数一变，VF 插值立刻不成立（旧版失败根因） |
| 2 | **不改 base 轮廓，只改 delta** | 保证跨字重拓扑天然一致 |
| 3 | **不删 cmap 条目** | 删一个码位 = 一个豆腐块 |
| 4 | **不裁 GSUB/GPOS feature** | 裁了就丢 `locl`、语言变体 |
| 5 | **禁止 GUI 手工修补** | 不可复现的修补必然在下轮丢失 |
| 6 | **数值不能代替看图** | 每轮必须出 PNG 并实际看过 |

---

## 2. 基座与产物

| 项 | 值 |
|---|---|
| 中文基座 | `ref/NotoSansCJKsc-VF.ttf`（Noto Sans CJK SC 2.004，原生 glyf+gvar） |
| 拉丁 | Mona Sans VF（`/usr/share/fonts/mona-sans/MonaSansVF[wdth,opsz,wght].ttf`） |
| 主轴 | `wght` 250–900，**默认 400**（Noto 原生默认是 100，必须重设） |
| 产物格式 | **只出 TrueType**（VF + 7 静态档）+ WOFF2。**不出 CFF/OTF** |
| 命名实例 | Thin250 / Light300 / Normal350 / Regular400 / Medium500 / Bold700 / Heavy900 |

---

## 3. 目录职责

```
wds/                 构建内核（Python）
  base.py            基座加载 + 轴重设 (min, default, max)
  contours.py        轮廓读取（点序 == glyf 点序）
  delta.py           ★ 增量形变引擎（本项目心脏）
  roles.py           笔画角色识别 → build/roles/*.json
  ops/l1_affine.py   L1 全局仿射算子
  ops/l3_stroke.py   L3 笔画级算子
  qa/gates.py        QA 闸门 G1–G5
  build.py           构建入口

contract/            轴/度量/特性契约（唯一真源，改这里等于改整个家族）
params/              语义参数 → 派生 7 档
docs/                设计宪法、管线、缺陷台账
ref/                 参照字体（不进 git）
vendor/glow-src/     ★ 上游源码，**只读参考，不参与构建**
```

---

## 4. 构建产物存放（遵守 w-box AGENTS.md）

- **代码** → `/workspace/wdsans`（SSD）
- **构建产物** → `/data/build-cache/wdsans-*`（HDD，可重建）
- 禁止把 `build/`、`dist/`、中间 JSON 放回 `/workspace`

---

## 5. 常用命令

```
cd /workspace/wdsans

# P0 全闸门验证（拓扑/往返/特性/cmap/结构）
/workspace/wdsans/venv/bin/python wds/qa/run_p0.py

# 构建（试验田子集）
/workspace/wdsans/venv/bin/python -m wds.build \
    --out /data/build-cache/wdsans-p0/wdsans-vf.ttf --subset

# 取静态实例做视觉样张
hb-view --variations=wght=400 --output-file=/tmp/x.png "永国口明湖烟电直"
```

---

## 6. 验证纪律

改任何算子后，**必须依次**：

1. `assert_same_shape()` 过 —— 点数/顺序/on-off 不变
2. `wds/qa/run_p0.py` 全绿
3. `hb-view` 出图，与 `ref/` 里参照字体并排看过
4. 记录到 `docs/REVIEWS/YYYY-MM-DD.md`

不满足 1–3 的改动，视为未完成。

---

## 7. 已知上游缺陷（不要重复踩）

详见 `docs/UPSTREAM-DEFECTS.md`。最要命的三条：

- glow-sans 用**固定 2° 直角容差**识别出脚 → 字重一变就失效（issue #2/#7/#28/#34）
- 去脚后只"降 1/4 脚高"补偿 → 口垫底字**整字飘起**（#7）
- 栅格化→CV→重描边 → **曲线必然被拉直**（#2/#34）

本项目的对策：几何不变量 + 角色 JSON + 增量位移，全部不依赖固定阈值。
