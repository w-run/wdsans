# glow-sans 管线：复现与 Mona 接入

> P1 实测记录。环境：CloudStudio `wdsans-build-1`（uiuelm）。

## 1. 构建链

```
fonts/init.sh  (SHS 2.001R + Fira)
   ↓ otfccdump --pretty --ignore-glyph-order --hex-cmap
fonts/<family>/*.json
   ├ extract-gid-categories  → build-files/extracted/{base-scale,center-scale,lengthen,punc-like}-sc/<w>.json
   ├ extract-shs-features    → build-files/features/{gsub,gpos}-sc/<w>.json
   ├ (han) extract + CV      → build-files/models/shs-sc/<w>/gid-NN.json   (31 分片 × 7 档)
   └ kana-like (用 SHS-J)    → build-files/models/kana-like/<w>.json
   ↓ node scripts/wds_build.js [wght]
build-mona/WDesignSans-<style>.otf
```

自写脚本（本仓库 `vendor/glow-src/scripts/`）：
- `wds_prepare.js` — 分类 + 特性一次性导出
- `wds_extract.js` — 一次读一档字体，提全部 31 分片（55s/7档）
- `wds_build.js` — 7 档构建，参数模板映射到 Mona 目标字重

## 2. Mona 接入

三步：
1. 实例化：`varLib.instancer MonaSansVF.ttf wght=<w> wdth=100 opsz=14`
   - Mona 三轴：wdth 75–125（默认 100）、wght 200–900（**默认 200**）、opsz 0–100（默认 0）
   - 三轴必须全给，否则拿到的是 200 字重
2. dump：`otfccdump Mona-<w>.ttf --pretty --ignore-glyph-order --hex-cmap -o fonts/Mona/Mona-<w>.json`
3. 改两处：
   - `res/glyph-data.js` 加 `monaFont(weight)`
   - `build-font.js` 拉丁分支加 `param.mona`，参数删掉 `fira`/`raleway`

**`latinscale = 733/729 = 1.00549`** → 实测 cap 733 / xh 520。
参照实测：OPPO H=733 x=519，HOS H=732 x=519 —— 520 正确，DESIGN.md 的 529 是笔误。

## 3. 参数模板映射

7 档取同 shs 源字重的 glow 参数：

| 本档 | glow 模板 | shs |
|---|---|---|
| 250 Thin | glow/200 | 0 |
| 300 Light | glow/300 | 1 |
| 350 Normal | glow/400 | 2 |
| 400 Regular | glow/500 | 3 |
| 500 Medium | glow/600 | 4 |
| 700 Bold | glow/700 | 5 |
| 900 Heavy | glow/900 | 6 |

## 4. 环境坑（已解）

1. `from cv2 import cv2` → `import cv2`
2. `cv2.findContours` 在 opencv4 返回 2 值 → `_res[-2]`
3. 版本锁定：numpy 1.26.4 / opencv-python-headless 4.10 / scikit-image 0.22
4. Node 依赖只装 `caryll-shapeops + progress + clipper-lib + bezier-js` 到 `/tmp/deps` 再软链；
   **不要 npm install**（会拉 canvas 原生编译失败）
5. `build-font.js` 末尾 `bar.update(1)` 在 showProgress=false 时崩 → 加 `if (bar)`
6. otfcc 用 premake5（不是 cmake）；默认 ninja 只建 otfccdump，build 需
   `ninja -f build_otfccbuild_release_x64.ninja`

## 5. 性能与执行约束（重要）

| 项 | 实测 |
|---|---|
| 单分片 CV（1024 字形） | 4 分 20 秒，单核 |
| 30 并发 | **无加速**（IO/配额瓶颈），单任务劣化到 20+ 分钟 |
| 建议并发 | **6** |
| 全量 | 217 任务 × 4.4 分 / 6 ≈ **2.5 小时** |
| 扩展 A 区分片（gid-04） | 有超慢字形，单分片跑过 41 分钟未完成 |
| 后台任务 | `nohup`/`setsid` 都会被 CloudStudio 回收，**只能前台分段跑**（每段 ≤ 20 分钟） |
| /dev/shm | 仅 64MB，不能当内存盘 |

## 6. 已完成 / 待办

- [x] 管线跑通，`WDesignSans-Regular.otf` 8912 字形构建成功
- [x] cap 733 / xh 520 / upm 1000 / wght 400 达标；GSUB/GPOS/GDEF/BASE/vhea/vmtx 全在
- [x] kana-like Regular 模型
- [ ] 全量模型：Regular 7/31 分片，其余 6 档 0/31
- [ ] 末端斜切仍在（`flattenends 0.75` + `endsremoval true` 从 glow 继承），按 DESIGN 应为 0 / false
- [ ] hhea 1160/-288（glow 的 tables/hhea.js 硬编码），需接行高修复
- [ ] kana-like 其余 6 档

## 7. TTF 拉丁源的曲线退化（已修，重要）

Mona Sans 是 **TrueType（glyf，二次贝塞尔）**，而 glow-sans 管线假设拉丁源是 **CFF（三次贝塞尔）**——Fira 和 Raleway 都是 OTF/CFF，所以原作者没遇到。

`otfccdump` 直接读 TTF 会把部分曲线段退化成直线：

| | Mona 原版 | 直接用 otfccdump |
|---|---|---|
| `O` 的绘制指令 | `qCurveTo × 8` | `curveTo × 8` + **`lineTo × 6`** |
| 渲染结果 | 圆 | **八边形** |

**修法**：dump 后重写 contours，用 fontTools 精确转三次：

```python
cp  = ContourPen(glyphSet)
pen = Qu2CuPen(cp, max_err=0.5, all_cubic=True)
glyphSet[name].draw(pen)
json['glyf'][name]['contours'] = cp.contours
```

脚本：`scripts/fix_mona_curves.py <Mona-N.ttf> <Mona-N.json> <out.json>`

验证（110px 渲染，"Aa Oo 123"）：修复后 ink 高度 81px，与 Mona 原版**完全一致**；修复前 O 为八边形。

> 教训：**任何 TTF 拉丁源都要先过 Qu2CuPen**，不能直接喂 otfccdump。
