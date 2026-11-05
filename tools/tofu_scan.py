
import json, sys, time, unicodedata
import numpy as np
import freetype
import uharfbuzz as hb
from fontTools.ttLib import TTFont

PATH = "/data/build-cache/wdsans-dist/WDesignSansSC-Regular.ttf"
OUT  = "/tmp/tofu_scan_result.json"
t0 = time.time()

def log(*a):
    print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)

# ---------- 1. cmap ----------
f = TTFont(PATH, lazy=True)
cmap = f.getBestCmap()
cps = sorted(cmap.keys())
log("cmap codepoints:", len(cps), "glyphs in maxp:", f["maxp"].numGlyphs)
glyph_order = f.getGlyphOrder()

# ---------- 2. harfbuzz: cp -> gid (shape) ----------
data = open(PATH, "rb").read()
blob = hb.Blob(data)
face = hb.Face(blob)
hbfont = hb.Font(face)
upem = face.upem
log("upem", upem, "hb glyph count", face.glyph_count)

hb_gid = {}
hb_adv = {}
gid0_list = []
for cp in cps:
    buf = hb.Buffer()
    buf.add_str(chr(cp))
    buf.guess_segment_properties()
    hb.shape(hbfont, buf)
    infos = buf.glyph_infos
    poss = buf.glyph_positions
    g = infos[0].codepoint if len(infos) else 0
    hb_gid[cp] = g
    hb_adv[cp] = poss[0].x_advance if len(poss) else 0
    if g == 0:
        gid0_list.append(cp)
log("hb shape done. gid0 count:", len(gid0_list))

# ---------- 3. freetype render: gid -> ink pixels ----------
ftface = freetype.Face(PATH)
PX = 100
ftface.set_pixel_sizes(0, PX)
log("ft px size", PX, "num_glyphs", ftface.num_glyphs)

ink = np.zeros(ftface.num_glyphs, dtype=np.int64)
wmax = np.zeros(ftface.num_glyphs, dtype=np.int64)
hmax = np.zeros(ftface.num_glyphs, dtype=np.int64)
ncont = np.zeros(ftface.num_glyphs, dtype=np.int32)
ok = np.zeros(ftface.num_glyphs, dtype=bool)

FLAGS = freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_AUTOHINT
for gid in range(ftface.num_glyphs):
    try:
        ftface.load_glyph(gid, FLAGS)
    except Exception:
        continue
    slot = ftface.glyph
    ok[gid] = True
    try:
        ncont[gid] = len(slot.outline.contours) if slot.outline.contours else 0
    except Exception:
        ncont[gid] = 0
    slot.render(freetype.FT_RENDER_MODE_NORMAL)
    bm = slot.bitmap
    buf_ = bm.buffer
    if buf_ is None or not len(buf_):
        ink[gid] = 0
        continue
    arr = np.frombuffer(bytes(buf_), dtype=np.uint8)
    ink[gid] = int(np.count_nonzero(arr))
    wmax[gid] = bm.width
    hmax[gid] = bm.rows
    if gid % 5000 == 0:
        log("render progress", gid, "/", ftface.num_glyphs)
log("freetype render done")

# ---------- 4. classify ----------
# legal blank characters
LEGAL_BLANK = set()
LEGAL_BLANK |= set(range(0x0000, 0x0021))          # C0 controls + space
LEGAL_BLANK |= {0x007F}
LEGAL_BLANK |= set(range(0x0080, 0x00A1))          # C1 controls
LEGAL_BLANK |= {0x00A0, 0x00AD, 0x061C, 0x115F, 0x1160, 0x1680, 0x17B4, 0x17B5,
                0x180B, 0x180C, 0x180D, 0x180E, 0x180F,
                0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007,
                0x2008, 0x2009, 0x200A, 0x200B, 0x200C, 0x200D, 0x200E, 0x200F,
                0x2028, 0x2029, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x202F,
                0x205F, 0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0x2065, 0x2066,
                0x2067, 0x2068, 0x2069, 0x206A, 0x206B, 0x206C, 0x206D, 0x206E,
                0x206F, 0x3000, 0x3164, 0xFE00, 0xFEFF, 0xFFA0, 0xFFF9, 0xFFFA,
                0xFFFB, 0xFEFF}
LEGAL_BLANK |= set(range(0xFE00, 0xFE10))   # variation selectors
LEGAL_BLANK |= set(range(0xE0100, 0xE01F0)) # VS supplement
LEGAL_BLANK |= set(range(0xE0000, 0xE0080)) # tags
LEGAL_BLANK |= set(range(0xFE20, 0xFE30))   # actually combining half marks - has ink, keep but harmless

def legal_blank(cp):
    if cp in LEGAL_BLANK:
        return True
    cat = unicodedata.category(chr(cp))
    if cat in ("Cc", "Cf", "Cs"):
        return True
    return False

blank = []       # gid!=0 but renders blank   (tofu candidates)
zero_cont = []   # gid!=0 but zero contours (cross-check)
for cp in cps:
    g = hb_gid[cp]
    if g == 0:
        continue
    if g < len(ink) and ink[g] == 0:
        blank.append(cp)

blank_legal = [c for c in blank if legal_blank(c)]
blank_illegal = [c for c in blank if not legal_blank(c)]

def desc(cp):
    try:
        n = unicodedata.name(chr(cp))
    except ValueError:
        n = "<no name>"
    cat = unicodedata.category(chr(cp))
    g = hb_gid[cp]
    return {
        "cp": f"U+{cp:04X}",
        "char": chr(cp),
        "name": n,
        "category": cat,
        "gid": g,
        "gname": glyph_order[g] if g < len(glyph_order) else "?",
        "adv": int(hb_adv[cp]),
        "ink": int(ink[g]) if g < len(ink) else -1,
        "contours": int(ncont[g]) if g < len(ncont) else -1,
    }

res = {
    "font": PATH,
    "upem": upem,
    "num_glyphs": int(ftface.num_glyphs),
    "cmap_count": len(cps),
    "gid0_count": len(gid0_list),
    "gid0_sample": [f"U+{c:04X}" for c in gid0_list[:60]],
    "blank_total": len(blank),
    "blank_legal_count": len(blank_legal),
    "blank_legal_samples": [desc(c) for c in blank_legal[:200]],
    "blank_illegal_count": len(blank_illegal),
    "blank_illegal": [desc(c) for c in blank_illegal],
    "elapsed": round(time.time()-t0, 1),
}
with open(OUT, "w") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
log("DONE", "gid0:", len(gid0_list), "blank:", len(blank), "illegal:", len(blank_illegal),
    "legal:", len(blank_legal))
print(json.dumps({k: res[k] for k in ("cmap_count","gid0_count","blank_total","blank_legal_count","blank_illegal_count")}, ensure_ascii=False))

