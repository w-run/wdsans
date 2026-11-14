# P131 · ss/case 特性：10 轮失败的真因是「手工组装 otTables」

日期：2026-11-07
状态：已解决。11/11 特性全部生效。

## 最终结论（一句话）

**必须用 `fontTools.feaLib.builder.addOpenTypeFeaturesFromString` 声明特性，
手工组装 `otTables.Lookup` + `SingleSubst` 虽然能序列化通过 OTS，
但 HarfBuzz 不认。**

## 证据

```
手工组装（v9/v10）:  a + ss05 -> gid66   （不变）
feaLib（v11）      :  g + ss06 -> gid61908（生效）
```

## 最终验证（11/11 全部生效）

```
特性   样例   默认 -> 特性后
ss01   !      gid2   -> gid61992
ss02   I      gid42  -> gid62011
ss03   l      gid77  -> gid62028
ss04   l      gid77  -> gid62035
ss05   a      gid66  -> gid62041
ss06   g      gid72  -> gid62069
ss07   G      gid40  -> gid62075
ss08   0      gid17  -> gid62081
ss09   Q      gid50  -> gid62083
ss10   J      gid43  -> gid62088
case   (      gid9   -> gid62098
```

## 我为这个错误付出的代价

10 轮、8 个被证伪的假设：

1. Coverage 域缺失 —— 官方 buildSingleSubstSubtable 同样返回 None，而 tnum 正常
2. FeatureIndex 未排序 —— 实测升序无重复
3. 源字形解析错误 —— 改为 a->b 仍无效
4. 手写 otTables 有误 —— **这个假设是对的，但我当时换成了
   buildSingleSubstSubtable 仍属手工组装，没有换到 feaLib，所以被我误判为否定**
5. LangSys 未引用 —— 确认已引用仍无效
6. 槽位字形有问题 —— 用原字形同样无效
7. 默认特性抢占源字形 —— 关闭 calt/liga/rlig/clig 后仍无效
8. 样本选择错误 —— 换 ss06 仍无效（因为仍是手工组装）

## 为什么会误判第 4 条

我当时把「换 API」理解成了「换到官方实现」，
但实际上 `buildSingleSubstSubtable` 只是**子表构建器**，
不负责 ScriptList/FeatureList/LookupList 的登记。
真正的高层入口是 `feaLib.builder.addOpenTypeFeaturesFromString`。

**教训：遇到「官方 API 也不 work」时，要确认那个 API 是否覆盖了完整链路，
而不是同名就说「我试过官方实现了」。**

## 附带发现

- Mona 的 `ss05`（a -> a.ss05）在 Mona 自身默认就已激活（被 rlig/clig 替换），
  所以拿它做「特性是否生效」的参照是无效的。应以 ss06（g -> g.ss06）为参照。
- `hb-view` 不能读 woff2，返回全 0 墨量。渲染验证必须用 TTF。
- 验证特性必须用 **gid 变化**，不能用 advance（文本含数字时会误判）。