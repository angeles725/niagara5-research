#!/usr/bin/env node
// B124 step 5: validity controls for the tiers of L.classify (b124_lib.js), which decide bundle_equiv.js.
//  baseline: the true pair must still classify as recorded;
//  negative: pair a bundle module with the readable factory of a DIFFERENT module -> tier must be null;
//  string mutation: change one character of a string literal in the readable factory -> tier must be null;
//  operator mutation: flip one operator -> null for the AST tiers (the skeleton tier cannot see it, measured).
// Usage: node bundle_controls.js ORGANIZED census.json equiv.json OUT.json [N=120]
const fs = require('fs'), path = require('path'), acorn = require('acorn');
const [org, censusFile, equivFile, outFile, nArg] = process.argv.slice(2); const N = +(nArg || 120);
const L = require('./b124_lib.js'); L.setOrg(org);
const census = JSON.parse(fs.readFileSync(censusFile, 'utf8')).bundles;
const eq = JSON.parse(fs.readFileSync(equivFile, 'utf8')).filter((r) => r.readable && r.bytes > 200 && r.tier);
const src = {}, defOf = new Map();
for (const b of census) { src[b.path] = fs.readFileSync(path.join(org, b.path), 'utf8'); for (const d of b.defs) defOf.set(b.path + '|' + d.id, d); }
const factory = (text) => { const c = acorn.parse(text, { ecmaVersion: 'latest' }).body.map((s) => s.expression).find((e) => e && e.type === 'CallExpression' && e.callee.name === 'define'); const f = c.arguments[c.arguments.length - 1]; return text.slice(f.start, f.end); };
const toks = (t) => [...acorn.tokenizer(t, { ecmaVersion: 'latest' })];
const mutString = (t) => { const s = toks(t).find((x) => x.type.label === 'string' && String(x.value).length >= 3 && x.value !== 'use strict'); return s && t.slice(0, s.start + 2) + (t[s.start + 2] === 'Z' ? 'Y' : 'Z') + t.slice(s.start + 3); };
const FLIP = { '===': '!==', '!==': '===', '||': '&&', '&&': '||', '<': '>', '+': '-' };
const mutOp = (t) => { const o = toks(t).find((x) => FLIP[x.type.label]); return o && t.slice(0, o.start) + FLIP[o.type.label] + t.slice(o.end); };

const AST = ['mangle', 'compress', 'uglify-expr'];   // a mutation must leave these tiers; for the skeleton pool it must leave every tier
(async () => {
  let x = 124; const rnd = () => (x = (x * 1103515245 + 12345) % 2147483648) / 2147483648;
  const groups = { ast: eq.filter((r) => r.tier !== 'skeleton'), skeleton: eq.filter((r) => r.tier === 'skeleton') };
  const res = {};
  for (const [g, pool] of Object.entries(groups)) {
    const r0 = res[g] = { pool: pool.length, n: 0, baselineOk: 0, negativeMatched: [], mutString: { tried: 0, detected: 0 }, mutOp: { tried: 0, detected: 0 } };
    for (let i = 0; i < N; i++) {
      const r = pool[Math.floor(rnd() * pool.length)], o = pool[Math.floor(rnd() * pool.length)];
      const d = defOf.get(r.bundle + '|' + r.id), bf = factory(src[r.bundle].slice(d.start, d.end));
      const rf = factory(fs.readFileSync(path.join(org, r.readable), 'utf8')), of = factory(fs.readFileSync(path.join(org, o.readable), 'utf8'));
      r0.n++;
      if ((await L.classify(rf, bf)).tier === r.tier) r0.baselineOk++;
      const gone = (c) => (g === 'ast' ? !AST.includes(c.tier) : !c.tier);
      if (r.readable !== o.readable && !gone(await L.classify(of, bf))) r0.negativeMatched.push(r.id + ' ~ ' + o.readable);
      const ms = mutString(rf), mo = mutOp(rf);
      if (ms) { r0.mutString.tried++; if (gone(await L.classify(ms, bf))) r0.mutString.detected++; }
      if (mo) { r0.mutOp.tried++; if (gone(await L.classify(mo, bf))) r0.mutOp.detected++; }
    }
  }
  fs.writeFileSync(outFile, JSON.stringify(res, null, 1)); console.log(JSON.stringify(res));
})();
