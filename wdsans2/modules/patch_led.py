P = '/workspace/wdsans2/modules/audit_geom.py'
lines = open(P, encoding="utf-8").read().split("\n")
block = [
    "# m_ledge: DEPRECATED - removed from chain in R29 (see AGENTS.md)",
    "#   v1 1182 chars / v2 2636 chars / v3 1511 chars but damaged 1456 glyphs",
    "#   root cause: cannot distinguish whole-glyph top bar from left-radical bar",
    "rec('ledge', 'SKIP', 'deprecated: m_ledge damaged 1456 glyphs, removed in R29')",
    "",
]
si = ei = None
for i, l in enumerate(lines):
    if l.startswith("# m_ledge:"):
        si = i
    if "# m_latinext: Latin Ext-A" in l:
        ei = i
        break
if si is None or ei is None or ei <= si:
    print("ANCHOR FAIL", si, ei)
else:
    lines = lines[:si] + block + lines[ei:]
    open(P, "w", encoding="utf-8").write("\n".join(lines))
    print("replaced", si, "->", ei - 1)