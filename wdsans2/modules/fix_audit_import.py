#!/usr/bin/env python3
# fix_audit_import - add contours_from_pen import
P = '/workspace/wdsans2/modules/audit_geom.py'
s = open(P, encoding="utf-8").read()
if "contours_from_pen" in s and "from canonpen3 import" not in s:
    s = s.replace(
        "from fontTools.pens.boundsPen import BoundsPen",
        "from fontTools.pens.boundsPen import BoundsPen\nfrom canonpen3 import contours_from_pen"
    )
    open(P, "w", encoding="utf-8").write(s)
    print("import added")
else:
    print("skip")