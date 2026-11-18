# WDesign Sans v261118 存档

日期: 2026-11-19 03:59
链尾: masters_R32 = R31 + m_by0align

## 文件
```
WDesignSans-VF.otf               41,333,256 B   可变字体 250-900
WDesignSans-FlatApex-Regular.otf 17,915,572 B   静态平顶版
wd-preview.woff2                  2,246,736 B   预览子集 7600 字形
masters/                          三档 master + index.json
```

## 本版包含的全部修复
```
R15  = 基础链（barple 等 15 个模块）
R29  = R15 + punctscale + featlang + latinreset + digitnine + chufoot
R30  = R29 + m_spikefix6   眼字艮部撇尖 11 字
R31  = R30 + m_seamfix3    全库 20,479 字闭合轮廓缝隙归零
R32  = R31 + m_by0align    326 字 bar/body 接合点 y 跟随本档字重
```

## 验证状态
```
几何审计      15 项全通过
表与特性审计  17 项全通过
三档签名      R31/R32 均 0 不一致
永 seams      NONE（三档）
```

## 已知待修
```
1. 横折拐角撇偏粗
   250档撇厚 38（SHS 28），m_barple2 已写好待重建链

2. 部首出脚
   「都」左下日：右竖 y=-60 比外框 -16 低 44

3. 闭口偏旁垂直位置与高度
   「叫」口旁：我们 y[167,745] 高578 / SHS y[79,749] 高670
   「昨」日旁：我们 y[111,765] / SHS y[30,762]
   -> 偏旁被压扁约 90 单位且上移约 88 单位
```

## 回滚方式
```bash
cp archive/v261118/WDesignSans-VF.otf /workspace/static/wdsans/
cp archive/v261118/wd-preview.woff2 /workspace/static/wdsans/
cp archive/v261118/masters/*.otf /workspace/wdsans2/build/masters_R32/
```