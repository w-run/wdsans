#!/usr/bin/env python3
"""P0 · 元数据归一：修 name 表 + 注入 STAT。

只碰 name / STAT / fsSelection，不动 glyf 与度量数值。
输出到 build/meta/，可重复执行（幂等）。

用法:
    python3 tools/fix_meta.py                     # 默认源 wdsans202506
    python3 tools/fix_meta.py --src DIR --out DIR
    python3 tools/fix_meta.py --use-typo-metrics   # 额外置 fsSelection bit7
"""
import argparse
import json
import os
import sys

from fontTools.ttLib import TTFont, newTable
from fontTools.otlLib.builder import buildStatTable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SRC = '/var/minis/shared/wdsans202506'
DEFAULT_OUT = os.path.join(ROOT, 'build', 'meta')


def load_axis():
    with open(os.path.join(ROOT, 'contract', 'axis.json')) as f:
        return json.load(f)


def set_name(font, nid, value):
    """更新所有平台下已存在的该 nameID；没有则补 win/mac 两条。"""
    name = font['name']
    plat = {(r.platformID, r.platEncID, r.langID) for r in name.names if r.nameID == nid}
    if not plat:
        name.setName(value, nid, 3, 1, 0x409)
        name.setName(value, nid, 1, 0, 0)
        return
    for pid, eid, lid in plat:
        name.setName(value, nid, pid, eid, lid)


def ensure_name(font, nid, value):
    name = font['name']
    if not any(r.nameID == nid for r in name.names):
        name.setName(value, nid, 3, 1, 0x409)
        name.setName(value, nid, 1, 0, 0)


def fix_one(src_path, out_path, axis, version, use_typo_metrics, fix_line_height):
    font = TTFont(src_path, recalcTimestamp=False)

    family = axis['family']
    ps_family = axis['psFamily']
    vendor = axis['vendor']
    stop = None
    for s in axis['stops']:
        if src_path.endswith(f"-{s['ps']}.ttf") or src_path.endswith(f"-{s['ps']}.otf"):
            stop = s
            break
    if stop is None:
        raise SystemExit(f'cannot map weight from filename: {src_path}')

    style = stop['name']
    is_ribbi = style in ('Regular', 'Bold')

    # legacy RIBBI 模型（Google Fonts 惯例）：
    #   非 Regular/Bold -> name1 = "家族 样式", name2 = "Regular"
    #   Regular / Bold  -> name1 = "家族",      name2 = "Regular"/"Bold"
    legacy_family = family if is_ribbi else f'{family} {style}'
    subfamily = style if is_ribbi else 'Regular'
    full_name = family if style == 'Regular' else f'{family} {style}'
    ps_name = f"{ps_family}-{stop['ps']}"

    set_name(font, 1, legacy_family)
    set_name(font, 2, subfamily)
    set_name(font, 3, f'{version};{vendor};{ps_name}')
    set_name(font, 4, full_name)
    # 关键：抹掉 FontCreator 指纹（POSTMORTEM 2.3）
    set_name(font, 5, f'Version {version}')
    set_name(font, 6, ps_name)
    # typographic family / subfamily（现代应用优先读这两个）
    ensure_name(font, 16, family)
    set_name(font, 16, family)
    ensure_name(font, 17, style)
    set_name(font, 17, style)

    # fsSelection
    os2 = font['OS/2']
    os2.version = 4  # bit7/8/9 需要 v4+
    fs = os2.fsSelection
    fs &= ~0x01  # clear ITALIC
    fs |= 0x100  # WWS
    if style == 'Regular':
        fs |= 0x40
        fs &= ~0x20
    elif style == 'Bold':
        fs |= 0x20
        fs &= ~0x40
    else:
        fs &= ~(0x40 | 0x20)
    if use_typo_metrics:
        fs |= 0x80
    else:
        fs &= ~0x80
    os2.fsSelection = fs
    os2.usWeightClass = stop['value']
    os2.usWidthClass = 5

    # 行高修复（思源黑已知问题）：
    #   hhea 1160/-288 → 行高 1.448em，macOS/CoreText 与 FreeType 都按 hhea 算
    #   修法：hhea 与 typo 对齐到 880/-120（=1.0em），并置 USE_TYPO_METRICS
    #   usWin* 保留 1160/288，避免 Windows 老引擎裁切超出基框的字形
    if fix_line_height:
        hhea = font['hhea']
        hhea.ascent = 880
        hhea.descent = -120
        hhea.lineGap = 0
        os2.sTypoAscender = 880
        os2.sTypoDescender = -120
        os2.sTypoLineGap = 0
        os2.fsSelection = os2.fsSelection | 0x80
        if 'vhea' in font:
            v = font['vhea']
            v.ascent = 500
            v.descent = -500
            v.lineGap = 0

    head = font['head']
    head.macStyle = 1 if style == 'Bold' else 0

    # STAT：完整轴 + 全部命名实例（Windows 依据它判断同族 7 档）
    values = []
    for s in axis['stops']:
        v = {
            'nominalValue': s['value'],
            'name': s['name'],
            'flags': 0x0002 if s['name'] == 'Regular' else 0,
        }
        values.append(v)
    buildStatTable(
        font,
        [{'tag': 'wght', 'name': 'Weight', 'ordering': 0, 'values': values}],
        elidedFallbackName=2,
        windowsNames=True,
        macNames=False,
    )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    font.save(out_path)
    return ps_name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=DEFAULT_SRC)
    ap.add_argument('--out', default=DEFAULT_OUT)
    ap.add_argument('--version', default=None)
    ap.add_argument('--use-typo-metrics', action='store_true')
    ap.add_argument('--no-fix-line-height', action='store_true')
    args = ap.parse_args()

    axis = load_axis()
    version = args.version or axis['version']

    for s in axis['stops']:
        src = None
        for ext in ('.ttf', '.otf'):
            cand = os.path.join(args.src, f"WDesignSans-{s['ps']}{ext}")
            if os.path.exists(cand):
                src = cand
                break
        if src is None:
            print(f"MISSING WDesignSans-{s['ps']}.ttf/.otf in {args.src}", file=sys.stderr)
            continue
        out = os.path.join(args.out, f"WDesignSans-{s['ps']}" + os.path.splitext(src)[1])
        ps = fix_one(src, out, axis, version, args.use_typo_metrics,
                     not args.no_fix_line_height)
        print(f'ok  {ps:24s} wght={s["value"]:3d}  -> {out}')

    print(f'\nversion={version}  typo_metrics={args.use_typo_metrics}  '
          f'fix_line_height={not args.no_fix_line_height}')


if __name__ == '__main__':
    main()
