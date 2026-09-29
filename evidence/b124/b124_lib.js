// Shared helpers for the B124 scripts: id -> readable path mapping, alias lookup, terser normalisation.
const fs = require('fs'), path = require('path'), T = require('terser'), U = require('uglify-js');
let org = null;
const setOrg = (o) => { org = o; };

// id -> candidate readable paths (relative to organized/) and kind
function candidates(id, bundleModule) {
  let kind = 'js', s = id;
  if (s.startsWith('hbs!')) { kind = 'hbs'; s = s.slice(4); }
  const ext = kind === 'hbs' ? ['.hbs'] : ['.js'];
  const out = [];
  let m;
  if ((m = s.match(/^nmodule\/([^/]+)\/(rc|ext)\/(.+)$/))) for (const e of ext) out.push(`${m[1]}/extracted/${m[2]}/${m[3]}${e}`);
  else if ((m = s.match(/^([^/]+)\/(.+)$/))) for (const e of ext) { out.push(`${m[1]}/extracted/rc/${m[2]}${e}`); out.push(`${bundleModule}/extracted/rc/${m[2]}${e}`); out.push(`${bundleModule}/extracted/rc/${s}${e}`); }
  else for (const e of ext) out.push(`${bundleModule}/extracted/rc/${s}${e}`);
  return { kind, out };
}

// Ids like "dialogs" / "bajaPromises" are r.js aliases: find the readable file that declares (or is named) that id.
const listCache = {};
function jsFiles(mod) {
  if (listCache[mod]) return listCache[mod];
  const res = [];
  const walk = (d) => { if (!fs.existsSync(d)) return; for (const e of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, e.name); if (e.isDirectory()) walk(p); else if (/\.js$/.test(e.name) && !/\.(built\.)?min\.js$/.test(e.name)) res.push(path.relative(org, p)); } };
  walk(path.join(org, mod, 'extracted'));
  return (listCache[mod] = res);
}
function aliasLookup(id, mod) {
  const base = id.split('/').pop();
  for (const m of [mod, 'js', 'bajaScript', 'bajaux']) {
    const files = jsFiles(m);
    const named = files.filter((f) => path.basename(f) === base + '.js');
    if (named.length === 1) return named[0];
    const esc = id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const decl = files.filter((f) => new RegExp(`define\\(\\s*['"]${esc}['"]`).test(fs.readFileSync(path.join(org, f), 'utf8')));
    if (decl.length === 1) return decl[0];
  }
  return null;
}

const normCache = new Map();
async function norm(code, mode) {
  const key = mode + '\0' + code;
  if (normCache.has(key)) return normCache.get(key);
  const v = await norm0(code, mode);
  normCache.set(key, v); return v;
}
async function norm0(code, mode) {
  // 'uglify' = a second, independent minifier: the bundles show UglifyJS-style output, see block 124 section 124.3
  if (mode === 'uglify' || mode === 'uglify-expr') { const r = U.minify(mode === 'uglify' ? code : `__n(${code});`, { compress: { passes: 2 }, mangle: true, output: { comments: false } }); if (r.error) throw r.error; return r.code; }
  const opt = mode === 'mangle' ? { compress: false, mangle: true } : { compress: { passes: 2 }, mangle: true };
  // 'stmt' = a top-level declaration/statement kept as is. Everything else is wrapped in a call: a bare
  // `(function(){...});` is side-effect free and compress would delete it, making every comparison vacuously equal
  // (a bug of this script's first version, caught by bundle_controls.js).
  const r = await T.minify(mode === 'stmt' ? code : `__n(${code});`, { ...opt, format: { comments: false } });
  return r.code;
}

// Weakest tier: the set of names and literals. Babel-machinery names (class helpers, descriptors) are dropped
// because the two Babel outputs express classes differently (`{key:"m",value:fn}` vs `C.prototype.m = fn`).
const NOISE = new Set(['key', 'value', 'prototype', 'constructor', 'writable', 'enumerable', 'configurable', 'get', 'set', 'default', '__proto__', 'length', 'call', 'apply', 'bind', 'create', 'defineProperty', 'setPrototypeOf', 'getPrototypeOf', 'name', 'arguments', 'object', 'function', 'undefined', 'symbol', 'string', 'number', 'boolean']);
async function skeleton(code) {
  const acorn = require('acorn');
  const folded = (await T.minify(`__n(${code});`, { compress: {}, mangle: false, format: { comments: false } })).code;
  const out = new Set(), order = [];
  (function walk(n) {
    if (!n || typeof n.type !== 'string') return;
    const add = (s) => { if (!out.has(s)) order.push(s); out.add(s); };   // `order` = first occurrences in source order
    // words of string literals (a folded or split concatenation keeps the words); numbers are ignored (constant folding rewrites them)
    if (n.type === 'Literal' && typeof n.value === 'string') for (const w of n.value.match(/[A-Za-z_$][A-Za-z0-9_$-]{2,}/g) || []) add(w);
    if (n.type === 'Property' && !n.computed && n.key.type === 'Identifier') add(n.key.name);
    if (n.type === 'MemberExpression' && !n.computed) add(n.property.name);
    for (const k of Object.keys(n)) { const v = n[k]; if (Array.isArray(v)) v.forEach(walk); else if (v && typeof v.type === 'string') walk(v); }
  })(acorn.parse(folded, { ecmaVersion: 'latest' }));
  for (const x of NOISE) out.delete(x);
  out.order = order.filter((x) => !NOISE.has(x));
  out.len = folded.length;   // length of the compressed code (the raw text carries comments, so it is no size measure)
  return out;
}
// Tiers, strongest first. 'mangle': terser without compress on both sides (only formatting + names differ);
// 'compress'/'uglify-expr': equal after the same terser / uglify-js normalisation; 'skeleton': same name/literal sets.
async function classify(rf, bf) {
  for (const mode of ['mangle', 'compress', 'uglify-expr']) if ((await norm(rf, mode)) === (await norm(bf, mode))) return { tier: mode };
  const [a, b] = [await skeleton(rf), await skeleton(bf)];
  const onlyR = [...a].filter((x) => !b.has(x)), onlyB = [...b].filter((x) => !a.has(x));
  const ratio = a.len / b.len;
  if (!onlyR.length && !onlyB.length && ratio > 0.4 && ratio < 3) return { tier: 'skeleton', ratio: +ratio.toFixed(2), ordered: JSON.stringify(a.order) === JSON.stringify(b.order) };
  return { tier: null, onlyReadable: onlyR.slice(0, 8), onlyBundle: onlyB.slice(0, 8), nOnlyR: onlyR.length, nOnlyB: onlyB.length, ratio: +ratio.toFixed(2) };
}

module.exports = { setOrg, candidates, aliasLookup, jsFiles, norm, classify, skeleton };
