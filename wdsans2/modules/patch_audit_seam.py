#!/usr/bin/env python3
# patch_audit_seam - add seam audit item to audit_geom.py
import re
P = '/workspace/wdsans2/modules/audit_geom.py'
s = open(P, encoding="utf-8").read()

if "seam" in s:
    print("already patched")
else:
    block = []
    block.append("")
    block.append("# seam: 闭合轮廓的首末点必须重合（防舍入残留）")
    block.append("#   判据: area/gap > 1000 表示该轮廓本应闭合")
    block.append("#   对照: 口/十/一 的比值 81~916，正确跳过")
    block.append("def _endp(s):")
    block.append("    return np.array(s[1][-1], float) if s[0] == 'QM' else np.array(s[-1], float)")
    block.append("")
    block.append("def _poly(c):")
    block.append("    P = [np.array(c['start'], float)]")
    block.append("    for s in c['segs']:")
    block.append("        if s[0] == 'QM':")
    block.append("            for q in s[1]: P.append(np.array(q, float))")
    block.append("        elif s[0] == 'C':")
    block.append("            P.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])")
    block.append("        elif s[0] == 'Q':")
    block.append("            P.extend([np.array(s[1],float), np.array(s[2],float)])")
    block.append("        else:")
    block.append("            P.append(np.array(s[1], float))")
    block.append("    return np.array(P)")
    block.append("")
    block.append("def _area(P):")
    block.append("    x = P[:,0]; y = P[:,1]")
    block.append("    return 0.5*abs(float(np.dot(x, np.roll(y,1)) - np.dot(y, np.roll(x,1))))")
    block.append("")
    block.append("_seam_n = 0")
    block.append("for _cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF][:4000]:")
    block.append("    _rp = RecordingPen()")
    block.append("    try:")
    block.append("        gs[cm[_cp]].draw(_rp)")
    block.append("    except Exception:")
    block.append("        continue")
    block.append("    _C = contours_from_pen(_rp.value)")
    block.append("    for _c in _C:")
    block.append("        if len(_c['segs']) < 3:")
    block.append("            continue")
    block.append("        _st = np.array(_c['start'], float)")
    block.append("        _gap = float(np.hypot(*(_endp(_c['segs'][-1]) - _st)))")
    block.append("        if 0.8 < _gap < 12 and _area(_poly(_c))/max(_gap,1e-6) > 1000:")
    block.append("            _seam_n += 1")
    block.append("rec('seam', 'PASS' if _seam_n == 0 else 'FAIL',")
    block.append("    '闭合轮廓首末点残留缝隙 %d 处 (sample 4000 字)' % _seam_n)")
    block.append("")
    ins = "\n".join(block)
    # 插在 latinext 之前
    anchor = "# m_latinext: Latin Ext-A 覆盖"
    if anchor in s:
        s = s.replace(anchor, ins + "\n" + anchor)
        open(P, "w", encoding="utf-8").write(s)
        print("patched")
    else:
        print("anchor not found")