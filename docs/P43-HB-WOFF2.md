# P43：HarfBuzz 8.4.0 不解 WOFF2 —— 推翻一个长期假设

## 发现过程

本轮做 SVG 锚点视觉检查时，顺便想看一眼子集渲染效果，结果：

```
TTF  渲染 → 1447 字节 PNG ✓
WOFF2 渲染 → 121 字节 PNG ✗（空白）
```

进一步验证：

```
$ hb-shape --font-file=WDesignSansSC-Regular.woff2 "永和"
[gid0=0+500|gid0=1+500]      ← 全是 notdef！
```

## 根因

```
$ ldd $(which hb-shape) | grep brotli
libbrotlidec.so.1 => /lib64/libbrotlidec.so.1
libbrotlicommon.so.1 => /lib64/libbrotlicommon.so.1
```

**brotli 库已链接，但 HarfBuzz 8.4.0 不解析 woff2 容器格式。**
它只把文件当字体表读取，遇到 wOF2 魔数直接失败 → 所有字符回落 gid0。

对照：**fontTools 能正常解**
```python
TTFont("...woff2").getBestCmap()  →  44,905 条  ✓
```

## 影响范围（重要）

此前所有用 hb-shape / hb-view 测 WOFF2 的结论，**实际上测的是 gid0**。

需要重新核对的文档：

| 文档 | 涉及内容 | 影响 |
|---|---|---|
| P28 子集化 | hb-shape 验证 woff2 特性 | 需重测 |
| P32 交付同步 | woff2 大小/哈希 | 无影响（非渲染测试）|
| P41 交付闭环 | woff2 大小/哈希 | 无影响（非渲染测试）|
| P42 子集化落地 | hb-shape 验证子集 woff2 | **需重测** |

**但注意**：凡是用 hb-shape 测 **TTF** 的结论全部有效，
因为项目绝大多数验证跑在 TTF 上。

## 正确做法

测 woff2 必须先解包成 TTF：

```python
f = TTFont("font.woff2")
f.flavor = None        # 去掉 woff2 包装
f.save("font_unpacked.ttf")
```

然后用 hb-shape / hb-view 测解包后的 TTF。

## 教训

**「工具返回了结果」不等于「结果有效」。**

hb-shape 对 woff2 没有报错、没有警告，只是安静地返回 `gid0`。
如果我不去截图看渲染结果，这个错误会一直藏着。

这是第 19 次「必须先验证工具本身」。具体到这次：
- 前面几轮我以为「woff2 体积对、哈希对」就说明 woff2 没问题——这部分是对的
- 但「用 hb-shape 测 woff2 的功能」是错的，因为工具不支持

**做法：渲染类测试一律用 TTF；woff2 只做解包完整性 + 体积/哈希校验。**