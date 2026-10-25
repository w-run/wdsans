const fs = require('fs');
const { readModels } = require('./src/font-build/res/glyph-data');
const GM = require('./src/glyph-manipulate/GlyphModel');
const m = readModels('build-files/models/shs-sc/Regular/gid-14.json');
const g = m['uni6C38'];
const out = new GM(g).restore();
fs.writeFileSync('/tmp/js_restore.json', JSON.stringify(out));
console.log('js contours', out.length, 'pts', out.reduce((s,c)=>s+c.length,0));
