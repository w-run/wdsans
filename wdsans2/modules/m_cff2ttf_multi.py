#!/usr/bin/env python3
"""m_cff2ttf_multi - 三档联动 CFF2 -> TTF（保证插值兼容）

关键: 用 cu2qu.curves_to_quadratic(curves, max_errors)
      一次处理三档的同一条曲线，返回点数一致的二次曲线。

对比单档转换的问题:
  逐档独立调 Cu2QuPen -> 每档的点数取决于该档曲线形状
  -> 三档点数不同 -> varLib 报 incompatible masters -> 该字形无 gvar
"""
import sys, os, time
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._g_l_y_f import Glyph, table__g_l_y_f
from fontTools.ttLib.tables._l_o_c_a import table__l_o_c_a
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.pointPen import PointToSegmentPen
import numpy as np
from cu2qu import curves_to_quadratic, curve_to_quadratic

BASE="/workspace/wdsans2/build"
SRC_DIR=os.path.join(BASE,os.environ.get("WDS_SRC_DIR","masters_R42"))
OUT_DIR=os.path.join(BASE,os.environ.get("WDS_OUT_DIR","ttf_masters_multi"))
MASTERS=[("master-ExtraLight-250.otf",250),
         ("master-Regular-400.otf",400),
         ("master-Heavy-900.otf",900)]
MAX_ERR=1.0


def get_contours(font, gname):
    """取字形的轮廓（分解后的线段/曲线序列）"""
    gs=font.getGlyphSet()
    rp=RecordingPen()
    try:
        gs[gname].draw(rp)
    except Exception:
        return None
    contours=[]; cur=None
    for op,args in rp.value:
        if op=="moveTo":
            cur={"start":tuple(args[0]),"ops":[]}
            contours.append(cur)
        elif op=="lineTo" and cur is not None:
            cur["ops"].append(("L",tuple(args[0])))
        elif op=="curveTo" and cur is not None:
            cur["ops"].append(("C",tuple(args[0]),tuple(args[1]),tuple(args[2])))
        elif op=="qCurveTo" and cur is not None:
            cur["ops"].append(("Q",tuple(args[0]),tuple(args[1])))
        elif op=="closePath":
            cur=None
        elif op=="endPath":
            cur=None
    return contours


def contours_to_quadratic(all_contours):
    """对三档的同名字形做联动转换
    all_contours: [contours_w250, contours_w400, contours_w900]
    返回: [quad_contours_w250, ...] 三档点数一致
    """
    n_masters=len(all_contours)
    res=[[] for _ in range(n_masters)]
    # 轮廓数必须一致
    counts=set(len(c) for c in all_contours)
    if len(counts)!=1:
        return None
    for ci in range(len(all_contours[0])):
        ops_counts=set(len(all_contours[m][ci]["ops"]) for m in range(n_masters))
        if len(ops_counts)!=1:
            return None
        out=[{"start":None,"ops":[]} for _ in range(n_masters)]
        cur_pt=[all_contours[m][ci]["start"] for m in range(n_masters)]
        for m in range(n_masters):
            out[m]["start"]=all_contours[m][ci]["start"]
        for oi in range(len(all_contours[0][ci]["ops"])):
            kinds=set(all_contours[m][ci]["ops"][oi][0] for m in range(n_masters))
            if len(kinds)!=1:
                return None
            kind=all_contours[0][ci]["ops"][oi][0]
            if kind=="L":
                for m in range(n_masters):
                    out[m]["ops"].append(("L",all_contours[m][ci]["ops"][oi][1]))
                    cur_pt[m]=all_contours[m][ci]["ops"][oi][1]
            elif kind=="C":
                # curves_to_quadratic 需要 (start, c1, c2, end) 四点
                curves=[[cur_pt[m],
                         all_contours[m][ci]["ops"][oi][1],
                         all_contours[m][ci]["ops"][oi][2],
                         all_contours[m][ci]["ops"][oi][3]] for m in range(n_masters)]
                try:
                    quads=curves_to_quadratic(curves,[MAX_ERR]*n_masters)
                except Exception:
                    return None
                for m in range(n_masters):
                    out[m]["ops"].append(("Q",quads[m],all_contours[m][ci]["ops"][oi][3]))
                    cur_pt[m]=all_contours[m][ci]["ops"][oi][3]
            elif kind=="Q":
                for m in range(n_masters):
                    out[m]["ops"].append(("Q",all_contours[m][ci]["ops"][oi][1],all_contours[m][ci]["ops"][oi][2]))
                    cur_pt[m]=all_contours[m][ci]["ops"][oi][2]
        for m in range(n_masters):
            res[m].append(out[m])
    return res


def build_glyph(quad_contours):
    """quad_contours -> Glyph（直接构造数组，不做任何点合并）

    🔴 为什么不用 TTGlyphPen:
       qCurveTo 内部会对「与上一控制点重合」的点做合并，
       导致同一条逻辑曲线在不同字重下产生不同点数 ->
       varLib 报 incompatible masters -> 该字形无 gvar 插值 -> 字重失效。
       实测受影响字形: a b j o p u 0 5 6 9（10 个）
       直接构造 coordinates/flags/endPts 可保证三档严格一致。
    """
    from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
    from fontTools.ttLib.tables.ttProgram import Program
    ON=1; OFF=0
    coords=[]; flags=[]; endPts=[]
    for c in quad_contours:
        st=c["start"]
        coords.append((int(round(st[0])), int(round(st[1]))))
        flags.append(ON)
        for op in c["ops"]:
            if op[0]=="L":
                p=op[1]
                coords.append((int(round(p[0])), int(round(p[1]))))
                flags.append(ON)
            elif op[0]=="Q":
                sp=op[1]              # [start, ctrl1, ..., end]
                for p in sp[1:-1]:    # 控制点
                    coords.append((int(round(p[0])), int(round(p[1]))))
                    flags.append(OFF)
                e=sp[-1]              # 终点
                coords.append((int(round(e[0])), int(round(e[1]))))
                flags.append(ON)
        endPts.append(len(coords)-1)
    g=Glyph()
    g.numberOfContours=len(quad_contours)
    g.coordinates=GlyphCoordinates(coords)
    g.flags=bytearray(flags)
    g.endPtsOfContours=endPts
    g.program=Program()
    return g


def convert_all():
    fonts=[]
    for fn,w in MASTERS:
        p=os.path.join(SRC_DIR,fn)
        f=TTFont(p, lazy=True)
        fonts.append(f)
        print("  载入 %d: %s" % (w,os.path.basename(fn)))
    order=fonts[0].getGlyphOrder()
    print("  共 %d 字形" % len(order))

    os.makedirs(OUT_DIR, exist_ok=True)
    glyphs_per=[{} for _ in fonts]
    n_conv=0; n_skip=0
    t0=time.time()

    for gi,gname in enumerate(order):
        allc=[get_contours(f,gname) for f in fonts]
        if any(c is None for c in allc) or any(len(c)==0 for c in allc):
            n_skip+=1
            for m in range(len(fonts)):
                glyphs_per[m][gname]=Glyph()
            continue
        # 三档轮廓结构必须一致
        sig=set()
        for c in allc:
            sig.add(tuple(len(x["ops"]) for x in c))
        if len(sig)!=1:
            n_skip+=1
            for m in range(len(fonts)):
                glyphs_per[m][gname]=Glyph()
            continue
        q=contours_to_quadratic(allc)
        if q is None:
            n_skip+=1
            for m in range(len(fonts)):
                glyphs_per[m][gname]=Glyph()
            continue
        for m in range(len(fonts)):
            try:
                glyphs_per[m][gname]=build_glyph(q[m])
            except Exception:
                glyphs_per[m][gname]=Glyph()
        n_conv+=1
        if (gi+1)%5000==0:
            print("    %d/%d  转换 %d 跳过 %d  %.0fs" % (
                gi+1,len(order),n_conv,n_skip,time.time()-t0), flush=True)

    print("  转换 %d, 跳过 %d, %.0fs" % (n_conv,n_skip,time.time()-t0))

    # 写三档 TTF
    for m,(fn,w) in enumerate(MASTERS):
        f=fonts[m]
        glyf=newTable("glyf"); glyf.glyphs=glyphs_per[m]; glyf.glyphOrder=order
        f["glyf"]=glyf
        maxp=f["maxp"]; maxp.tableVersion=0x00010000
        maxp.maxZones=1; maxp.maxTwilightPoints=0; maxp.maxStorage=0
        maxp.maxFunctionDefs=0; maxp.maxInstructionDefs=0
        maxp.maxStackElements=0; maxp.maxSizeOfInstructions=0
        maxp.maxComponentElements=max((len(getattr(g,"components",[])) for g in glyphs_per[m].values()),default=0)
        for tag in ("CFF2","CFF","VORG"):
            if tag in f: del f[tag]
        f["loca"]=table__l_o_c_a()
        f["head"].glyphDataFormat=0; f["head"].indexToLocFormat=1
        f["post"].formatType=3.0; f["post"].glyphOrder=None
        f.sfntVersion="\x00\x01\x00\x00"

        # 🔴 关键: TrueType 要求 hmtx.lsb == glyf.xMin。
        #    CFF 里 lsb 不参与渲染定位，所以原始 lsb 往往 != xmin（本字体 87% 如此）。
        #    若不动 lsb，fontTools 保存时会自动平移坐标去凑 lsb
        #    -> 每个字位移量不同（lsb - xmin）-> 整体字距错乱、数字 1 偏右。
        #    ✅ 正确做法: 坐标保持不动，把 lsb 改成实际的 xMin。
        hm=f["hmtx"]
        fixed=0
        for gn2 in order:
            g2=glyphs_per[m].get(gn2)
            if g2 is None: continue
            if g2.numberOfContours == 0:
                continue
            g2.recalcBounds(glyf)
            xmin=g2.xMin
            adv,lsb=hm[gn2]
            if lsb != xmin:
                hm[gn2]=(adv,xmin)
                fixed+=1
        print("    lsb 校正 %d 个字形" % fixed)

        out=os.path.join(OUT_DIR,"master-%d.ttf"%w)
        f.save(out); f.close()
        print("  [%d] -> %s (%.1fMB)" % (w,out,os.path.getsize(out)/1e6))


if __name__=="__main__":
    convert_all()
