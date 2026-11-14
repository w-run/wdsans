# P129 · 交付物清单（dist-v8 + subset-v8）

日期：2026-11-07
状态：完整交付，OTS 27/27 通过

## 产物结构

```
/data/build-cache/wdsans-dist-v8/        15 个字体 + README + OFL
  7 x WDesignSansSC-{Thin..Heavy}.ttf     ~21.6 MB
  7 x WDesignSansSC-{Thin..Heavy}.woff2   ~7.7 MB
  WDesignSansSC-VF.woff2                  19.9 MB

/data/build-cache/wdsans-subset-v8/      12 个
  {Regular,Medium,Bold}-sub{3755,6763} x {ttf,woff2}
```

## 验证结果

| 检查项 | 结果 |
|---|---|
| OTS 全量（dist + subset） | **27/27 通过** |
| 6 个 OpenType 特性 | 6/6 生效（gid 变化验证） |
| tnum 等宽 | 各档 advance 极差 = 0 |
| tnum 字重一致性 | Thin/Regular/Bold/Heavy 比值全部 1.00 |
| 子集保留 tnum | sub3755 / sub6763 均含 tnum |
| 原生 TrueType | glyf + gvar，无 CFF |

## OpenType 特性状态

### 已实现且验证生效（6 个）

tnum / frac / numr / dnom / sups / subs

判据：hb-shape 前后 gid 必须变化（不能只看 advance）。

### 未实现（6 个）：ss01 / ss02 / ss03 / ss04 / ss05 / case

feature 已注册、mapping 正确、已挂到 7 个 script，但 HarfBuzz 不应用。
排查记录见 P125，已排除 7 个假设：

1. Coverage 域缺失 —— 官方 builder 同样返回 None，而 tnum 正常
2. FeatureIndex 未排序 —— 实测升序无重复
3. 源字形解析错误 —— 改为 a->b 仍无效
4. 手写 otTables 有误 —— 改用官方 otlLib builder 仍无效
5. LangSys 未引用 —— 确认已引用仍无效
6. 新槽位字形有问题 —— 用原字形同样无效
7. 默认特性抢占源字形 —— 关闭 calt/liga/rlig/clig/aalt 后仍无效

**结论：不能再靠猜。下一步应在二进制层面逐字节 diff 与 Mona 的差异。**

## 字形形态：已做的量化排查

以下维度全部测量过，均未发现我方劣于 OPPO/HOS：

| 维度 | 结果 |
|---|---|
| 笔画宽度变异系数 CV | ours 0.128 < OPPO 0.180 < HOS 0.185 |
| 路径端比 p90/p10 | ours 1.038，OPPO 1.015，HOS 1.088 |
| 墨量重心 | ours cx=0.483 / OPPO 0.486 / HOS 0.488（差异 <0.005）|
| 轮廓尖角角度 | ours 不比 HOS 更尖锐 |
| 「一」端面角度 | 三款均 90 度 |

**局部差异**：「永」顶部点在 ours 上 x 起点比 HOS 早 50upm、位置偏低 18upm。
这是 Noto 原始设计，是否构成缺陷需视觉判定。

## 教训

1. **hb-view 不能读 woff2**（返回全 0 墨量）。所有渲染验证必须用 TTF。
2. **验证 OpenType 特性必须用 gid 变化**，不能用 advance —— 文本含数字时会误判。
3. **不要用 getattr 探测编译期派生字段**（如 Coverage），Python 层拿不到不等于文件里没有。
4. **移植字形优先「复用自己的 + 最小变换」**，而非搬运外部字形（见 P127）。