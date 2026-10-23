"""高清字形渲染：走浏览器 Canvas（真实文字引擎 + Cairo/Skia 光栅化）。

不用自己写的 Python 光栅器 —— 自制的永远只验证几何，看不到抗锯齿、hinting、
栅格化误差，而细节恰恰藏在那些地方。

用法：
    python3 render_glyph.py 永 --fonts shs=...,oppo=... --outdir /var/minis/workspace/specimen/hd

产出：<outdir>/<glyph>.html（2×2 网格，每格 600 CSS px）
然后交给 browser_use 截图。
"""
import argparse
import os
import subprocess
import sys

FONT_DIR = "/var/minis/workspace/specimen/fonts"


def to_woff2(path, key, chars):
    os.makedirs(FONT_DIR, exist_ok=True)
    dst = os.path.join(FONT_DIR, f"hd_{key}.woff2")
    if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(path):
        return dst
    subprocess.run([sys.executable, "-m", "fontTools.subset", path,
                    f"--text={chars}", "--layout-features=*", "--flavor=woff2",
                    f"--output-file={dst}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return dst


def build(fonts, glyph, outdir):
    chars = "".join(sorted(set(glyph)))
    for key, label, path in fonts:
        to_woff2(path, key, chars + "永国回色东南湖人大天我之乎者也一三五已中水")

    cells = "".join(
        f'<div class="cell"><div class="lab">{label}</div>'
        f'<canvas width="1200" height="1200" data-f="{key}"></canvas></div>'
        for key, label, _ in fonts)

    faces = "\n".join(
        f"@font-face{{font-family:HD{key};src:url('fonts/hd_{key}.woff2') format('woff2')}}"
        for key, _, _ in fonts)

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#fff;width:1240px}}
.grid{{display:grid;grid-template-columns:1fr 1fr}}
.cell{{position:relative;border:1px solid #eee}}
.cell canvas{{width:600px;height:600px;display:block}}
.lab{{position:absolute;left:8px;top:6px;font:13px/1 -apple-system;color:#999;z-index:2}}
</style></head><body>
<div class="grid">{cells}</div>
<script>
const G={glyph!r};
const EM=900, BASE=780;      // 画布 1200 中：em 高 900，基线在 y=780
for (const cv of document.querySelectorAll('canvas')) {{
  const ctx=cv.getContext('2d');
  const key=cv.dataset.f;
  ctx.fillStyle='#fff'; ctx.fillRect(0,0,1200,1200);
  ctx.fillStyle='#111';
  ctx.font=`${{EM}}px "HD${{key}}"`;
  ctx.textBaseline='alphabetic';
  ctx.textAlign='center';
  ctx.fillText(G, 600, BASE);
}}
</script></body></html>"""
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"{glyph}.html")
    with open(out, "w") as f:
        f.write(html)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glyph")
    ap.add_argument("--fonts", required=True, help="key=label=path,key=label=path")
    ap.add_argument("--outdir", default="/var/minis/workspace/specimen/hd")
    a = ap.parse_args()
    fonts = []
    for item in a.fonts.split(","):
        parts = item.split("=", 2)
        if len(parts) != 3:
            raise SystemExit(f"bad font spec: {item} (want key=label=path)")
        fonts.append(tuple(parts))
    print(build(fonts, a.glyph, a.outdir))


if __name__ == "__main__":
    main()
