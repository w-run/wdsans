# WDesign Sans · 项目状态
> 个人使用 · Source Han Sans 2.005 (OFL) + Mona Sans (OFL)

## 一、目标
构建 OPPO Sans 风格 CJK 可变字体。参考 OPPO/HOS 的笔画风格，但不采样其轮廓。

## 二、已验证结论

### 架构
- 3 档 master（250/400/900）+ 插值
- CanonicalPen 写 CFF2（仅 rmoveto/rlineto/rrcurveto）
- post formatType=3.0（65535 字形超 post 2.0 上限）
- 拉丁用 VF 实例化后转 CFF2

### 已修复的坑
1. T2CharStringPen 拓扑不一致 -> CanonicalPen
2. CanonicalPen 隐含闭合段 -> 不追加闭合段
3. post 2.0 溢出 -> 强制 3.0
4. varLib.build 需 designspace 路径（fontTools 4.67）
5. qCurveTo 多点：N 点=N-1 控制点+1 终点，相邻控制点中点为隐含 on-curve 点
6. 顶部提升方向错误：去出脚后空隙在下半部，应向下落
7. 坐标重复累加：set_y 后再 shift 同批点 -> 飞出 em 框

### 去出脚判据（feetFINAL.py）
```
出脚 = 轮廓底部的「竖-短横-竖」U 形凸起
1. 横边长 0.35*sw ~ 1.8*sw
2. 横边 y 在字底部 1.0*sw 内
3. 前后各接竖边，竖边向上延伸到轮廓顶 1.5*sw 内
4. 轮廓高度 > 5*sw
黑名单（单竖笔收笔）：王 生 川 中 申 甲 十 用 主 玉 土 干 工 丰 士 卅 三
```

验证：口2 日2 田2 国2 白2 目2 百2 回2 四2 品4 晶4 凸2 凹2 础2 吕2 古2 石2 右2 全对；艹0 草0 王0 生0 零误检。全库 1677 字 / 2368 处。

### 补偿（footfix.py，按用户规则）
```
1. 出脚点抬到参照横边 y（去出脚）
2. 框轮廓下移 delta（拉低两侧竖线）
3. 底横轮廓下移 delta（拉低本体横线）
4. 内部内容下移 delta/2（保持垂直居中）
delta = OPPO 目标高 - 去脚后高
```

400 档验证（upm）：口 791->706->755 vs OPPO 755 误差0；田 843->781->802 vs 802；国 875->824->849 vs 849；回 878->825->832 vs 832；四 800->724->797 vs 797；凹 810->731->819 vs 819。

**覆盖率 813/1677 字（49%）**，其余需跨轮廓参照未处理。

## 三、产物
- build/masters/ 原始 7 档 pristine
- build/masters13/ 当前最佳：3 档，去出脚 813 字 + 拉丁 238 字
- build/WDSans-v2.otf VF 输出
- build/WDSans-v1.otf 上一版（未去出脚）

## 四、预览
http://box.w-run.net/wdsans/

## 五、未完成
1. 去出脚覆盖 49%，啊/阿 等需跨轮廓参照
2. 喇叭口：SHS 无，OPPO 有
3. 笔末切角：SHS 圆头，OPPO 平直
4. 折角：SHS 圆角，OPPO 锐利
5. 撇捺曲率：未测量
6. 重心：SHS ncy 0.510 vs OPPO 0.501
7. 中宫：三种方法结论矛盾
8. 特征覆盖：仅 3755 字验证

## 六、参考数据
- SHS VF 2.005: CFF2, 65535 glyphs, cmap 44853, upm 1000
- OPPO Sans 4.0: 29385 glyphs, cmap 29197
- Mona Sans VF: 797 glyphs, 568 cmap, 3 axes
- 笔画宽（口横画）: 250:30 300:49 350:68 400:77 500:97 700:124 900:150
