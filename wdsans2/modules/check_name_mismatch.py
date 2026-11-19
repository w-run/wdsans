#!/usr/bin/env python3
"""检查 master 与 VF 的 glyph 名不一致，导致多少字被漏改"""
import sys, json
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont

MASTER="/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"
VF="/workspace/static/wdsans/WDesignSans-VF.otf"

mf=TTFont(MASTER,lazy=True); mcm=mf.getBestCmap()
vf=TTFont(VF,lazy=True); vcm=vf.getBestCmap()

# 上次的索引是按 master glyph 名建的
IDX=json.load(open("/workspace/wdsans2/build/vertend_idx.json"))
print("索引大小: %d (按 master glyph 名)" % len(IDX))

# 建 master glyph名 -> codepoint 的反向表
m_rev={}
for cp,gn in mcm.items():
    m_rev.setdefault(gn,[]).append(cp)

# VF 的 glyph 名集合
vf_names=set(vcm.values())

miss_same_cp=[]   # 名字在 VF 里存在但对应不同 cp
miss_absent=[]    # 名字在 VF 里根本不存在
ok=0
for gn in IDX:
    if gn in vf_names:
        # 该名字在 VF 里对应的 codepoint
        v_cps=[cp for cp,g in vcm.items() if g==gn]
        m_cps=m_rev.get(gn,[])
        if set(v_cps)==set(m_cps):
            ok+=1
        else:
            miss_same_cp.append((gn, m_cps[:3], v_cps[:3]))
    else:
        miss_absent.append((gn, m_rev.get(gn,[])[:3]))

print()
print("名字匹配且 cp 一致: %d" % ok)
print("名字存在但 cp 不同: %d" % len(miss_same_cp))
print("名字在 VF 中不存在: %d" % len(miss_absent))
print()
if miss_same_cp[:10]:
    print("=== 名字存在但 cp 不同（前10）===")
    for gn,m,v in miss_same_cp[:10]:
        print("  %-14s master_cp=%s  vf_cp=%s" % (gn,
            [hex(x) for x in m],[hex(x) for x in v]))
print()
if miss_absent[:10]:
    print("=== 名字不存在（前10）===")
    for gn,m in miss_absent[:10]:
        print("  %-14s master_cp=%s" % (gn,[hex(x) for x in m]))

# 关键: 换算成"漏改的 codepoint 数"
# 对每个漏改的 master glyph，按 cp 找到 VF 里的 glyph
missed_cps=[]
for gn,_ in [(x[0],0) for x in miss_same_cp] + [(x[0],0) for x in miss_absent]:
    for cp in m_rev.get(gn,[]):
        if cp in vcm:
            missed_cps.append(cp)
print()
print("按 codepoint 可修复的漏改字: %d" % len(set(missed_cps)))
mf.close(); vf.close()
