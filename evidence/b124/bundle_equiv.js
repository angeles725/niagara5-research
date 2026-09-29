#!/usr/bin/env node
// B124 step 2: for every define() module in every bundle (census.json from bundle_census.js) locate the
// readable sibling and classify equivalence. Needs `acorn` and `terser` (npm i acorn terser; see README.md).
// Usage: node bundle_equiv.js ORGANIZED census.json OUT.json
const fs = require('fs'), path = require('path'), acorn = require('acorn');
const [org, censusFile, outFile] = process.argv.slice(2);
const census = JSON.parse(fs.readFileSync(censusFile, 'utf8')).bundles;

const L = require('./b124_lib.js'); L.setOrg(org);
const { candidates, aliasLookup, norm } = L;

function topDefine(src) {
  const ast = acorn.parse(src, { ecmaVersion: 'latest' });
  const found = [];
  for (const st of ast.body) if (st.type === 'ExpressionStatement' && st.expression.type === 'CallExpression' && st.expression.callee.name === 'define') found.push(st.expression);
  return found;
}
const factoryOf = (call, src) => { const a = call.arguments; const f = a[a.length - 1]; return f && /Function/.test(f.type) ? src.slice(f.start, f.end) : null; };
const depsSrc = (call, src) => { const a = call.arguments.filter((x) => x.type === 'ArrayExpression')[0]; return a ? src.slice(a.start, a.end) : '[]'; };


(async () => {
  const results = [];
  for (const b of census) {
    const bsrc = fs.readFileSync(path.join(org, b.path), 'utf8');
    for (const d of b.defs) {
      const row = { bundle: b.path, module: b.module, id: d.id, bytes: d.bytes };
      const { kind, out } = candidates(d.id, b.module);
      let hit = out.find((p) => fs.existsSync(path.join(org, p)));
      if (!hit && kind === 'js') { hit = aliasLookup(d.id, b.module); if (hit) row.alias = true; }
      if (!hit) { row.cls = kind === 'hbs' ? 'NO-READABLE-SOURCE-TEMPLATE' : 'NO-READABLE-SOURCE'; row.tried = out; results.push(row); continue; }
      row.readable = hit;
      if (kind === 'hbs') { row.cls = 'TEMPLATE-PATH-ONLY'; row.readableBytes = fs.statSync(path.join(org, hit)).size; results.push(row); continue; }
      try {
        const rsrc = fs.readFileSync(path.join(org, hit), 'utf8');
        const calls = topDefine(rsrc);
        if (calls.length !== 1) {
          const bt0 = bsrc.slice(d.start, d.end), bA0 = acorn.parse(bt0, { ecmaVersion: 'latest' }).body[0].expression;
          const fb = factoryOf(bA0, bt0);
          row.cls = calls.length === 0 ? 'SCRIPT-NO-DEFINE' : 'READABLE-DEFINE-COUNT'; row.count = calls.length;
          row.bundleFactory = fb ? fb.length : null; row.bundleFactoryEmpty = fb ? /^function\(\)\{\}$/.test(fb.replace(/\s+/g, '')) : null;
          results.push(row); continue;
        }
        const bt = bsrc.slice(d.start, d.end);
        const bAst = acorn.parse(bt, { ecmaVersion: 'latest' }).body[0].expression;
        const rf = factoryOf(calls[0], rsrc), bf = factoryOf(bAst, bt);
        row.depsEqual = (await norm(depsSrc(calls[0], rsrc), 'compress')) === (await norm(depsSrc(bAst, bt), 'compress'));
        if (/^function\(\)\{\}$/.test(bf.replace(/\s+/g, ''))) { row.cls = 'EMPTY-STUB'; results.push(row); continue; }   // define("id",function(){}): content lives under another id
        const c = await L.classify(rf, bf); row.tier = c.tier; if (!c.tier) row.skel = c; else if (c.ratio) { row.ratio = c.ratio; row.ordered = c.ordered; }
        row.cls = c.tier === 'mangle' ? 'IDENTICAL-AFTER-MINIFY' : c.tier === 'skeleton' ? 'SKELETON-MATCH' : c.tier ? 'SEMANTIC-MATCH' : 'DIFFERS';
      } catch (e) { row.cls = 'ERROR'; row.err = String(e).slice(0, 200); }
      results.push(row);
    }
  }
  fs.writeFileSync(outFile, JSON.stringify(results, null, 1));
  const tally = {}; for (const r of results) tally[r.cls] = (tally[r.cls] || 0) + 1;
  console.log(tally);
})();
