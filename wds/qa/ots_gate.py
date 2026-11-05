"""OTS 浏览器兼容性闸门（P48）。

OTS 是 Chrome/Firefox 加载字体的强制关卡，不通过则浏览器静默拒绝。
本模块供构建流水线调用：任何产物不通过则整体失败。
"""
from __future__ import annotations
import glob, os, subprocess, sys


def _ots_binary():
    """定位 ots-sanitize（不在 PATH，在 python 包内）。"""
    import ots
    d = os.path.dirname(ots.__file__)
    p = os.path.join(d, "ots-sanitize")
    return p if os.path.exists(p) else None


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