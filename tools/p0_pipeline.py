"""WDesign Sans · P0 管线验证

目标：证明「节点位移」路线可行 —— 变形后的字体仍然能重建出可变字体，
且 fvar / GSUB / locl / GPOS 全部保留。

流程：
    VF ──instancer──▶ 静态 master(s)
       ──transform──▶ 变形后的 master(s)
       ──varLib.build──▶ 新 VF
"""
import os
import sys
import shutil
import subprocess

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.varLib.models import VariationModel


# ---------------------------------------------------------------- 轮廓读写

def glyph_paths(font, glyph_names):
    """读出每个字形的绝对坐标路径（moveTo/lineTo/qCurveTo/curveTo/closePath）。"""
    gs = font.getGlyphSet()
    out = {}
    for gn in glyph_names:
        pen = RecordingPen()
        gs[gn].draw(pen)
        out[gn] = pen.value
    return out


def write_paths(font, paths):
    """把绝对坐标路径写回 CFF / CFF2 的 charstring（确定性编码）。"""
    from canonical_cff import replay_to_canonical

    is_cff2 = "CFF2" in font
    tag = "CFF2" if is_cff2 else ("CFF " if "CFF " in font else "CFF")
    table = font[tag].cff.topDictIndex[0]
    cs = table.CharStrings
    for gn, value in paths.items():
        old = cs[gn]
        new = replay_to_canonical(value).getCharString(
            private=old.private, globalSubrs=old.globalSubrs
        )
        cs[gn] = new
    return font


def _replay(value, pen):
    for op, args in value:
        getattr(pen, op)(*args)


# ---------------------------------------------------------------- master

def make_master(vf_path, wght, out_path):
    font = TTFont(vf_path)
    inst = instantiateVariableFont(font, {"wght": wght}, inplace=False, optimize=False)
    for tag in ("fvar", "avar", "STAT", "HVAR", "VVAR"):
        if tag in inst:
            del inst[tag]
    inst.save(out_path)
    inst.close()
    return out_path


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/p0/sub.otf"
    outdir = "/tmp/p0/out"
    os.makedirs(outdir, exist_ok=True)

    from transforms import apply_all

    # 每个字重一组参数：先只做温和的「中宫松散 + 重心微调」
    WEIGHT_PARAMS = {
        250: {"spread": {"factor": 1.035}, "gravity": {"strength": 0.02}},
        900: {"spread": {"factor": 1.020}, "gravity": {"strength": 0.02}},
    }

    print("[1/4] 从 VF 实例化两个 master …")
    el = make_master(src, 250, f"{outdir}/master-EL.otf")
    hv = make_master(src, 900, f"{outdir}/master-HV.otf")

    print("[2/4] 读取轮廓 …")
    names = TTFont(src).getGlyphOrder()
    print(f"     {len(names)} 个字形")

    print("[3/4] 应用形变并回写 …")
    for path, wght in ((el, 250), (hv, 900)):
        f = TTFont(path)
        paths = glyph_paths(f, names)
        params = WEIGHT_PARAMS[wght]
        paths = {gn: apply_all(v, params) for gn, v in paths.items()}
        write_paths(f, paths)
        f.save(path)
        f.close()
    print("     ok")

    print("[4/4] 重建 VF …")
    _build_vf(el, hv, f"{outdir}/result.otf")
    print("     ok")


def _build_vf(el_path, hv_path, out_path):
    """用 fontTools varLib 从两个 CFF master 重建 CFF2 可变字体。"""
    from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor, InstanceDescriptor

    ds = DesignSpaceDocument()
    ax = AxisDescriptor()
    ax.tag = "wght"; ax.name = "weight"; ax.minimum = 250; ax.maximum = 900; ax.default = 250
    ax.map = [(250, 0), (300, 160), (350, 320), (400, 390), (500, 560), (700, 780), (900, 1000)]
    ds.addAxis(ax)

    for path, loc in ((el_path, 0), (hv_path, 1000)):
        s = SourceDescriptor()
        s.path = path
        s.location = {"weight": loc}
        s.familyName = "WDesignSans"
        ds.addSource(s)

    ds_path = out_path.replace(".otf", ".designspace")
    ds.write(ds_path)

    from fontTools import varLib
    vf, _, _ = varLib.build(ds_path)
    vf.save(out_path)


if __name__ == "__main__":
    main()
