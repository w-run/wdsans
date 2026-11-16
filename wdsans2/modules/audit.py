#!/usr/bin/env python3
"""audit.py - 全模块效果审计（总入口）

背景: 连续两轮出现「重建链漏模块」（m_curvflat / m_latinreset），
两者都是纯几何模块，构建不报错、门禁不报警，只能靠测量发现。

**每次重建链 / 每次部署前必须跑一遍。**

用法: python modules/audit.py
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

SCRIPTS = [
    ('表与特性', 'audit_all.py'),
    ('几何与排版', 'audit_geom.py'),
]

fails = []
for label, script in SCRIPTS:
    print('=' * 64)
    print('### %s (%s)' % (label, script))
    print('=' * 64)
    r = subprocess.run([PY, '-u', os.path.join(HERE, script)],
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    print(out)
    import re
    m = re.search(r'FAIL (\d+)', out)
    nfail = int(m.group(1)) if m else 0
    if r.returncode != 0 or nfail > 0:
        fails.append('%s(%d FAIL)' % (label, nfail))

print('=' * 64)
if fails:
    print('审计失败: %s' % fails)
    sys.exit(1)
print('全部审计通过')