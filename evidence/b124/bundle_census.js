#!/usr/bin/env node
// B124 step 1: census of the *.built.min.js bundles under organized/<mod>/extracted/.
// Usage: node bundle_census.js ORGANIZED OUT.json   (needs `acorn`: npm i acorn; see README.md)
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const acorn = require('acorn');
const org = process.argv[2], out = process.argv[3];
const sha = (b) => crypto.createHash('sha256').update(b).digest('hex');

function findBundles(root) {
  const res = [];
  for (const mod of fs.readdirSync(root).sort()) {
    const rc = path.join(root, mod, 'extracted', 'rc');
    if (!fs.existsSync(rc)) continue;
    const walk = (d) => { for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, e.name);
      if (e.isDirectory()) walk(p); else if (e.name.endsWith('.built.min.js')) res.push({ module: mod, rel: path.relative(root, p) });
    } };
    walk(rc);
  }
  return res;
}

// Walk a node collecting define("id", ...) calls (terser hides them in sequences, if-tests, UMD wrappers);
// never descend into a define call itself (its factory is the module).
function findDefines(node, out) {
  if (!node || typeof node.type !== 'string') return out;
  if (node.type === 'CallExpression' && node.callee.name === 'define' && node.arguments[0] && node.arguments[0].type === 'Literal' && typeof node.arguments[0].value === 'string') { out.push(node); return out; }
  for (const k of Object.keys(node)) { const v = node[k]; if (Array.isArray(v)) v.forEach((c) => findDefines(c, out)); else if (v && typeof v.type === 'string') findDefines(v, out); }
  return out;
}

function analyse(src) {
  const ast = acorn.parse(src, { ecmaVersion: 'latest' });
  const defs = [], other = [], prelude = [];
  for (const st of ast.body) {
    if (st.type === 'FunctionDeclaration' || st.type === 'VariableDeclaration') { prelude.push({ start: st.start, end: st.end, name: st.id ? st.id.name : st.declarations.map((d) => d.id.name).join(',') }); continue; }
    const ds = findDefines(st, []);
    for (const n of ds) {
      const a = n.arguments, deps = a[1] && a[1].type === 'ArrayExpression' ? a[1] : null;
      defs.push({ id: a[0].value, deps: deps ? deps.elements.length : null, start: n.start, end: n.end, bytes: n.end - n.start, top: st.type === 'ExpressionStatement' && (st.expression === n || st.expression.type === 'SequenceExpression') });
    }
    const covered = ds.reduce((s, n) => s + n.end - n.start, 0);
    if (st.end - st.start - covered > 0) {
      // pieces = the sub-expressions of the statement that are not themselves define() calls
      const els = st.type === 'ExpressionStatement' && st.expression.type === 'SequenceExpression' ? st.expression.expressions : [st.type === 'ExpressionStatement' ? st.expression : st];
      const pieces = els.filter((n) => !ds.includes(n)).map((n) => ({ start: n.start, end: n.end, type: n.type }));
      other.push({ type: st.type, start: st.start, end: st.end, bytes: st.end - st.start - covered, pieces, head: src.slice(st.start, st.start + 100) });
    }
  }
  return { defs, other, prelude };
}

const rows = [];
for (const b of findBundles(org)) {
  const buf = fs.readFileSync(path.join(org, b.rel)); const src = buf.toString('utf8');
  const a = analyse(src);
  rows.push({ path: b.rel, module: b.module, bytes: buf.length, sha256: sha(buf), banner: src.slice(0, 160).replace(/\s+/g, ' '),
    sourceMappingURL: /sourceMappingURL/.test(src), newlines: (src.match(/\n/g) || []).length,
    modules: a.defs.length, nestedDefs: a.defs.filter((d) => !d.top).length, defBytes: a.defs.reduce((s, d) => s + d.bytes, 0),
    prelude: a.prelude, preludeBytes: a.prelude.reduce((t, p) => t + p.end - p.start, 0), other: a.other, otherBytes: a.other.reduce((t, o) => t + o.bytes, 0), defs: a.defs });
}
fs.writeFileSync(out, JSON.stringify({ bundles: rows }, null, 1));
console.log('bundles', rows.length, 'modules', rows.reduce((s, r) => s + r.modules, 0), 'bytes', rows.reduce((s, r) => s + r.bytes, 0));
console.log('nested defines', rows.reduce((s, r) => s + r.nestedDefs, 0), 'other bytes', rows.reduce((s, r) => s + r.otherBytes, 0), 'prelude bytes', rows.reduce((s, r) => s + r.preludeBytes, 0));
