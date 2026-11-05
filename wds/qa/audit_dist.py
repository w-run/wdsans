"""交付产物一致性核对（P35 教训的自动化）。

P35 的 VF WOFF2 漏更新，根因是「靠记忆确认哪些产物重建了」。
本工具改为机器核对：逐个产物比对「母版时间戳」与「关键指标」。

用法:
    python -m wds.qa.audit_dist --master <母版.ttf> --dist <交付目录>
"""
from __future__ import annotations
import argparse, os, sys, time
from fontTools.ttLib import TTFont

WEIGHTS = [("Thin",250),("Light",300),("Normal",350),("Regular",400),
           ("Medium",500),("Bold",700),("Heavy",900)]
EXT_A = range(0x0100, 0x0180)


def metrics(path):
    f = TTFont(path, lazy=True)
    cm = f.getBestCmap()
    d = {
        "cmap": len(cm),
        "ext_a": sum(1 for c in EXT_A if c in cm),
        "glyphs": len(f.getGlyphOrder()),
        "fvar": "fvar" in f,
        "size": os.path.getsize(path),
        "mtime": time.strftime("%H:%M", time.localtime(os.path.getmtime(path))),
    }
    f.close()
    return d


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--dist", required=True)
    a = ap.parse_args(argv)

    m = metrics(a.master)
    print("母版: cmap=%d ext_a=%d glyphs=%d fvar=%s 时间=%s" % (
        m["cmap"], m["ext_a"], m["glyphs"], m["fvar"], m["mtime"]))
    print()

    bad = 0
    rows = []
    for name, w in WEIGHTS:
        for ext in ("ttf", "woff2"):
            p = os.path.join(a.dist, "WDesignSansSC-%s.%s" % (name, ext))
            if not os.path.exists(p):
                rows.append(("MISSING", name, ext, "", "")); bad += 1; continue
            d = metrics(p)
            ok = d["cmap"] == m["cmap"] and d["ext_a"] == m["ext_a"]
            tag = "OK" if ok else "**过期**"
            if not ok: bad += 1
            rows.append((tag, name, ext, "cmap=%d ext_a=%d" % (d["cmap"], d["ext_a"]), d["mtime"]))

    p = os.path.join(a.dist, "WDesignSansSC-VF.woff2")
    if os.path.exists(p):
        d = metrics(p)
        ok = d["cmap"] == m["cmap"] and d["ext_a"] == m["ext_a"] and d["fvar"]
        tag = "OK" if ok else "**过期**"
        if not ok: bad += 1
        rows.append((tag, "VF", "woff2", "cmap=%d ext_a=%d fvar=%s" % (
            d["cmap"], d["ext_a"], d["fvar"]), d["mtime"]))
    else:
        rows.append(("MISSING", "VF", "woff2", "", "")); bad += 1

    print("%-8s %-8s %-6s %-28s %s" % ("状态","档位","格式","指标","时间"))
    for r in rows:
        print("%-8s %-8s %-6s %-28s %s" % r)
    print()
    print("结论:", "全部一致" if bad == 0 else "%d 个产物与母版不一致" % bad)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())