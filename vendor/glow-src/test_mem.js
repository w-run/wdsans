const fs = require('fs');
const { readModels, listHanModelPaths } = require('/var/minis/shared/projects/wdsans/vendor/glow-src/src/font-build/res/glyph-data');
const gf = require('/var/minis/shared/projects/wdsans/vendor/glow-src/src/font-build/glyph-filters');
const p = JSON.parse(fs.readFileSync('parameters/wds/Regular.json'));
delete p.fira; delete p.raleway; p.mona = 400; p.shs = 3;
const mf = gf.hanModelFilter(p), pf = gf.hanPostFilter(p);
const models = readModels(listHanModelPaths('SC', 'Regular')[0]);
const keys = Object.keys(models);
console.error('total', keys.length);
let i = 0;
for (const k of keys) {
  gf.model2Glyph(models[k], p.baseline, p.width, mf, pf);
  i++;
  if (i % 100 === 0) {
    const m = process.memoryUsage();
    console.error(`${i} heap=${Math.round(m.heapUsed/1e6)}MB rss=${Math.round(m.rss/1e6)}MB`);
  }
}
console.error('done', i);
