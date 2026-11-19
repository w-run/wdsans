#!/usr/bin/env python3
"""negtest_r38 - 三项新检查的负向测试"""
import subprocess, shutil, os
from fontTools.ttLib import TTFont

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
BAK = "/tmp/vf_good_R38.otf"
BAD = "/tmp/vf_bad_R38.otf"

shutil.copy(VF, BAK)
print("=== 负向测试 1: 恢复 Mac name 记录 ===")
f = TTFont(VF)
from fontTools.ttLib.tables._n_a_m_e import NameRecord
nr = NameRecord()
nr.nameID = 1; nr.platformID = 1; nr.platEncID = 0; nr.langID = 0
nr.string = b'WDesign Sans'
f['name'].names.append(nr)
f.save(BAD)
f.close()

def run(font):
    env = dict(os.environ)
    r = subprocess.run(
        ["/workspace/wdsans/venv/bin/python", "-u", "claim_audit.py"],
        cwd="/workspace/wdsans2/modules", capture_output=True, text=True, env=env)
    return r.returncode, r.stdout or ''

# 临时替换部署文件做测试
shutil.copy(BAD, VF)
code, out = run(VF)
print("  exit =", code, "(应 1)")
for ln in out.split(chr(10)):
    if 'FAIL' in ln or '交付物核对' in ln:
        print('   ', ln.strip())

shutil.copy(BAK, VF)
print()
print("=== 恢复后 ===")
code2, out2 = run(VF)
print("  exit =", code2, "(应 0)")
for ln in out2.split(chr(10))[-6:]:
    if ln.strip(): print('   ', ln.strip())

os.remove(BAD)