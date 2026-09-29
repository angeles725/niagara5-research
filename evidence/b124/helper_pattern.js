#!/usr/bin/env node
// B124: does a minifier release rewrite the Babel `_typeof` helper the way the bundles show,
// `return(_typeof=<fn>)(o)`, rather than `return _typeof=<fn>,_typeof(o)`? One probe per installed release.
// Usage: node helper_pattern.js   (needs the terser aliases and uglify-js from README.md)
const src = 'function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }';
const want = '(_typeof=', out = [];
(async () => {
  const rel = { terser: 'terser', t481: 't481', t505: 't505', t561: 't561', t572: 't572', t590: 't590', t5100: 't5100', t5121: 't5121', t514: 't514', t519: 't519', t526: 't526', t531: 't531', t536: 't536', t539: 't539', t543: 't543' };
  // terser 4 returns the result directly, 5 a promise; await handles both
  for (const [k, m] of Object.entries(rel)) { let M; try { M = require(m); } catch (e) { continue; } const v = require(m + '/package.json').version;
    const c = (await M.minify(src, { compress: {}, mangle: false })).code; out.push(`terser ${v}: ${c.includes(want) ? 'COLLAPSED (f=..)(o)' : 'sequence  f=..,f(o)'}`); }
  const U = require('uglify-js'); out.push(`uglify-js ${require('uglify-js/package.json').version}: ${U.minify(src, { mangle: false }).code.includes(want) ? 'COLLAPSED (f=..)(o)' : 'sequence  f=..,f(o)'}`);
  console.log(out.join('\n'));
})();
