#!/usr/bin/env python3
"""m_fbclean2 - fontbakery 第二轮修复（R38）

来源: fontbakery 1.1.0 check-universal --succinct

修 1  FAIL inconsistencies_between_fvar_STAT
  fvar 9 个 instance（250/300/350/400/500/600/700/800/900）
  STAT 只有 1 个 AxisValue，且 Format=2 无 Value 字段
  -> 9 个 instance 全无对应条目，应用读不到字重名称
  修: 为每个 instance 建 Format 1 的 AxisValue，按 value 排序

修 2  FAIL no_mac_entries
  name 表有 20 条 platformID=1（Mac）记录
  这 20 条是我们自己的 bvf 脚本加的（[(3,1,0x409),(1,0,0)]）
  SHS 原版只有 platformID=3
  修: 删除所有 platformID=1 的记录

修 3  🔴 回归: zh-CN name 记录全部丢失
  R37 部署版只有 (1,0x000)+(3,0x409)，zh-CN 0 条
  SHS 原版有 3 条 zh-CN
  AGENTS.md 已记录「VF 构建会丢弃 zh-CN，必须 post_vf_name2 修复」
  但 bvf_r37.py 的自写 name 替换没加 0x804 -> 回归
  修: 从 master 复制 zh-CN 的 nameID 1/2/4/16/17
      🔴 nameID17 在 master 里是 ExtraLight，必须强制改 Regular
"""
import os, sys
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables._n_a_m_e import NameRecord

VF = "/workspace/wdsans2/build/VF_R37.otf"
OUT = "/workspace/wdsans2/build/VF_R38.otf"
MASTER = "/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"


def fix_stat(f, dry):
    fv = f["fvar"]
    st = f["STAT"].table
    axis_tag = fv.axes[0].axisTag
    existing = {}
    if st.AxisValueArray and st.AxisValueArray.AxisValue:
        for av in st.AxisValueArray.AxisValue:
            v = getattr(av, 'Value', None)
            if v is not None:
                existing[round(float(v), 1)] = av
    new_vals = []
    for inst in fv.instances:
        w = inst.coordinates.get(axis_tag)
        if w is None:
            continue
        w = round(float(w), 1)
        if w in existing:
            continue
        av = otTables.AxisValue()
        av.Format = 1
        av.AxisIndex = 0
        av.Flags = 2
        av.Value = float(w)
        av.ValueNameID = inst.subfamilyNameID
        new_vals.append(av)
        existing[w] = av
    if not st.AxisValueArray:
        st.AxisValueArray = otTables.AxisValueArray()
        st.AxisValueArray.AxisValue = []
    all_av = list(st.AxisValueArray.AxisValue) + new_vals
    def key(av):
        ai = getattr(av, 'AxisIndex', 0)
        v = getattr(av, 'Value', None)
        return (ai, float(v) if v is not None else -99999)
    all_av.sort(key=key)
    st.AxisValueArray.AxisValue = all_av
    print('  STAT AxisValue: %d -> %d (+%d)' % (len(all_av)-len(new_vals), len(all_av), len(new_vals)))


def fix_mac(f, dry):
    nm = f['name']
    before = len(nm.names)
    mac = [r for r in nm.names if r.platformID == 1]
    if not dry:
        nm.names = [r for r in nm.names if r.platformID != 1]
    print('  name: %d 条，删 %d 条 Mac -> %d 条' % (before, len(mac), before-len(mac)))


def fix_zhname(f, dry):
    """补回 zh-CN 记录，nameID17 强制 Regular"""
    vnm = f['name']
    mf = TTFont(MASTER, lazy=True)
    mnm = mf['name']
    added = 0
    for nid in (1, 2, 4, 16, 17):
        src = None
        for r in mnm.names:
            if r.nameID == nid and r.langID == 0x804 and r.platformID == 3:
                src = r
                break
        if src is None:
            continue
        # 已有就跳过
        exists = any(r.nameID == nid and r.langID == 0x804 and r.platformID == 3 for r in vnm.names)
        if exists:
            continue
        txt = str(src)
        if nid == 17:
            txt = 'Regular'   # 🔴 master 里是 ExtraLight
        nr = NameRecord()
        nr.nameID = nid
        nr.platformID = 3
        nr.platEncID = 1
        nr.langID = 0x804
        nr.string = txt.encode('utf-16-be')
        if not dry:
            vnm.names.append(nr)
        added += 1
    mf.close()
    zh = sum(1 for r in vnm.names if r.langID == 0x804)
    print('  zh-CN 记录: 补 %d 条 -> 共 %d 条' % (added, zh + (0 if not dry else added)))


def main(dry=False):
    print('m_fbclean2: %s -> %s dry=%s' % (VF, OUT, dry))
    f = TTFont(VF)
    print('  [1] fvar/STAT 一致性')
    fix_stat(f, dry)
    print('  [2] Mac name 记录')
    fix_mac(f, dry)
    print('  [3] zh-CN name 记录（回归修复）')
    fix_zhname(f, dry)
    if dry:
        f.close(); return
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    f.save(OUT)
    f.close()
    print('  保存 %s (%.1fMB)' % (OUT, os.path.getsize(OUT)/1e6))

    # 验证
    g = TTFont(OUT, lazy=True)
    st = g['STAT'].table
    n_av = len(st.AxisValueArray.AxisValue) if st.AxisValueArray else 0
    plats = sorted(set(r.platformID for r in g['name'].names))
    zh = sum(1 for r in g['name'].names if r.langID == 0x804)
    n17 = [str(r) for r in g['name'].names if r.nameID == 17 and r.langID == 0x804]
    print('  验证: STAT=%d  platforms=%s  zh-CN=%d  nameID17(zh)=%s' % (n_av, plats, zh, n17))
    g.close()


if __name__ == "__main__":
    main("--dry" in sys.argv)