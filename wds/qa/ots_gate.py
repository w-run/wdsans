"""OTS 浏览器兼容性闸门（P48 建立，P71 修复导入脆弱性）。

OTS 是 Chrome/Firefox 加载字体的强制关卡，不通过则浏览器静默拒绝。
本模块供构建流水线调用：任何产物不通过则整体失败。

## P71 修复：`import ots` 的 CWD 脆弱性

原实现直接 `import ots`，靠 sys.path 解析。
若当前工作目录存在同名文件（如一个测试脚本 ots.py），
Python 会优先导入那个文件，导致找不到 ots-sanitize 而崩溃。

改为用 importlib.util 按包名精确查找，再用 PathFinder 定位目录，
不依赖 CWD，也不依赖 sys.path 顺序。
"""
from __future__ import annotations
import glob
import os
import subprocess
import sys


def _ots_binary():
    """定位 ots-sanitize（在 python 包的安装目录内）。

    用 importlib 精确查找，避免与 CWD 中的同名模块冲突。
    """
    import importlib.util
    try:
        spec = importlib.util.find_spec("ots")
    except (ImportError, ValueError):
        spec = None
    if spec is not None and spec.origin:
        d = os.path.dirname(spec.origin)
        p = os.path.join(d, "ots-sanitize")
        if os.path.exists(p):
            return p
    # 兜底：在 sys.path 各目录下找 ots 包
    for base in sys.path:
        if not base:
            continue
        p = os.path.join(base, "ots", "ots-sanitize")
        if os.path.exists(p):
            return p
    return None


def check(paths=None, dist_dirs=None, verbose=False):
    """返回不通过的产物数量（0 = 全部通过）。"""
    ots = _ots_binary()
    if not ots:
        raise RuntimeError("找不到 ots-sanitize")
    if paths is None:
        paths = []
        for d in (dist_dirs or []):
            paths += sorted(glob.glob(os.path.join(d, "*.ttf")))
            paths += sorted(glob.glob(os.path.join(d, "*.woff2")))
    bad = 0
    out = "/tmp/_ots_gate.tmp"
    for p in paths:
        r = subprocess.run([ots, p, out], capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            bad += 1
            print("  OTS FAIL: %s" % os.path.basename(p), flush=True)
            msg = (r.stderr or r.stdout or "").strip()
            if msg:
                print("    " + msg[-200:], flush=True)
        elif verbose:
            print("  OTS OK: %s" % os.path.basename(p), flush=True)
        if os.path.exists(out):
            os.remove(out)
    return bad


if __name__ == "__main__":
    dirs = sys.argv[1:] or ["/data/build-cache/wdsans-dist",
                            "/data/build-cache/wdsans-subset"]
    n = check(dist_dirs=dirs, verbose=True)
    print("OTS: %s" % ("全部通过" if n == 0 else "%d 个失败" % n))
    sys.exit(0 if n == 0 else 1)