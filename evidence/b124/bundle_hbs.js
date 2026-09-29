#!/usr/bin/env node
// B124 step 3: prove the compiled hbs! template modules against their readable .hbs sources by re-running the
// Handlebars compiler that Tridium ships (organized/js/extracted/rc/handlebars/handlebars.js) and comparing the
// template spec object with the one embedded in the bundle. Usage: node bundle_hbs.js ORGANIZED census.json OUT.json
const fs = require('fs'), path = require('path'), acorn = require('acorn');
const [org, censusFile, outFile] = process.argv.slice(2);
const L = require('./b124_lib.js'); L.setOrg(org);
const hbsPath = path.join(org, 'js/extracted/rc/handlebars/handlebars.js');
const Handlebars = require(hbsPath);
const census = JSON.parse(fs.readFileSync(censusFile, 'utf8')).bundles;

function specOf(text) {
  const call = acorn.parse(text, { ecmaVersion: 'latest' }).body[0].expression;
  let spec = null;
  (function walk(n) {
    if (!n || typeof n.type !== 'string' || spec) return;
    if (n.type === 'CallExpression' && n.callee.type === 'MemberExpression' && n.callee.property.name === 'template') { spec = text.slice(n.arguments[0].start, n.arguments[0].end); return; }
    for (const k of Object.keys(n)) { const v = n[k]; if (Array.isArray(v)) v.forEach(walk); else if (v && typeof v.type === 'string') walk(v); }
  })(call);
  return spec;
}

(async () => {
  const rows = [];
  for (const b of census) {
    const bsrc = fs.readFileSync(path.join(org, b.path), 'utf8');
    for (const d of b.defs.filter((x) => x.id.startsWith('hbs!'))) {
      const row = { bundle: b.path, id: d.id, bytes: d.bytes };
      const hit = L.candidates(d.id, b.module).out.find((p) => fs.existsSync(path.join(org, p)));
      if (!hit) { row.cls = 'HBS-NO-SOURCE'; rows.push(row); continue; }
      row.readable = hit;
      try {
        const spec = specOf(bsrc.slice(d.start, d.end));
        if (!spec) { row.cls = 'HBS-NO-TEMPLATE-CALL'; rows.push(row); continue; }
        const pre = Handlebars.precompile(fs.readFileSync(path.join(org, hit), 'utf8'));
        const [x, y] = [await L.norm(pre, 'compress'), await L.norm(spec, 'compress')];
        row.cls = x === y ? 'HBS-RECOMPILE-MATCH' : 'HBS-DIFFERS';
        if (x !== y) { let i = 0; while (x[i] === y[i]) i++; row.diff = { at: i, pre: x.slice(Math.max(0, i - 50), i + 80), bundle: y.slice(Math.max(0, i - 50), i + 80) }; }
      } catch (e) { row.cls = 'HBS-ERROR'; row.err = String(e).slice(0, 160); }
      rows.push(row);
    }
  }
  fs.writeFileSync(outFile, JSON.stringify(rows, null, 1));
  const t = {}; rows.forEach((r) => { t[r.cls] = (t[r.cls] || 0) + 1; }); console.log(t);
})();
