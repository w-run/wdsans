#!/bin/sh
# 重新获取参照字体。已存在的文件跳过。
set -e
cd "$(dirname "$0")"

JSD="https://cdn.jsdelivr.net/gh"

need() { [ -s "$1" ] && return 1; return 0; }

echo "== shs 静态字重（从本地 TTC 导出）"
TTC="/var/minis/shared/fonts/src/SourceHanSans.ttc"
if [ -f "$TTC" ]; then
  python3 - <<'PY'
from fontTools.ttLib import TTCollection
import os
want={"ExtraLight":250,"Light":300,"Normal":350,"Regular":400,"Medium":500,"Bold":700,"Heavy":900}
ttc=TTCollection("/var/minis/shared/fonts/src/SourceHanSans.ttc", lazy=True)
for f in ttc.fonts:
    n=f['name'].getDebugName(4) or ""
    if n.startswith("Source Han Sans SC") and "HW" not in n:
        s=n.replace("Source Han Sans SC","").strip() or "Regular"
        if s in want:
            out=f"shs/shs-{want[s]}.otf"
            if not os.path.exists(out):
                f.save(out); print("  ", out)
PY
else
  echo "  跳过：没有本地 TTC，请先下载"
  echo "  https://github.com/adobe-fonts/source-han-sans/releases/download/2.005R/01_SourceHanSans.ttc.zip"
fi

if need shs/shs-vf.otf; then
  echo "== shs VF（需手动放置 31.7MB 的 SourceHanSansSC-VF.otf）"
fi

echo "== hos VF"
need hos/hos-vf.ttf && curl -sL --max-time 300 -o hos/hos-vf.ttf \
  "$JSD/kanami09/HarmonyOS-Sans-Font@master/files/HarmonyOS_Sans_SC.ttf" && echo "  ok"

echo "== hos 静态"
for pair in "Thin:250" "Light:300" "Regular:400" "Medium:500" "Bold:700" "Black:900"; do
  s=${pair%%:*}; w=${pair#*:}
  out="hos/hos-$w.ttf"
  need "$out" && curl -sL --max-time 180 -o "$out" \
    "$JSD/ajacocks/harmonyos-sans-font@master/HarmonyOS_Sans_SC/HarmonyOS_Sans_SC_$s.ttf" && echo "  $out"
done

echo "== ops 静态（注意：300/900 是精简版，只 6763 个 CJK）"
for pair in "L:300" "R:400" "M:500" "B:700" "H:900"; do
  k=${pair%%:*}; w=${pair#*:}
  out="ops/ops-$w.ttf"
  need "$out" && curl -sL --max-time 300 -o "$out" \
    "$JSD/cooingwu/OPPO-Sans@master/OPPOSans-$k.ttf" && echo "  $out"
done

echo "== wdo（从已废弃项目复制）"
OLD="/var/minis/shared/wdsans202506"
for pair in "Thin:250" "Light:300" "Normal:350" "Regular:400" "Medium:500" "Bold:700" "Heavy:900"; do
  s=${pair%%:*}; w=${pair#*:}
  out="wdo/wdo-$w.ttf"
  if need "$out" && [ -f "$OLD/WDesignSans-$s.ttf" ]; then
    cp "$OLD/WDesignSans-$s.ttf" "$out" && echo "  $out"
  fi
done

echo "完成。核对："
du -sh shs hos ops wdo 2>/dev/null
