"""补齐 STAT 与 vendor：让七档命名实例在任何系统上都正确。"""
from __future__ import annotations
from fontTools.ttLib import TTFont
from fontTools.otlLib.builder import buildStatTable
from .rename import STOPS

VENDOR_ID = "WDGN"

def fix_vendor(font: TTFont):
    font["OS/2"].achVendID = VENDOR_ID
    return VENDOR_ID

def rebuild_stat(font: TTFont):
    axes = [{"tag": "wght", "name": "Weight", "ordering": 0,
             "minimum": 250, "default": 400, "maximum": 900}]
    values = []
    for wght, sub in STOPS:
        v = {"name": sub, "location": {"wght": wght}}
        if sub == "Regular":
            v["flags"] = 0x2
        values.append(v)
    buildStatTable(font, axes, values, elidedFallbackName="Regular")
    return len(values)