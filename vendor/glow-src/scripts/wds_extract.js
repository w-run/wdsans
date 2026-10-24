// 一次读一档字体，按 31 个 gid 分片全部提取，避免反复加载 300MB JSON
const fs = require('fs');

const W = ['ExtraLight', 'Light', 'Normal', 'Regular', 'Medium', 'Bold', 'Heavy'];
const GID_DIR = 'encoding/gid/shs-sc-han';
const tsvs = fs.readdirSync(GID_DIR).filter(f => f.endsWith('.tsv')).sort();

const files = tsvs.map(t => ({
  name: t,
  gids: fs.readFileSync(`${GID_DIR}/${t}`).toString()
    .split('\n').map(l => l.split('\t')[0]).filter(Boolean),
}));

for (const w of W) {
  const p = `fonts/SourceHanSansSC/SourceHanSansSC-${w}.json`;
  let font;
  try {
    font = JSON.parse(fs.readFileSync(p).toString());
  } catch (e) {
    console.error(`SKIP ${w}: ${e.message}`);
    continue;
  }
  const outDir = `build-files/extracted/shs-sc/${w}`;
  fs.mkdirSync(outDir, { recursive: true });
  let total = 0;
  for (const f of files) {
    const out = {};
    for (const g of f.gids) {
      const gd = font.glyf[g];
      if (!gd) continue;
      const vo = gd.verticalOrigin;
      out[g] = gd.contours.map(c => c.map(pt => ({
        x: pt.x, y: pt.y + 1000 - vo, on: pt.on,
      })));
      total++;
    }
    fs.writeFileSync(`${outDir}/${f.name.replace('.tsv', '.json')}`, JSON.stringify(out));
  }
  console.log(`${w}: ${files.length} shards, ${total} glyphs`);
  font = null;
}
