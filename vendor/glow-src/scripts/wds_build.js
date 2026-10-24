// WDesign Sans 构建：严格 7 档、只出 Normal 宽度、拉丁用 Mona
// 用法: node scripts/wds_build.js [仅构建某个 wght，如 400]
const fs = require('fs');
const cp = require('child_process');
const path = require('path');
const buildFont = require('../src/font-build/build-font');

const ROOT = path.join(__dirname, '..');
const VERSION = '2026.100';

// 目标档 -> glow 参数模板（同为 shs 源字重）、拉丁目标 wght
const STOPS = [
  { wght: 250, name: 'Thin',    tmpl: 'glow/200', shsIdx: 0 },
  { wght: 300, name: 'Light',   tmpl: 'glow/300', shsIdx: 1 },
  { wght: 350, name: 'Normal',  tmpl: 'glow/400', shsIdx: 2 },
  { wght: 400, name: 'Regular', tmpl: 'glow/500', shsIdx: 3 },
  { wght: 500, name: 'Medium',  tmpl: 'glow/600', shsIdx: 4 },
  { wght: 700, name: 'Bold',    tmpl: 'glow/700', shsIdx: 5 },
  { wght: 900, name: 'Heavy',   tmpl: 'glow/900', shsIdx: 6 },
];

// cap 对齐：Mona 729 -> 733
const LATINSCALE = 733 / 729;

function loadParam(stop, overrides) {
  const p = JSON.parse(
    fs.readFileSync(path.join(ROOT, 'parameters', stop.tmpl + '.json')).toString());
  delete p.fira;
  delete p.raleway;
  p.mona = stop.wght;
  p.latinscale = LATINSCALE;
  p.shs = stop.shsIdx;
  Object.assign(p, overrides || {});
  return p;
}

function buildOne(stop, overrides, outDir) {
  const param = loadParam(stop, overrides);
  console.log(`[${stop.wght} ${stop.name}] param=${JSON.stringify(param)}`);
  const t0 = Date.now();
  const font = buildFont(param, 'SC', 'Normal', 5, stop.name, stop.wght,
    VERSION, false);
  const otfccDir = path.join(ROOT, 'build-files/otfcc/WDesignSans');
  fs.mkdirSync(otfccDir, { recursive: true });
  const jsonPath = path.join(otfccDir, `WDesignSans-${stop.name}.json`);
  const otfPath = path.join(outDir, `WDesignSans-${stop.name}.otf`);
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(jsonPath, JSON.stringify(font));
  cp.execSync(`otfccbuild -q --dummy-dsig --merge-features --merge-lookups ` +
    `--subroutinize "${jsonPath}" -o "${otfPath}"`, { stdio: 'inherit' });
  const glyphs = Object.keys(font.glyf).length;
  console.log(`  -> ${otfPath}  ${glyphs} glyphs  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  return otfPath;
}

function main() {
  const only = process.argv[2] ? parseInt(process.argv[2]) : null;
  const outDir = path.join(ROOT, process.env.WDS_OUT || 'build');
  for (const stop of STOPS) {
    if (only && stop.wght !== only) continue;
    buildOne(stop, {}, outDir);
  }
}

main();
