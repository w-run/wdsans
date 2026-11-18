import sys, json
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_boxrad
cps=json.load(open("/workspace/wdsans2/build/box_lr.json"))
FN={"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
SW={"250":29.0,"400":67.0,"900":127.0}
hits={}
for tag in ["250","400","900"]:
    m_boxrad.BOTTOM_EXTEND = 80.0*(SW[tag]/67.0)
    f=TTFont("/workspace/wdsans2/build/masters_R32/"+FN[tag],lazy=True)
    gs=f.getGlyphSet(); cm=f.getBestCmap()
    s=set()
    for cp in cps:
        if cp not in cm: continue
        rp=RecordingPen()
        try: gs[cm[cp]].draw(rp)
        except Exception: continue
        if m_boxrad.find(contours_from_pen(rp.value)): s.add(cp)
    f.close(); hits[tag]=s
    print("%s: %d" % (tag, len(s)))
print()
only400 = hits["400"]-hits["250"]
print("400有250无: %d 字 -> %s" % (len(only400), "".join(chr(c) for c in sorted(only400))))
only900 = hits["900"]-hits["250"]
print("900有250无: %d 字 -> %s" % (len(only900), "".join(chr(c) for c in sorted(only900))))