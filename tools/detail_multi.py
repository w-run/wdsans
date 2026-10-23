"""多区域细节对比：一页多行，每行一个 em 区域，每列一款字体。

用法：
    python3 detail_multi.py 永 --rects "点:330,690,700,900;竖钩:380,-160,640,140" --fonts "a=标签=路径,..."
"""
import argparse
import os
import subprocess
import sys

FONT_DIR = "/var/minis/workspace/specimen/fonts"


def to_woff2(path, key, chars):
    os.makedirs(FONT_DIR, exist_ok=True)
    dst = os.path.join(FONT_DIR, f"dm_{key}.woff2")
    if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(path):
        return dst
    subprocess.run([sys.executable, "-m", "fontTools.subset", path,
                    f"--text={chars}", "--layout-features=*", "--flavor=woff2",
                    f"--output-file={dst}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return dst


def build(fonts, glyph, rects, outdir, cell=420):
    chars = "".join(sorted(set(glyph + "永国回色东南湖人大天我之乎者也一三五已中水日田")))
    for key, _, path in fonts:
        to_woff2(path, key, chars)

    faces = "\n".join(
        f"@font-face{{font-family:DM{key};src:url('fonts/dm_{key}.woff2') format('woff2')}}"
        for key, _, _ in fonts)

    rows = []
    for name, (x0, y0, x1, y1) in rects:
        cells = "".join(
            f'<div class="cell"><div class="lab">{label}</div>'
            f'<canvas width="{cell*2}" height="{cell*2}" '
            f'data-f="{key}" data-r="{x0},{y0},{x1},{y1}"></canvas></div>'
            for key, label, _ in fonts)
        rows.append(f'<div class="rname">{name}</div><div class="grid">{cells}</div>')

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#fff;width:{cell*len(fonts)}px}}
.rname{{font:12px/1 -apple-system;color:#666;letter-spacing:.1em;padding:10px 2px 4px}}
.grid{{display:grid;grid-template-columns:repeat({len(fonts)},1fr)}}
.cell{{position:relative;border:1px solid #eee}}
.cell canvas{{width:{cell}px;height:{cell}px;display:block}}
.lab{{position:absolute;left:5px;top:3px;font:10px/1 -apple-system;color:#bbb;z-index:2}}
</style></head><body>
{''.join(rows)}
<script>
const G={glyph!r};
for (const cv of document.querySelectorAll('canvas')) {{
  const ctx=cv.getContext('2d');
  const [x0,y0,x1,y1]=cv.dataset.r.split(',').map(Number);
  const W=x1-x0, H=y1-y0, S=cv.width;
  const scale=S/W;
  ctx.fillStyle='#fff'; ctx.fillRect(0,0,S,S);
  ctx.fillStyle='#111';
  ctx.font=`${{scale*1000}}px "DM${{cv.dataset.f}}"`;
  ctx.textBaseline='alphabetic'; ctx.textAlign='left';
  ctx.save(); ctx.beginPath(); ctx.rect(0,0,S,S); ctx.clip();
  const hh = S*H/W;
  ctx.translate(0, 0);
  ctx.fillText(G, -x0*scale, hh + y0*scale);
  ctx.restore();
}}
</script></body></html>"""
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"dm_{glyph}.html")
    with open(out, "w") as f:
        f.write(html)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glyph")
    ap.add_argument("--rects", required=True, help="名称:x0,y0,x1,y1;名称:...")
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--outdir", default="/var/minis/workspace/specimen/hd")
    ap.add_argument("--cell", type=int, default=420)
    a = ap.parse_args()
    rects = []
    for item in a.rects.split(";"):
        name, box = item.split(":")
        rects.append((name, [float(v) for v in box.split(",")]))
    fonts = [tuple(x.split("=", 2)) for x in a.fonts.split(",")]
    print(build(fonts, a.glyph, rects, a.outdir, a.cell))


if __name__ == "__main__":
    main()
