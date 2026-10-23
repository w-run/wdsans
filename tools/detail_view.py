"""细节放大对比：按**绝对 em 坐标**取景，保证四款字体严格对齐。

和之前的 bbox 裁剪不同：所有格子用同一套 em→像素映射，
所以同一个 em 矩形在每格里是同一个物理位置，可以直接逐像素对比。

用法：
    python3 detail_view.py 永 --rect 0,-150,320,120 --fonts a=标签=路径,...
产出 HTML，交给浏览器截图。
"""
import argparse
import os
import subprocess
import sys

FONT_DIR = "/var/minis/workspace/specimen/fonts"


def to_woff2(path, key, chars):
    os.makedirs(FONT_DIR, exist_ok=True)
    dst = os.path.join(FONT_DIR, f"dv_{key}.woff2")
    if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(path):
        return dst
    subprocess.run([sys.executable, "-m", "fontTools.subset", path,
                    f"--text={chars}", "--layout-features=*", "--flavor=woff2",
                    f"--output-file={dst}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return dst


def build(fonts, glyph, rect, outdir, cell=560):
    chars = "".join(sorted(set(glyph + "永国回色东南湖人大天我之乎者也一三五已中水日田")))
    for key, _, path in fonts:
        to_woff2(path, key, chars)

    x0, y0, x1, y1 = rect
    faces = "\n".join(
        f"@font-face{{font-family:DV{key};src:url('fonts/dv_{key}.woff2') format('woff2')}}"
        for key, _, _ in fonts)
    cells = "".join(
        f'<div class="cell"><div class="lab">{label}</div>'
        f'<canvas width="{cell*2}" height="{cell*2}" data-f="{key}"></canvas></div>'
        for key, label, _ in fonts)

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#fff}}
.grid{{display:grid;grid-template-columns:repeat({len(fonts)},1fr);width:{cell*len(fonts)}px}}
.cell{{position:relative;border:1px solid #eee}}
.cell canvas{{width:{cell}px;height:{cell}px;display:block}}
.lab{{position:absolute;left:6px;top:4px;font:11px/1 -apple-system;color:#999;z-index:2}}
</style></head><body>
<div class="grid">{cells}</div>
<script>
const G={glyph!r};
const R=[{x0},{y0},{x1},{y1}];       // em 坐标矩形
const W=R[2]-R[0], H=R[3]-R[1];
for (const cv of document.querySelectorAll('canvas')) {{
  const ctx=cv.getContext('2d');
  const S=cv.width;
  const scale=S/W;                    // em 单位 -> 画布像素
  ctx.fillStyle='#fff'; ctx.fillRect(0,0,S,S);
  ctx.fillStyle='#111';
  // 字号 = 1 em 的像素数
  ctx.font=`${{scale*1000}}px "DV${{cv.dataset.f}}"`;
  ctx.textBaseline='alphabetic';
  ctx.textAlign='left';
  // 把 em 原点 (0,0) 放到画布对应位置：x=R[0]*scale, y = S + R[1]*scale
  ctx.save();
  ctx.beginPath(); ctx.rect(0,0,S,S); ctx.clip();
  ctx.fillText(G, -R[0]*scale, S + R[1]*scale);
  ctx.restore();
}}
</script></body></html>"""
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"dv_{glyph}_{x0}_{y0}.html")
    with open(out, "w") as f:
        f.write(html)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glyph")
    ap.add_argument("--rect", required=True, help="x0,y0,x1,y1（em 坐标）")
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--outdir", default="/var/minis/workspace/specimen/hd")
    ap.add_argument("--cell", type=int, default=560)
    a = ap.parse_args()
    rect = [float(v) for v in a.rect.split(",")]
    fonts = [tuple(item.split("=", 2)) for item in a.fonts.split(",")]
    print(build(fonts, a.glyph, rect, a.outdir, a.cell))


if __name__ == "__main__":
    main()
