#!/usr/bin/env python3
"""ledge_off - 从链中彻底移除 m_ledge，重建干净链

### 决定（2026-11-17）
m_ledge 三轮尝试全部失败：
  v1 (MOD29): 1,182 字
  v2 (MOD30): 2,636 字，但改坏曲线
  v3 (L3)   : 1,511 字，仍有 1,456 字被误伤（462 字位移>100）

根因: 「顶部横笔」与「左侧偏旁横笔」在轮廓层面无法可靠区分。
      左右结构字的偏旁横笔，右侧阻挡判据在 y 区间不重叠时失效
      （散/形/几 的右边部件在横笔 y 带之外）。

用户反馈的具体损伤: 极/条/目/角/眼/得/散/形/几/界/混
  混 的「日」变成上下两半分离
  极/条/几 的横折右上有出头

### 本脚本
从 R15（末代无 m_ledge 的基座）重新串接后续模块，跳过 m_ledge。
新链: R15 -> punctscale -> featlang -> latinreset -> digitnine -> chufoot
"""
import os, subprocess, sys

PY = '/workspace/wdsans/venv/bin/python'
MOD = '/workspace/wdsans2/modules'
B = '/workspace/wdsans2/build'

STEPS = [
  ('m_punctscale', B + '/masters_R15',  B + '/S1_punct'),
  ('m_featlang',   B + '/S1_punct',     B + '/S2_feat'),
  ('m_latinreset', B + '/S2_feat',      B + '/S3_latin'),
  ('m_digitnine',  B + '/S3_latin',     B + '/S4_digit'),
  ('m_chufoot',    B + '/S4_digit',     B + '/masters_R29'),
]

for mod, src, out in STEPS:
    print('=== %s ===' % mod, flush=True)
    env = dict(os.environ, WDS_SRC=src, WDS_OUT=out)
    r = subprocess.run([PY, "-u", MOD + "/" + mod + ".py"],
                       cwd=MOD, env=env, capture_output=True, text=True)
    tail = [l for l in (r.stdout + r.stderr).strip().split("\n") if l.strip()]
    for l in tail[-4:]:
        print('  ' + l, flush=True)
    if r.returncode != 0:
        print('  FAILED', flush=True); sys.exit(1)
print('all done')