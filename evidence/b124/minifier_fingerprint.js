#!/usr/bin/env node
// B124 step 7: which minifier produced the bundles? For a sample of define() factories, minify the readable
// source with terser and with uglify-js (default compress, no mangle), canonicalise identifier names on both
// sides with one neutral pass (terser compress:false, mangle:true) and count byte-equal results against the
// bundle's own factory. Usage: node minifier_fingerprint.js ORGANIZED census.json equiv.json OUT.json [N=300]
const fs = require('fs'), path = require('path'), acorn = require('acorn'), T = require('terser'), U = require('uglify-js');
const [org, censusFile, equivFile, outFile, nArg] = process.argv.slice(2); const N = +(nArg || 300);
const census = JSON.parse(fs.readFileSync(censusFile, 'utf8')).bundles;
const eq = JSON.parse(fs.readFileSync(equivFile, 'utf8')).filter((r) => r.readable && r.bytes > 300 && !/^(SCRIPT|TEMPLATE|NO-)/.test(r.cls));
const src = {}, defs = new Map();
for (const b of census) { src[b.path] = fs.readFileSync(path.join(org, b.path), 'utf8'); for (const d of b.defs) defs.set(b.path + '|' + d.id, d); }
const fac = (text) => { const c = acorn.parse(text, { ecmaVersion: 'latest' }).body.map((s) => s.expression).find((e) => e && e.type === 'CallExpression' && e.callee.name === 'define'); const f = c.arguments[c.arguments.length - 1]; return text.slice(f.start, f.end); };
const canon = async (code) => (await T.minify(`__n(${code});`, { compress: false, mangle: true, format: { comments: false } })).code;
const unwrap = (c) => c.replace(/^__n\(/, '').replace(/\);?$/, '');
// terser releases are installed side by side as npm aliases (npm i t514@npm:terser@5.14.2 ...); see README.md
const versions = { 't505': '5.5.1', 't514': '5.14.2', 't519': '5.19.4', 't526': '5.26.0', 't531': '5.31.6', 't536': '5.36.0', 't539': '5.39.2', 't543': '5.43.1' };
const V = { 'terser-5.51.2': (c) => T.minify(`__n(${c});`, { compress: {}, mangle: false, format: { comments: false } }).then((r) => unwrap(r.code)),
  'uglify-js-3.19.3': async (c) => unwrap(U.minify(`__n(${c});`, { compress: {}, mangle: false, output: { comments: false } }).code) };
for (const [alias, v] of Object.entries(versions)) { let M; try { M = require(alias); } catch (e) { continue; } V['terser-' + v] = (c) => M.minify(`__n(${c});`, { compress: {}, mangle: false, format: { comments: false } }).then((r) => unwrap(r.code)); }
(async () => {
  let x = 7; const rnd = () => (x = (x * 1103515245 + 12345) % 2147483648) / 2147483648;
  const res = { n: 0 }; for (const k of Object.keys(V)) res[k] = 0;
  for (let i = 0; i < N; i++) {
    const r = eq[Math.floor(rnd() * eq.length)]; const d = defs.get(r.bundle + '|' + r.id);
    const bf = fac(src[r.bundle].slice(d.start, d.end)), rf = fac(fs.readFileSync(path.join(org, r.readable), 'utf8'));
    const want = await canon(bf); res.n++;
    for (const [k, f] of Object.entries(V)) { try { if ((await canon(await f(rf))) === want) res[k]++; } catch (e) { res[k + '-err'] = (res[k + '-err'] || 0) + 1; } }
  }
  fs.writeFileSync(outFile, JSON.stringify(res)); console.log(JSON.stringify(res));
})();
