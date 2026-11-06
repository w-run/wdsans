# -*- coding: utf-8 -*-
"""交付物验收工具（P91）：三层检查，内置 woff2 解包。

## 为什么需要

P90 做最终验收时，脚本直接 hb-view 喂了 VF.woff2，得到 205 字节空白图，
差点误判为「VF 损坏」。根因是 P43 早已记录的限制：

  HarfBuzz 8.4.0 不解 WOFF2，静默返回空白。

**文档记录了 ≠ 流程遵守了。** 所以本工具把解包做进流程，不依赖人记得。

## 三层检查

  1. 传输层：与 w-box 源逐文件 sha256 比对
  2. 格式层：OTS 全部通过
  3. 渲染层：woff2 先解包成 TTF 再渲染，统计墨迹量确认非空白
"""
from __future__ import annotations
import glob
import hashlib
import os
import subprocess
import tempfile


def _sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _unpack_woff2(path, outdir):
    """WOFF2 → TTF。返回 TTF 路径（已是 TTF 则原样返回）。"""
    if not path.endswith(".woff2"):
        return path
    from fontTools.ttLib import TTFont
    dst = os.path.join(outdir, os.path.basename(path)[:-6] + ".ttf")
    f = TTFont(path)
    f.flavor = None
    f.save(dst)
    f.close()
    return dst


def render_ink(path, text="\u4e2d\u6587 WDesign 2026", size=40):
    """渲染并返回墨迹像素数。内部自动解包 woff2。"""
    import numpy as np
    from PIL import Image
    tmp = tempfile.mkdtemp()
    try:
        ttf = _unpack_woff2(path, tmp)
        png = os.path.join(tmp, "r.png")
        subprocess.run(["hb-view", "--font-file=" + ttf,
                        "--font-size=%d" % size, "--output-file=" + png,
                        "--background=FFFFFF", "--margin=4", text],
                       check=True, capture_output=True)
        a = 255 - np.array(Image.open(png).convert("L"), dtype=np.float64)
        return int((a > 40).sum())
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def check_transport(local_dir, remote_manifest):
    """比对本地文件与远端 sha256 清单。返回 (一致数, 问题列表)。"""
    ok = 0
    problems = []
    for rel, want in remote_manifest.items():
        p = os.path.join(local_dir, rel)
        if not os.path.exists(p):
            problems.append("缺失: " + rel)
            continue
        if _sha256(p) == want:
            ok += 1
        else:
            problems.append("哈希不符: " + rel)
    return ok, problems


def check_render(font_paths, min_ink=200):
    """逐个渲染，墨迹量低于阈值判为异常。返回 (通过数, 问题列表)。"""
    ok = 0
    problems = []
    for p in font_paths:
        try:
            ink = render_ink(p)
            if ink >= min_ink:
                ok += 1
            else:
                problems.append("%s 墨迹仅 %d px（疑似空白/字形缺失）" % (
                    os.path.basename(p), ink))
        except Exception as e:
            problems.append("%s 渲染失败: %s" % (os.path.basename(p), str(e)[:60]))
    return ok, problems