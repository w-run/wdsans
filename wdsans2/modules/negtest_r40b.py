#!/usr/bin/env python3
"""negtest_r40b - 正确制造逆序"""
import subprocess, shutil, os
from fontTools.ttLib import TTFont

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
BAK = "/tmp/vf_r40b_good.otf"
BAD = "/tmp/vf_r40b_bad.otf"

shutil.copy(VF, BAK)
print("=== 负向测试: 用不同 tag 制造逆序 ===")
f = TTFont(VF)
gs = f['GSUB'].table
fr = gs.FeatureList.FeatureRecord
tags = [x.FeatureTag for x in fr]
print('  当前有序:', tags == sorted(tags))

# 找第一条和最后一条（tag 必然不同）交换
i0 = 0
i1 = len(fr) - 1
print("  交换 [%d]=%s <-> [%d]=%s" % (i0, tags[i0], i1, tags[i1]))
fr[i0], fr[i1] = fr[i1], fr[i0]
new_tags = [x.FeatureTag for x in fr]
print('  改后有序:', new_tags == sorted(new_tags))
f.save(BAD)
f.close()

shutil.copy(BAD, VF)
r = subprocess.run(['/workspace/wdsans/venv/bin/python','-u','claim_audit.py'],
    cwd='/workspace/wdsans2/modules', capture_output=True, text=True)
print("  exit =", r.returncode, "(应 1)")
for ln in (r.stdout or '').split(chr(10)):
    if 'FAIL' in ln or '交付物核对' in ln or '有序' in ln:
        print('   ', ln.strip())

shutil.copy(BAK, VF)
print()
print("=== 恢复后 ===")
r2 = subprocess.run(['/workspace/wdsans/venv/bin/python','-u','claim_audit.py'],
    cwd='/workspace/wdsans2/modules', capture_output=True, text=True)
print("  exit =", r2.returncode, "(应 0)")
for ln in (r2.stdout or '').split(chr(10))[-5:]:
    if ln.strip(): print('   ', ln.strip())

os.remove(BAD)