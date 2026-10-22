# WDesign Sans (wdsans)

基于思源黑体 2.005 改造的中文可变字体。中文为主，拉丁取自 Mona Sans。

## 文档（权威顺序）

1. **[docs/DESIGN.md](docs/DESIGN.md)** — 设计宪法：定位、命名、7 档字重、视觉决策的可测参数、许可红线
2. **[docs/PIPELINE.md](docs/PIPELINE.md)** — 技术管线：VF-first、四算子、QA 闸门、里程碑、风险表
3. **[docs/PARAMS.md](docs/PARAMS.md)** — 参数体系：旧版诊断、新版目标值、算子实现状态
4. **[docs/POSTMORTEM-v2025.060.md](docs/POSTMORTEM-v2025.060.md)** — 旧版失败复盘（实测数据）

## 工具

```
tools/transforms.py     形变算子（face / spread / gravity / soften / stroke）
tools/canonical_cff.py  确定性 CFF2 字串编码（保证跨 master 点结构一致）
tools/raster.py         非零环绕光栅器
tools/specimen.py       样张渲染
tools/compare.py        A/B 对比渲染
tools/p0_pipeline.py    P0 管线：VF → master → 形变 → 重建 VF
```

## 铁律

1. 只移动节点，不重建轮廓 —— 否则可变字体不成立
2. 不裁剪 GSUB 白名单，不删 cmap 条目
3. 一切改动进脚本、进 git，禁止 GUI 手工修补
4. **数值测量不能代替看图** —— 每轮必须出图并实际看过

## 底座

- Source Han Sans 2.005R (OFL 1.1, RFN "Source")
- Mona Sans (OFL 1.1, RFN "Mona")
