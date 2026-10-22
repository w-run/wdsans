"""样张生成器：用浏览器渲染，不做自制光栅化。

铁律：视觉验证必须走真实排版引擎（WebKit），因为我们要判断的是「排印效果」，
不是「轮廓拓扑是否合法」。自制光栅器只看得到几何，看不到 hinting、抗锯齿、
字距、行距、混排关系 —— 那些恰恰是排版里最重要的部分。

用法：
    python3 specimen_html.py out.html --fonts shs=/path/a.otf oppo=/path/b.ttf --text "永国回"
    python3 specimen_html.py out.html --preset refs      # 思源黑/鸿蒙/OPPO 三家对照
"""
import argparse
import os
import subprocess
import sys

FONT_DIR = "/var/minis/workspace/specimen/fonts"

PRESETS = {
    "refs": {
        "SHS": ("思源黑（基座）", "/var/minis/shared/fonts/src/../src/shs-sc-regular.otf"),
        "HMOS": ("鸿蒙 Sans SC", "/tmp/p0/hmos.ttf"),
        "OPPO": ("OPPO Sans", "/tmp/p0/oppo.ttf"),
    },
}


def subset_woff2(src, dst, text):
    """只保留需要的字形，转 woff2。CJK 全量字体太重，浏览器加载会卡。"""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(src):
        return dst
    cmd = [sys.executable, "-m", "fontTools.subset", src,
           f"--text={text}", "--layout-features=*", "--flavor=woff2",
           f"--output-file={dst}"]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return dst


def build_html(fonts, text, title="字体对照"):
    """fonts: list of (key, label, path)"""
    faces, cards, paras = [], [], []
    for key, label, path in fonts:
        faces.append(f"@font-face{{font-family:{key};src:url('fonts/{key}.woff2') format('woff2')}}")
        cards.append(f'<div class="tag">{label}</div>')

    cells = "".join(
        "<div class='card'>" + "".join(
            f'<div class="tag">{label}</div><div class="g" style="font-family:{key}">{ch}</div>'
            for key, label, _ in fonts) + "</div>"
        for ch in text
    )

    para = ("字体设计最难的部分不是把字形画好看，而是让四万个字形在同一套规则下"
            "保持一致的灰度与节奏。当笔画被程序自动加粗、中宫被整体放大之后，"
            "问题往往不会在大字号样张里暴露，而是藏在十二像素的正文里："
            "笔画粘连、部件错位、破洞被填实、竖钩收笔断裂。")
    blocks = "".join(
        f'<div style="font-family:{k};font-size:13px;line-height:1.95;text-align:justify;'
        f'margin-top:14px;border-top:1px dashed #eee;padding-top:8px">'
        f'<b style="font:9px/1 -apple-system;color:#bbb;letter-spacing:.1em">{l}</b><br>{para}</div>'
        for k, l, _ in fonts)

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{title}</title><style>
{chr(10).join(faces)}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#fff;padding:22px 26px;color:#111}}
h2{{font:400 11px/1 -apple-system,sans-serif;color:#999;letter-spacing:.12em;
   margin:18px 0 10px;border-top:1px solid #eee;padding-top:8px}}
h2:first-child{{border:0;margin-top:0}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}}
.card{{border:1px solid #eee;padding:6px 0 8px;text-align:center}}
.card .tag{{font:9px/1 -apple-system,sans-serif;color:#bbb;letter-spacing:.05em}}
.g{{font-size:104px;line-height:1.1;margin:2px 0}}
</style></head><body>
<h2>单字 · 104px ｜每列自上而下：{ " / ".join(l for _, l, _ in fonts) }</h2>
<div class="grid">{cells}</div>
<h2>密排正文 · 13px（真实使用场景）</h2>
{blocks}
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--preset", default=None)
    ap.add_argument("--fonts", nargs="*", default=[])
    ap.add_argument("--text", default="永国回色東南明湖")
    args = ap.parse_args()

    if args.preset:
        fonts = [(k, l, p) for k, (l, p) in PRESETS[args.preset].items()]
    else:
        fonts = []
        for item in args.fonts:
            k, p = item.split("=", 1)
            fonts.append((k, k, p))

    for key, label, path in fonts:
        subset_woff2(path, os.path.join(FONT_DIR, f"{key}.woff2"), args.text)

    html = build_html(fonts, args.text)
    with open(args.out, "w") as f:
        f.write(html)
    print("saved", args.out)


if __name__ == "__main__":
    main()
