#!/usr/bin/env python3
"""patch_audit_ledge - 把 ledge 审计项标记为已废弃（SKIP）"""
import re

P = '/workspace/wdsans2/modules/audit_geom.py'
s = open(P, encoding="utf-8").read()

# 1) 文件头注释
s = s.replace('  m_ledge     顶部横笔右余 = TARGET_MARGIN',
              '  m_ledge     已废弃（误伤 1,456 字），见 AGENTS.md')

# 2) 整段 ledge 检测 -> 直接 SKIP
start = s.find('# m_ledge: 顶部横笔右余应为 ~90（400档）')
end = s.find('# m_latinext: Latin Ext-A 覆盖')
if start > 0 and end > start:
    brief = """# m_ledge: 已废弃

m_ledge / m_ledge2 / m_ledge3 三轮尝试均因误伤过多而放弃：
  v1 (MOD29) 1,182 字
  v2 (MOD30) 2,636 字，改坏曲线
  v3 (L3)    1,511 字，实测仍误伤 1,456 字（462 字位移>100）

根因: 「整字顶横」与「左侧偏旁横笔」在轮廓层面无法可靠区分。
左右结构字的偏旁横笔，右侧阻挡判据在 y 区间不重叠时失效
（散/形/几 的右边部件在横笔 y 带之外）。

典型误伤: 珔518 玸508 玦498 砍479 殃460 孜449 功431
         以及 极条角得散形几界混 等常用字。

现链已彻底移除 m_ledge（R29）。本项保留为 SKIP 以示已知。
rec("ledge", "SKIP", "已废弃（误伤 1,456 字，见 AGENTS.md）")

"""
    s = s[:start] + brief + s[end:]
    print("ledge 段已替换")

open(P, 'w', encoding='utf-8').write(s)
print('done')