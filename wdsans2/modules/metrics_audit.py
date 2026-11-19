#!/usr/bin/env python3
"""metrics_audit - 行高度量对比（从未验证过的维度）

影响: 行高决定每段文字的垂直间距，是所有 UI 排版的基础。
      若 ascender/descender 与参考不一致，行距会整体偏大或偏小。

检查: hhea.ascent/descent/lineGap, OS/2 sTypoAscender/Descender/LineGap,
      usWinAscent/Descent, unitsPerEm
"""
from fontTools.ttLib import TTFont

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS":  "/workspace/wdsans/ref/hos/hos-400.ttf",
}

FIELDS = [
    ("hhea.ascent",      lambda f: f["hhea"].ascent),
    ("hhea.descent",     lambda f: f["hhea"].descent),
    ("hhea.lineGap",     lambda f: f["hhea"].lineGap),
    ("OS2.sTypoAscender",  lambda f: f["OS/2"].sTypoAscender),
    ("OS2.sTypoDescender", lambda f: f["OS/2"].sTypoDescender),
    ("OS2.sTypoLineGap",   lambda f: f["OS/2"].sTypoLineGap),
    ("OS2.usWinAscent",    lambda f: f["OS/2"].usWinAscent),
    ("OS2.usWinDescent",   lambda f: f["OS/2"].usWinDescent),
    ("OS2.fsSelection",  lambda f: "0x%04X" % f["OS/2"].fsSelection),
    ("upm",              lambda f: f["head"].unitsPerEm),
]

data = {}
for name, path in FONTS.items():
    f = TTFont(path, lazy=True)
    d = {}
    for label, fn in FIELDS:
        try:
            d[label] = fn(f)
        except Exception as e:
            d[label] = "ERR"
    data[name] = d
    f.close()

hdr = "%-22s" % "字段"
for n in FONTS:
    hdr += " %10s" % n
print(hdr)
print("-" * len(hdr))
for label, _ in FIELDS:
    row = "%-22s" % label
    for n in FONTS:
        v = data[n][label]
        row += " %10s" % (("%d" % v) if isinstance(v, int) else v)
    # 标记与 SHS 的差异
    a = data["我们"][label]; b = data["SHS"][label]
    if isinstance(a, int) and isinstance(b, int) and a != b:
        row += "   <- 与 SHS 差 %+d" % (a - b)
    print(row)

print()
print("=== 单倍行高（ascent - descent + lineGap）===")
for n in FONTS:
    h = data[n]["hhea.ascent"] - data[n]["hhea.descent"] + data[n]["hhea.lineGap"]
    o = data[n]["OS2.sTypoAscender"] - data[n]["OS2.sTypoDescender"] + data[n]["OS2.sTypoLineGap"]
    u = data[n]["OS2.usWinAscent"] + data[n]["OS2.usWinDescent"]
    print("  %-6s hhea=%-5d OS2.typo=%-5d usWin=%-5d" % (n, h, o, u))