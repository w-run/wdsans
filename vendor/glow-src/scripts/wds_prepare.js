// WDesign Sans 专用：只从 SC 生成 build-files 中间产物
// 用法: node scripts/wds_prepare.js
const fs = require('fs');

const W = ['ExtraLight', 'Light', 'Normal', 'Regular', 'Medium', 'Bold', 'Heavy'];
const SC = w => JSON.parse(
  fs.readFileSync(`fonts/SourceHanSansSC/SourceHanSansSC-${w}.json`).toString());

// 1. gid 分类（base-scale / center-scale / lengthen / punc-like）
['base-scale', 'center-scale', 'lengthen', 'punc-like'].forEach(cat => {
  const dir = `build-files/extracted/${cat}-sc`;
  fs.mkdirSync(dir, { recursive: true });
  const gids = fs.readFileSync(`encoding/gid/${cat}.tsv`).toString()
    .split('\n').map(l => l.split('\t')[0]).filter(Boolean);
  W.forEach(w => {
    const f = SC(w);
    const out = {};
    let missing = 0;
    gids.forEach(g => { if (f.glyf[g]) out[g] = f.glyf[g]; else missing++; });
    fs.writeFileSync(`${dir}/${w}.json`, JSON.stringify(out));
    console.log(`extracted/${cat}-sc/${w}.json  ${Object.keys(out).length} glyphs, missing ${missing}`);
  });
});

// 2. GSUB / GPOS（原样搬运，不裁剪）
['GSUB', 'GPOS'].forEach(t => {
  const dir = `build-files/features/${t.toLowerCase()}-sc`;
  fs.mkdirSync(dir, { recursive: true });
  W.forEach(w => {
    fs.writeFileSync(`${dir}/${w}.json`, JSON.stringify(SC(w)[t]));
    console.log(`features/${t.toLowerCase()}-sc/${w}.json`);
  });
});
