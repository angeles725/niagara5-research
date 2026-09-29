#!/usr/bin/env node
// B124 step 4: account for the bytes of each bundle that are NOT define() modules:
//  (a) top-level prelude statements (Babel helpers, hoisted scripts): match each against a readable top-level
//      statement of the same name (terser-normalised) in the bundle's module, then in any module;
//  (b) "other" segments (vendor UMD libraries, require.config calls, IIFEs): 128-byte chunk coverage against the
//      module's shipped readable/vendor .js files, else statement-level match.
// Usage: node bundle_segments.js ORGANIZED census.json OUT.json
const fs = require('fs'), path = require('path'), acorn = require('acorn');
const [org, censusFile, outFile] = process.argv.slice(2);
const L = require('./b124_lib.js'); L.setOrg(org);
const census = JSON.parse(fs.readFileSync(censusFile, 'utf8')).bundles;

const stmtIndex = {};   // module -> Map(name -> [{file, text}])
function stmts(mod) {
  if (stmtIndex[mod]) return stmtIndex[mod];
  const m = new Map();
  for (const f of L.jsFiles(mod)) {
    let src, ast;
    try { src = fs.readFileSync(path.join(org, f), 'utf8'); ast = acorn.parse(src, { ecmaVersion: 'latest' }); } catch (e) { continue; }
    for (const st of ast.body) {
      let names = null;
      if (st.type === 'FunctionDeclaration') names = [st.id.name]; else if (st.type === 'VariableDeclaration') names = st.declarations.map((d) => d.id.name).filter(Boolean);
      if (names) for (const n of names) { if (!m.has(n)) m.set(n, []); m.get(n).push({ file: f, text: src.slice(st.start, st.end) }); }
    }
  }
  return (stmtIndex[mod] = m);
}
const allMods = () => fs.readdirSync(org).filter((x) => fs.existsSync(path.join(org, x, 'extracted')));

async function same(x, y) {  // terser first, then the second minifier (uglify): different but equivalent shapes converge there
  for (const mode of ['stmt', 'uglify']) { const [p, q] = [await L.norm(x, mode).catch(() => null), await L.norm(y, mode).catch(() => null)]; if (p && p === q) return mode; }
  return null;
}
// Fallback for a statement no oracle proved equal: share of the bundle statement's 24-char shingles (after
// uglify normalisation) found in the best same-named readable statement. NOT a proof, only how near it is.
async function nearest(bundleMod, name, text) {
  const grams = (s) => { const r = new Set(); for (let i = 0; i + 24 <= s.length; i++) r.add(s.slice(i, i + 24)); return r; };
  const mine = await L.norm(text, 'uglify').catch(() => text); const G = grams(mine); let best = null;
  for (const mod of [bundleMod]) for (const c of stmts(mod).get(name) || []) {
    const theirs = grams(await L.norm(c.text, 'uglify').catch(() => c.text)); let hit = 0; for (const x of G) if (theirs.has(x)) hit++;
    const r = G.size ? hit / G.size : 0; if (!best || r > best.ratio) best = { ratio: +r.toFixed(3), file: c.file };
  }
  return best;
}
async function proveStatement(bundleMod, name, text) {
  for (const mod of [bundleMod, ...allMods().filter((x) => x !== bundleMod)]) {
    for (const c of stmts(mod).get(name) || []) { const o = await same(text, c.text); if (o) return { how: mod === bundleMod ? 'same-module' : 'other-module', oracle: o, file: c.file }; }
  }
  return null;
}

async function smallMatch(mod, text) {   // a short top-level expression (require.config, IIFE, shim) vs readable top-level expressions
  for (const f of L.jsFiles(mod)) {
    let s, ast; try { s = fs.readFileSync(path.join(org, f), 'utf8'); ast = acorn.parse(s, { ecmaVersion: 'latest' }); } catch (e) { continue; }
    for (const st of ast.body) if (st.type === 'ExpressionStatement') { const o = await same(text, s.slice(st.expression.start, st.expression.end)); if (o) return o + ':' + f; }
  }
  return null;
}
function chunkCoverage(mod, seg) {
  const files = fs.readdirSync(org).includes(mod) ? walkAll(path.join(org, mod, 'extracted')) : [];
  const texts = files.map((f) => [path.relative(org, f), fs.readFileSync(f, 'utf8')]);
  const n = Math.floor(seg.length / 128); let best = { file: null, hit: 0 };
  const chunks = []; for (let i = 0; i < n; i++) chunks.push(seg.slice(i * 128, i * 128 + 128));
  for (const [f, t] of texts) { let hit = 0; for (const c of chunks) if (t.includes(c)) hit++; if (hit > best.hit) best = { file: f, hit }; }
  return { chunks: n, hit: best.hit, file: best.file };
}
function walkAll(d) { const r = []; for (const e of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, e.name); if (e.isDirectory()) r.push(...walkAll(p)); else if (/\.js$/.test(e.name) && !/\.built\.min\.js$/.test(e.name)) r.push(p); } return r; }
const strip = (t) => t.replace(/define\("[^"]+",/g, 'define(');   // r.js names anonymous vendor defines


(async () => {
  const out = { prelude: [], other: [] };
  for (const b of census) {
    const src = fs.readFileSync(path.join(org, b.path), 'utf8');
    for (const p of b.prelude) {
      const names = p.name.split(','); const text = src.slice(p.start, p.end);
      const r = names.length === 1 ? await proveStatement(b.module, names[0], text) : null;
      out.prelude.push({ bundle: b.path, name: p.name, bytes: p.end - p.start, proof: r, near: r || names.length !== 1 ? undefined : await nearest(b.module, names[0], text) });
    }
    for (const o of b.other) for (const pc of o.pieces) {
      const seg = src.slice(pc.start, pc.end);
      const row = { bundle: b.path, type: pc.type, bytes: seg.length, head: seg.slice(0, 60) };
      if (seg.length >= 1000) {
        row.chunks = chunkCoverage(b.module, seg);
        if (row.chunks.file) { const f = fs.readFileSync(path.join(org, row.chunks.file), 'utf8'); row.equal = await same(strip(seg), f); }
      } else row.equal = await smallMatch(b.module, seg);
      out.other.push(row);
    }
  }
  fs.writeFileSync(outFile, JSON.stringify(out, null, 1));
  const pb = out.prelude.reduce((t, r) => { const k = r.proof ? r.proof.how : 'UNPROVEN'; t[k] = t[k] || { n: 0, bytes: 0 }; t[k].n++; t[k].bytes += r.bytes; return t; }, {});
  console.log('prelude', JSON.stringify(pb)); console.log('other', out.other.map((o) => `${o.bundle.split('/')[0]}:${o.bytes}:${o.chunks ? o.chunks.hit + '/' + o.chunks.chunks + ' ' + o.chunks.file : '-'} equal=${o.equal}`).join('\n'));
})();
