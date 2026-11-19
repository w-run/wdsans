#!/usr/bin/env python3
"""apply_fbclean2_to_fa - 对 FlatApex 应用同样的修复"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/modules')
import m_fbclean2 as M
from fontTools.ttLib import TTFont

FA = "/workspace/static/wdsans/WDesignSans-FlatApex-Regular.otf"
TMP = "/workspace/wdsans2/build/FA_R38.otf"

f = TTFont(FA)
print("FlatApex 修复:")
print('  [1] fvar/STAT')
try:
    M.fix_stat(f, False)
except Exception as e:
    print("  STAT 跳过: %s" % e)
print('  [2] Mac name')
M.fix_mac(f, False)
print('  [3] zh-CN name')
M.fix_zhname(f, False)
f["post"].formatType = 3.0
f["post"].glyphOrder = None
f.save(TMP)
f.close()

g = TTFont(TMP, lazy=True)
st = g['STAT'].table if 'STAT' in g else None
n = len(st.AxisValueArray.AxisValue) if st and st.AxisValueArray else 0
plats = sorted(set(r.platformID for r in g['name'].names))
zh = sum(1 for r in g['name'].names if r.langID == 0x804)
print("  验证: STAT=%d platforms=%s zh-CN=%d size=%.1fMB" % (n, plats, zh, os.path.getsize(TMP)/1e6))
g.close()