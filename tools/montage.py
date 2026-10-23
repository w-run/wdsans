"""拼图：每格单独出图（glyph_view），再拼成一张。

为什么这样：每张格子图都是**独立生成**的，可以单独打开核对；
拼图只负责排布，不参与坐标计算。所以不存在"缩放对不对"的问题 ——
格子多大由 --size 决定，画布尺寸就是格子尺寸的整数倍。

区块截取走 glyph_view 的 --crop（按 em 格位，不是按像素放大）。

用法：
    # 四家 口 字左下角，2×2 拼图
    python3 montage.py --glyphs 口 --crop a7-c8 --size 420 --cols 2 \
      --fonts "SHS=ref/shs/shs-400.otf,HOS=ref/hos/hos-400.ttf,
               OPPO=ref/ops/ops-400.ttf,WDO=ref/wdo/wdo-400.ttf" \
      --out /tmp/foot.png

    # 保留每格的原图，便于逐个核对
    python3 montage.py ... --out /tmp/foot.png --keep /tmp/cells
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DEJAVU = "/usr/share/fonts/dejavu/DejaVuSans.ttf"
DEJAVU_B = "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"


CJK = os.path.join(os.path.dirname(HERE), "ref", "shs", "shs-400.otf")


def font(size, bold=False, cjk=False):
    """标签字体。PIL 内置 DejaVu 没有汉字，中文标签要借思源。"""
    if cjk and os.path.exists(CJK):
        try:
            return ImageFont.truetype(CJK, size)
        except Exception:
            pass
    for p in ((DEJAVU_B if bold else DEJAVU), DEJAVU):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_cell(font_path, glyph, crop, size, grid, out, box=None):
    """调 glyph_view 出一张格子图 —— 单个文件，可单独打开验证。"""
    cmd = [sys.executable, os.path.join(HERE, "glyph_view.py"),
           "--font", font_path, "--glyph", glyph, "--out", out,
           "--size", str(size)]
    if box:
        cmd += ["--box", box]
    elif crop:
        cmd += ["--crop", crop]
    if grid:
        cmd.append("--grid")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return None, (r.stderr or r.stdout).strip().splitlines()[-1:]
    return out, None


PALETTE = [(255, 60, 60), (60, 110, 220), (20, 150, 80), (150, 80, 200),
           (230, 140, 0), (0, 170, 190)]


def render_overlay(fonts, glyph, a):
    """叠图：每家用 glyph_view 单独出图，取墨迹做蒙版，按色叠加。

    每张原图仍是独立生成的，可单独核对；叠加只做合成，不做坐标换算。
    """
    tmp = tempfile.mkdtemp(prefix="overlay.")
    keep = a.keep
    if keep:
        os.makedirs(keep, exist_ok=True)
    imgs = []
    for lab, path in fonts:
        out = os.path.join(keep if keep else tmp, f"{lab}_{glyph}.png")
        p, err = render_cell(path, glyph, a.crop, a.size, False, out, a.box)
        if err:
            print(f"[跳过] {lab}: {err}", file=sys.stderr)
            continue
        imgs.append((lab, Image.open(p).convert("L")))
    if not imgs:
        raise SystemExit("没有可用的图")

    w, h = imgs[0][1].size
    rows_lg = (len(imgs) + 1) // 2 if len(imgs) > 3 else 1
    bar = a.bar or max(46, 26 * rows_lg)
    canvas = Image.new("RGB", (w, bar + h), "#ffffff")
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, w, bar - 1], fill="#f2f4f7")
    for i, (lab, im) in enumerate(imgs):
        if im.size != (w, h):
            im = im.resize((w, h), Image.LANCZOS)
        col = PALETTE[i % len(PALETTE)]
        # 墨迹蒙版 → 轮廓线 + 淡填充。轮廓线才看得出边缘差在哪
        ink = im.point(lambda v: 255 - v)
        edge = ImageChops.subtract(ink, ink.filter(ImageFilter.MinFilter(3)))
        canvas.paste(Image.new("RGB", (w, h), col), (0, bar),
                     ink.point(lambda v: int(v * 0.22)))
        canvas.paste(Image.new("RGB", (w, h), col), (0, bar), edge)

    # 图例：自动分两列，避免超出画布
    fl = font(max(15, min(26, bar // rows_lg - 6)), bold=True)
    ncol_lg = 2 if len(imgs) > 3 else len(imgs)
    cw = w // ncol_lg
    row_h = (bar - 8) // max(1, (len(imgs) + ncol_lg - 1) // ncol_lg)
    for i, (lab, _) in enumerate(imgs):
        r, c = divmod(i, ncol_lg)
        col = PALETTE[i % len(PALETTE)]
        lx = c * cw + 10
        ly = 6 + r * row_h
        d.rectangle([lx, ly + 4, lx + 18, ly + 4 + row_h - 12], fill=col)
        d.text((lx + 26, ly + 4 + (row_h - 12) // 2), lab, fill="#333333",
               font=fl, anchor="lm")
    d.rectangle([0, 0, w - 1, bar + h - 1], outline="#9db3cc", width=2)
    canvas.save(a.out)
    print("saved", a.out, f"{w}×{bar + h}  {len(imgs)} 家叠加  区域 {a.box or a.crop or '整字'}")
    if keep:
        print("每格原图:", keep)
    else:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True, help="标签=路径,标签=路径（可换行）")
    ap.add_argument("--glyphs", required=True, help="字符，可多个")
    ap.add_argument("--out", required=True, help="拼好的 PNG")
    ap.add_argument("--crop", default=None, help="区块，如 a7-c8 或 d2")
    ap.add_argument("--box", default=None,
                    help="em 坐标裁剪 x0,y0,x1,y1，比 --crop 精确（不留空白）")
    ap.add_argument("--size", type=int, default=420, help="每格边长（像素）")
    ap.add_argument("--cols", type=int, default=0, help="每行几格，默认=字体数")
    ap.add_argument("--grid", action="store_true", help="格内叠 8×8 网格与编号")
    ap.add_argument("--gap", type=int, default=6, help="格间距（像素）")
    ap.add_argument("--keep", default=None, help="保留每格原图到此目录")
    ap.add_argument("--overlay", action="store_true",
                    help="叠图：同一字形所有字体叠在一格（按色区分）")
    ap.add_argument("--bar", type=int, default=0, help="每格标签条高度，默认自动")
    a = ap.parse_args()

    raw = a.fonts.replace("\n", "").replace(" ", "")
    fonts = []
    for seg in raw.split(","):
        if not seg:
            continue
        lab, p = seg.split("=", 1)
        if any(ord(c) > 126 for c in lab):
            print(f"警告：标签 {lab!r} 含非 ASCII，会显示空框；请用 SHS/HOS/OPPO/WDO",
                  file=sys.stderr)
        fonts.append((lab, p))
    glyphs = []
    for c in a.glyphs:
        if c not in glyphs:
            glyphs.append(c)
    total = len(fonts) * len(glyphs)
    ncol = a.cols if a.cols > 0 else len(fonts)
    ncol = max(1, min(ncol, total))
    nrow = (total + ncol - 1) // ncol

    if a.overlay:
        render_overlay(fonts, glyphs[0], a)
        return

    tmp = tempfile.mkdtemp(prefix="montage.")
    keep = a.keep
    if keep:
        os.makedirs(keep, exist_ok=True)

    bar = a.bar or max(36, a.size // 12)
    cells = []
    for idx in range(total):
        gid, fid = divmod(idx, len(fonts))
        lab, path = fonts[fid]
        ch = glyphs[gid]
        name = f"{lab}_{ch}.png"
        out = os.path.join(keep if keep else tmp, name)
        p, err = render_cell(path, ch, a.crop, a.size, a.grid, out, a.box)
        if err:
            print(f"[跳过] {lab} {ch}: {err}", file=sys.stderr)
            cells.append((lab, ch, None))
        else:
            cells.append((lab, ch, out))

    # 拼图：画布 = 格子尺寸整数倍，不做任何缩放
    cw = ch_ = a.size
    W = ncol * cw + (ncol - 1) * a.gap
    H = nrow * (ch_ + bar) + (nrow - 1) * a.gap
    canvas = Image.new("RGB", (W, H), "#ffffff")
    d = ImageDraw.Draw(canvas)
    fl = font(max(16, bar - 12), bold=True)
    fg = font(max(28, bar - 6), cjk=True)

    for idx, (lab, ch, path) in enumerate(cells):
        r, c = divmod(idx, ncol)
        x = c * (cw + a.gap)
        y = r * (ch_ + bar + a.gap)
        # 标签条
        d.rectangle([x, y, x + cw - 1, y + bar - 1], fill="#f2f4f7")
        d.text((x + 6, y + bar // 2), lab, fill="#333333", font=fl, anchor="lm")
        d.text((x + cw - 6, y + bar // 2), ch, fill="#999999", font=fg, anchor="rm")
        if path:
            im = Image.open(path).convert("RGB")
            if im.size != (cw, ch_):          # 只等比放进格子，不拉伸
                im.thumbnail((cw, ch_), Image.LANCZOS)
            canvas.paste(im, (x, y + bar))
        else:
            d.text((x + cw // 2, y + bar + ch_ // 2), "缺字", fill="#cc0000",
                   font=fg, anchor="mm")
        # 格子外框：没有它，相邻格笔画会连成一片
        d.rectangle([x, y, x + cw - 1, y + bar + ch_ - 1], outline="#9db3cc", width=2)

    canvas.save(a.out)
    area = f"box {a.box}" if a.box else (a.crop or "整字")
    print("saved", a.out, f"{W}×{H}  {nrow}行×{ncol}列  每格 {cw}px  区域 {area}")
    if not keep:
        shutil.rmtree(tmp, ignore_errors=True)
    else:
        print("每格原图:", keep)


if __name__ == "__main__":
    main()
