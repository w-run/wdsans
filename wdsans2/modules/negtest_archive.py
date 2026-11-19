#!/usr/bin/env python3
"""negtest_archive - 存档表检查的负向测试"""
import subprocess, shutil, os
P = "/workspace/wdsans/docs/DELIVERY.md"
BAK = "/tmp/del_good.md"
shutil.copy(P, BAK)

s = open(P, encoding="utf-8").read()
good = "| v261120 | R35（+ m_middotadv）| 111 MB | static/wdsans/archive/v261120/ |"
bad = "| v261120 | R35（+ m_middotadv）| 111 MB | static/wdsans/archive/v261121/ |"
if good in s:
    open(P, 'w', encoding='utf-8').write(s.replace(good, bad))
    print("已注入错误行")
else:
    print("未找到目标行")

print()
print("=== 负向测试（应 exit=1）===")
r = subprocess.run([
    "/workspace/wdsans/venv/bin/python", "-u", "claim_audit.py"],
    cwd="/workspace/wdsans2/modules", capture_output=True, text=True)
print("exit =", r.returncode)
for ln in (r.stdout or '').split(chr(10)):
    if 'FAIL' in ln or '存档表' in ln or '交付物核对' in ln:
        print(' ', ln.strip())

shutil.copy(BAK, P)
print()
print("=== 恢复后（应 exit=0）===")
r2 = subprocess.run([
    "/workspace/wdsans/venv/bin/python", "-u", "claim_audit.py"],
    cwd="/workspace/wdsans2/modules", capture_output=True, text=True)
print("exit =", r2.returncode)
for ln in (r2.stdout or '').split(chr(10))[-4:]:
    if ln.strip(): print(' ', ln.strip())