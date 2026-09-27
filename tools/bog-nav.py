#!/usr/bin/env python3
"""bog-nav: read-only navigator for a Niagara N4/N5 station config.bog (or a bare file.xml).

Used as-is from niagara-research (N4 kit tool): the BOG-XML grammar (component
nodes + b:Link records) is a Niagara-wide format, not an N4-only one, and this
tool takes the bog path as an explicit argument. Verified against a real N5
artifact — see tools/README.md for the `defaults/platform.bog` parse result.

WHY: the four session research tools (corpus-nav, module-navigator, niagara-help, hdbread)
navigate the CORPUS; this one navigates a live STATION's saved graph. A config.bog is a ZIP
whose file.xml is a BOG-XML tree of <p> component nodes (h='handle', t='pfx:Type') plus
<p t='b:Link'> link records that live on the TARGET component and point back at a source via
sourceOrd='h:xxxx'. Grep cannot resolve h:xxxx -> a component path, cannot walk the tree, and
cannot answer "which link feeds Cuarto1.setpoint?". This does.

Grammar + handle-graph parser REUSED from build-n4-module-kit/toolbelt/bog-audit.sh
(kit main 3f666a0): TAG_RE, ga(), the Comp class, prefix_map/handle_map/handle_count,
the link_list (container_h/src_h/src_slot/tgt_slot), stack, nearest_comp(). This tool adds
parent/child tracking for tree walks and the query subcommands; it never writes.

Subcommands:
  tree [--type PFX:Type] [--depth N]      component tree (optionally filtered by type)
  types [--slots] [--grep S]              histogram of component types (characterise an unknown bog)
  slot <path|h:handle> [slotName]         a component's value slots + child components
  find --type PFX:Type [--slots]          flat list of a type; --slots also finds handle-less value wrappers
  pointcache [--device N] [--stale]       Alerton Compass DisplayService PointCache: decode ORD + freshness
  links [--to P] [--from P] [--slot NAME] links, sourceOrd h:xxxx resolved to a path
  handle <h:xxxx>                         the component at a handle + its links
  writable [--module PFX]                 classify direct value slots by external writability
  grep <regex>                            regex over component paths, types, and slot names
  diff <bogB>                             component/slot/link delta vs another bog

Alerton Compass note: Compass is a DERIVED-but-distinct Niagara. Its point universe is NOT the
Tridium control:ControlPoint model -- it lives in the DisplayService PointCache (disp:PointCacheObj,
keyed by a bacref ORD) with the value as a handle-LESS `bac:*` wrapper. `pointcache` decodes it;
`find --slots` / `types --slots` stop those wrappers reading as a silent zero.

Read-only. Prints rows; pass --json for machine output. stdlib only. Python3 guard -> exit 3.
"""
import sys, os, re, json, csv, zipfile, argparse
from collections import defaultdict


def _render(rows, args, line_fn, empty='(none)', cols=None):
    """Shared output: --json (list of dicts), --csv (header+rows), else line_fn per row."""
    if getattr(args, 'json', False):
        print(json.dumps(rows, indent=2)); return
    if getattr(args, 'csv', False):
        if rows:
            keys = cols or list(rows[0].keys())
            w = csv.writer(sys.stdout); w.writerow(keys)
            for r in rows:
                w.writerow([r.get(k, '') for k in keys])
        return
    if not rows:
        print(empty); return
    for r in rows:
        print(line_fn(r))

# --- grammar (verbatim from bog-audit.sh D10 engine) ---
TAG_RE = re.compile(r'<(/?)([A-Za-z]\w*)\b([^>]*?)(/?)>')

def ga(text, name):
    """Get attribute value: single-quoted first, then double-quoted (bog mixes both)."""
    m = re.search(rf"\b{re.escape(name)}='([^']*)'", text)
    if m:
        return m.group(1)
    m = re.search(rf'\b{re.escape(name)}="([^"]*)"', text)
    return m.group(1) if m else None


class Comp:
    __slots__ = ('name', 'handle', 'type_', 'pfx', 'module', 'path',
                 'slots', 'actions', 'has_fallback', 'is_writable',
                 'parent_h', 'children', 'value_type', 'value_val')

    def __init__(self, name, handle, type_, pfx, module, path, parent_h):
        self.name = name
        self.handle = handle
        self.type_ = type_
        self.pfx = pfx
        self.module = module
        self.path = path
        self.slots = {}          # slot_name -> {type, value, flags}
        self.actions = {}        # action_name -> flags_str
        self.has_fallback = False
        self.parent_h = parent_h
        self.children = []       # child handles, in document order
        # the handle-LESS `value` child (e.g. <p n="value" t="bac:BacnetBinaryPv" v=".."/>):
        # a typed slot the type index would otherwise miss. Captured so `find --slots`,
        # `types --slots` and `pointcache` can see it (bog-nav bug fix 2026-09-18).
        self.value_type = None
        self.value_val = None
        _ts = type_.split(':')[-1] if ':' in type_ else type_
        self.is_writable = bool(re.match(r'(Boolean|Numeric|Float|Integer)Writable$', _ts))

    def simple_type(self):
        return self.type_.split(':')[-1] if ':' in self.type_ else self.type_


class Bog:
    """Parsed BOG graph: handle_map, link_list, prefix_map, roots."""
    def __init__(self, path, lines=None):
        self.src_path = path
        self.prefix_map = {}
        self.handle_map = {}
        self.handle_count = {}
        self.link_list = []
        self.roots = []          # top-level component handles
        self._parse(lines if lines is not None else _read_bog_xml(path))

    def _parse(self, text_lines):
        prefix_map = self.prefix_map
        handle_map = self.handle_map
        handle_count = self.handle_count
        link_list = self.link_list
        stack = []
        in_link = False
        link_buf = {}

        def nearest_comp():
            for fr in reversed(stack):
                if fr['type'] == 'comp':
                    return fr['comp']
            return None

        _PLATFORM_SLOTS = frozenset({'wsAnnotation', 'value', 'status', 'displayName'})

        for raw in text_lines:
            line = raw.rstrip()
            if not line.strip():
                continue
            for m in TAG_RE.finditer(line):
                is_closing = bool(m.group(1))
                tag_name = m.group(2)
                is_self_cls = bool(m.group(4)) or m.group(0).endswith('/>')
                full = m.group(0)

                if is_closing:
                    if tag_name in ('p', 'a') and stack:
                        popped = stack.pop()
                        if popped['type'] == 'link':
                            link_list.append(dict(link_buf))
                            in_link = False
                            link_buf = {}
                    continue

                if tag_name == 'a':  # action element
                    n = ga(full, 'n') or ''
                    f_ = ga(full, 'f') or ''
                    comp = nearest_comp()
                    if comp:
                        comp.actions[n] = f_
                    continue

                if tag_name != 'p':
                    continue

                n = ga(full, 'n') or ''
                h = ga(full, 'h')
                t = ga(full, 't') or ''
                v = ga(full, 'v')
                m_attr = ga(full, 'm') or ''
                f_attr = ga(full, 'f') or ''

                if m_attr:
                    for part in m_attr.split():
                        if '=' in part:
                            pk, mv = part.split('=', 1)
                            prefix_map[pk] = mv

                if in_link:
                    if is_self_cls:
                        if n == 'sourceOrd' and v and v.startswith('h:'):
                            link_buf['src_h'] = v[2:]
                        elif n == 'sourceOrd' and v:
                            link_buf['src_ord'] = v
                        elif n == 'sourceSlotName' and v:
                            link_buf['src_slot'] = v
                        elif n == 'targetSlotName' and v:
                            link_buf['tgt_slot'] = v
                    elif h is None:
                        parent = stack[-1] if stack else {}
                        stack.append({'type': 'other', 'handle': None,
                                      'path': parent.get('path', ''), 'comp': None})
                    continue

                if t == 'b:Link' and not is_self_cls:
                    comp = nearest_comp()
                    in_link = True
                    link_buf = {
                        'container_h': comp.handle if comp else None,
                        'container_path': comp.path if comp else '',
                        'link_name': n,
                        'src_h': None, 'src_ord': None,
                        'src_slot': None, 'tgt_slot': None,
                    }
                    parent = stack[-1] if stack else {}
                    stack.append({'type': 'link', 'handle': None,
                                  'path': parent.get('path', ''), 'comp': None})
                    continue

                if h is not None and not is_self_cls:
                    pfx = t.split(':')[0] if ':' in t else ''
                    module = prefix_map.get(pfx, '')
                    parent = stack[-1] if stack else None
                    parent_path = parent['path'] if parent else ''
                    parent_comp = nearest_comp()
                    parent_h = parent_comp.handle if parent_comp else None
                    path = (parent_path + '/' + n).lstrip('/')

                    handle_count[h] = handle_count.get(h, 0) + 1
                    comp = Comp(n, h, t, pfx, module, path, parent_h)
                    handle_map[h] = comp
                    if parent_h is None:
                        self.roots.append(h)
                    elif parent_h in handle_map:
                        handle_map[parent_h].children.append(h)
                    stack.append({'type': 'comp', 'handle': h, 'path': path, 'comp': comp})
                    continue

                if n == 'fallback':
                    comp = nearest_comp()
                    if comp:
                        comp.has_fallback = True
                    if not is_self_cls:
                        parent = stack[-1] if stack else {}
                        stack.append({'type': 'other', 'handle': None,
                                      'path': parent.get('path', '') + '/fallback',
                                      'comp': None})
                    continue

                if is_self_cls and (v is not None or f_attr):
                    _parent = stack[-1] if stack else None
                    if _parent and _parent['type'] == 'comp' and n not in _PLATFORM_SLOTS:
                        _parent['comp'].slots[n] = {'type': t, 'value': v, 'flags': f_attr}
                    elif _parent and _parent['type'] == 'comp' and n == 'value' and t:
                        # typed `value` wrapper (BACnet/Alerton: bac:BacnetBinaryPv, b:Float...).
                        # `value` is a platform slot excluded above, but for a leaf value node it
                        # IS the point payload; keep its type so the type index can find it.
                        _parent['comp'].value_type = t
                        _parent['comp'].value_val = v
                    elif (_parent and _parent['type'] == 'other'
                          and _parent.get('slot_owner') is not None and n in ('value', 'status')):
                        # nested struct child of a composite property (StatusNumeric.value):
                        # surface it on the owning slot — this is the shape a child-ORD write targets.
                        slot = _parent['slot_owner'].slots.get(_parent['slot_name'])
                        if slot is not None and v is not None:
                            slot['child'] = slot.get('child') or {}
                            slot['child'][n] = v
                            if n == 'value':
                                slot['value'] = v
                    continue

                # composite property (non-self-closing, no handle): e.g. setpoint StatusNumeric.
                # Record it as a value slot on the nearest comp so `slot`/`writable` see it, then
                # push an 'other' frame TAGGED with the owner so its nested <value>/<status> child
                # is captured (not dropped) by the branch above.
                if not is_self_cls and h is None:
                    _parent = stack[-1] if stack else None
                    owner = None
                    if _parent and _parent['type'] == 'comp' and n not in _PLATFORM_SLOTS:
                        _parent['comp'].slots[n] = {'type': t, 'value': None, 'flags': f_attr}
                        owner = _parent['comp']
                    parent = stack[-1] if stack else {}
                    ppath = parent.get('path', '')
                    stack.append({'type': 'other', 'handle': None,
                                  'path': (ppath + '/' + n).lstrip('/') if n else ppath,
                                  'comp': None, 'slot_owner': owner, 'slot_name': n})

    # ---- resolution helpers ----
    def resolve(self, ref):
        """path or h:handle -> Comp (or None)."""
        if ref.startswith('h:'):
            return self.handle_map.get(ref[2:])
        ref = ref.strip('/')
        for c in self.handle_map.values():
            if c.path == ref:
                return c
        # tolerate a leaf-name match if unambiguous
        hits = [c for c in self.handle_map.values() if c.path.endswith('/' + ref) or c.name == ref]
        return hits[0] if len(hits) == 1 else None

    def link_row(self, lk):
        src = self.handle_map.get(lk.get('src_h'))
        src_path = src.path if src else (lk.get('src_ord') or ('h:' + lk['src_h'] if lk.get('src_h') else '?'))
        return {
            'link': lk.get('link_name'),
            'source': f"{src_path}.{lk.get('src_slot')}",
            'target': f"{lk.get('container_path')}.{lk.get('tgt_slot')}",
            'src_resolved': src is not None,
        }


def _read_bog_xml(path):
    """Yield file.xml lines from a .bog (ZIP) or a bare .xml. Exit 3 on failure."""
    if not os.path.exists(path):
        sys.stderr.write(f'bog-nav: no such file: {path}\n')
        sys.exit(3)
    try:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
                name = 'file.xml' if 'file.xml' in names else next(
                    (n for n in names if n.endswith('file.xml')), None)
                if name:
                    data = z.read(name).decode('utf-8', errors='replace')
                else:
                    # a .dist station backup: config.bog is nested inside — read it as a ZIP
                    inner = next((n for n in names if n.endswith('config.bog')), None)
                    if not inner:
                        sys.stderr.write(f'bog-nav: no file.xml or config.bog inside {path}\n')
                        sys.exit(3)
                    import io as _io
                    with zipfile.ZipFile(_io.BytesIO(z.read(inner))) as zc:
                        cn = next((n for n in zc.namelist() if n.endswith('file.xml')), None)
                        if not cn:
                            sys.stderr.write(f'bog-nav: no file.xml inside {inner} of {path}\n')
                            sys.exit(3)
                        data = zc.read(cn).decode('utf-8', errors='replace')
        else:
            data = open(path, encoding='utf-8', errors='replace').read()
    except Exception as exc:
        sys.stderr.write(f'bog-nav: cannot read {path}: {exc}\n')
        sys.exit(3)
    return data.splitlines()


# ---- external-writability classifier (viewer record aa7054702 / B823 / B825) ----
# B-class/module simple form (…Numeric, b:Double) OR a whole-string Java primitive (double,int).
# The primitives are anchored ^…$ so a type like NumericPoint / constraint never false-matches.
_SIMPLE_WRITABLE = re.compile(
    r'(Boolean|Numeric|Float|Integer|Double|String|Enum|RelTime|AbsTime)$'
    r'|^(?:double|boolean|float|int|long|short|byte|char)$')

def source_types(root):
    """Best-effort {slotName: type} from a module Java source tree — for enriching bog value
    slots the bog stores WITHOUT a t= attr (frozen simples: type lives in @NiagaraProperty)."""
    m = {}
    if not root or not os.path.isdir(root):
        return m
    for cur, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fn in files:
            if not fn.endswith('.java'):
                continue
            try:
                lines = open(os.path.join(cur, fn), encoding='utf-8', errors='replace').read().split('\n')
            except Exception:
                continue
            i = 0
            while i < len(lines):
                if '@NiagaraProperty' not in lines[i]:
                    i += 1; continue
                buf = lines[i]; depth = lines[i].count('(') - lines[i].count(')'); j = i + 1
                while depth > 0 and j < len(lines):
                    buf += ' ' + lines[j]; depth += lines[j].count('(') - lines[j].count(')'); j += 1
                i = j
                nm = re.search(r'name\s*=\s*"([^"]+)"', buf)
                tm = re.search(r'type\s*=\s*"([^"]+)"', buf)
                if nm and tm and nm.group(1) not in m:
                    m[nm.group(1)] = tm.group(1)
    return m


def type_display(slot_type, slot_name, src_types):
    """Display string for a slot type, filling a bog-absent type from source when available."""
    if slot_type:
        return slot_type
    if src_types and slot_name in src_types:
        return f'{src_types[slot_name]} (from source)'
    return 'frozen simple (type in source)'


def writability(slot_type, slot_name):
    """Classify a direct value slot's external write shape. See B823 §823.2, viewer record.
    Returns (klass, note)."""
    t = slot_type.split(':')[-1] if slot_type and ':' in slot_type else (slot_type or '')
    if t.startswith('Status'):
        # a complex property: writable via its child leaf (bare <real>), or the wrapped-obj
        # parent PUT (silent-zero hazard). [CERT-live] B826-G2 / viewer record.
        return ('complex', 'child-leaf ORD bare <real> preferred; parent wrapped-obj = silent-zero hazard')
    if not t:
        return ('bare', 'no type attr (untyped value/mode slot)')
    if _SIMPLE_WRITABLE.search(t):
        return ('simple', 'plain simple value; carries writable="true" externally')
    return ('other', t)


# ================================================================
# subcommands
# ================================================================
def cmd_tree(bog, args):
    want_type = args.type
    rows = []

    def walk(h, depth):
        c = bog.handle_map[h]
        if args.depth is None or depth <= args.depth:
            if not want_type or c.type_ == want_type or c.simple_type() == want_type.split(':')[-1]:
                rows.append({'depth': depth, 'handle': h, 'name': c.name,
                             'type': c.type_, 'path': c.path})
        if args.depth is None or depth < args.depth:
            for ch in c.children:
                walk(ch, depth + 1)
        elif want_type:
            for ch in c.children:  # keep descending to find deeper matches when filtering
                walk(ch, depth + 1)

    for r in bog.roots:
        walk(r, 0)
    if args.json:
        print(json.dumps(rows, indent=2))
        return
    for r in rows:
        indent = '  ' * r['depth']
        print(f"h:{r['handle']:<8} {indent}{r['name']}  <{r['type']}>")


def cmd_slot(bog, args):
    src_types = source_types(getattr(args, 'src', None))
    c = bog.resolve(args.ref)
    if not c:
        sys.stderr.write(f'bog-nav: cannot resolve {args.ref}\n')
        sys.exit(1)
    if args.slotname:
        s = c.slots.get(args.slotname)
        out = {'path': c.path, 'slot': args.slotname, **(s or {})}
        if args.json:
            print(json.dumps(out, indent=2))
        elif s:
            eff = s.get('type') or (src_types.get(args.slotname, '') if src_types else '')
            k, note = writability(eff, args.slotname)
            child = ('  child={' + ', '.join(f'{kk}={vv}' for kk, vv in s['child'].items()) + '}'
                     ) if s.get('child') else ''
            print(f"{c.path}.{args.slotname}  type={type_display(s.get('type'), args.slotname, src_types)}  "
                  f"value={s.get('value')}{child}  flags={s.get('flags')}  write={k} [{note}]")
        else:
            print(f"{c.path}: no direct slot '{args.slotname}' "
                  f"(children: {', '.join(bog.handle_map[ch].name for ch in c.children) or 'none'})")
        return
    out = {'path': c.path, 'handle': c.handle, 'type': c.type_,
           'slots': c.slots, 'actions': c.actions,
           'children': [{'name': bog.handle_map[ch].name, 'handle': ch,
                         'type': bog.handle_map[ch].type_} for ch in c.children]}
    if args.json:
        print(json.dumps(out, indent=2))
        return
    print(f"{c.path}  h:{c.handle}  <{c.type_}>")
    for sn, s in c.slots.items():
        eff = s.get('type') or (src_types.get(sn, '') if src_types else '')
        k, _ = writability(eff, sn)
        child = ('  child={' + ', '.join(f'{kk}={vv}' for kk, vv in s['child'].items()) + '}'
                 ) if s.get('child') else ''
        print(f"  slot  {sn} = {s.get('value')}{child}  "
              f"<{type_display(s.get('type'), sn, src_types)}>  f={s.get('flags')}  [{k}]")
    for an, f in c.actions.items():
        print(f"  action  {an}  f={f}")
    for ch in c.children:
        cc = bog.handle_map[ch]
        print(f"  child  {cc.name}  h:{ch}  <{cc.type_}>")


def cmd_links(bog, args):
    dangling_names = _source_slot_names(args.src) if getattr(args, 'src', None) else None
    rows = []
    for lk in bog.link_list:
        row = bog.link_row(lk)
        if args.to and not _match_ref(lk.get('container_h'), lk.get('container_path'), lk.get('tgt_slot'), args.to):
            continue
        if not _slot_filter(lk, args):
            continue
        if args.from_:
            src = bog.handle_map.get(lk.get('src_h'))
            src_path = src.path if src else ''
            if not _match_ref(lk.get('src_h'), src_path, lk.get('src_slot'), args.from_):
                continue
        # CHECK7: a link whose targetSlotName is not any source slot name (needs --src).
        # Restricted to OWN-module target containers (bog-audit CHECK7) — a kitControl/driver
        # target's slots are not in the module source we scanned, so it is not our dangle.
        cont = bog.handle_map.get(lk.get('container_h'))
        is_dangling = bool(dangling_names is not None and lk.get('tgt_slot')
                           and cont and cont.module in OWN_MODULES
                           and lk.get('tgt_slot') not in dangling_names)
        if args.dangling and not is_dangling:
            continue
        row['dangling'] = is_dangling
        rows.append(row)
    _render(rows, args,
            lambda r: (f"{r['source']}  -->  {r['target']}"
                       + ('  [orphan sourceOrd]' if not r['src_resolved'] else '')
                       + ('  [DANGLING tgt]' if r.get('dangling') else '')),
            empty='(no matching links)')


def _slot_filter(lk, args):
    """--slot semantics (endpoint-aware since 2026-09-06): with --from it names the SOURCE
    slot, with --to the TARGET slot, with neither (or with --slot-any) it matches either end.
    Rationale: `links --from Cuarto1 --slot fanMode` used to return Cuarto1.evap3FanMode -->
    EvaporatorUnit_1.fanMode because the TARGET end is named fanMode -- exact, but the wrong
    endpoint for the question "does Cuarto1.fanMode link out?"."""
    slot = getattr(args, 'slot', None)
    if not slot:
        return True
    src_ok = lk.get('src_slot') == slot
    tgt_ok = lk.get('tgt_slot') == slot
    from_, to = getattr(args, 'from_', None), getattr(args, 'to', None)
    if getattr(args, 'slot_any', False) or not (from_ or to) or (from_ and to):
        return src_ok or tgt_ok
    return src_ok if from_ else tgt_ok


def _match_path(path, slot, needle):
    needle = needle.strip('/')
    if path == needle or (path or '').endswith('/' + needle):
        return True
    full = f"{path}.{slot}"
    return needle in full


def _match_ref(comp_h, path, slot, needle):
    """Match a --to/--from needle against ONE link endpoint.
    A handle needle (h:xxxx) matches that endpoint component's handle EXACTLY;
    any other needle falls back to path/slot matching (_match_path). Without this,
    `links --to h:1d204` / `--from h:5b006` compared the handle string against paths
    and silently returned nothing (false negative) even when the link existed."""
    if needle.startswith('h:'):
        return comp_h == needle[2:]
    return _match_path(path, slot, needle)


def cmd_handle(bog, args):
    h = args.handle[2:] if args.handle.startswith('h:') else args.handle
    c = bog.handle_map.get(h)
    if not c:
        print(f'h:{h}: no such handle'
              + (f" (appears {bog.handle_count.get(h)}x)" if h in bog.handle_count else ''))
        sys.exit(1)
    fed_by = [bog.link_row(lk) for lk in bog.link_list if lk.get('container_h') == h]
    feeds = [bog.link_row(lk) for lk in bog.link_list if lk.get('src_h') == h]
    if args.json:
        print(json.dumps({'path': c.path, 'type': c.type_,
                          'fed_by': fed_by, 'feeds': feeds}, indent=2))
        return
    print(f"h:{h}  {c.path}  <{c.type_}>  parent=h:{c.parent_h}")
    for r in fed_by:
        print(f"  fed-by   {r['source']}  -->  {r['target']}")
    for r in feeds:
        print(f"  feeds    {r['source']}  -->  {r['target']}")


def cmd_writable(bog, args):
    src_types = source_types(getattr(args, 'src', None))
    rows = []
    for c in bog.handle_map.values():
        if args.module and c.pfx != args.module and c.module != args.module:
            continue
        for sn, s in c.slots.items():
            eff = s.get('type') or (src_types.get(sn, '') if src_types else '')
            k, note = writability(eff, sn)
            if args.klass and k != args.klass:
                continue
            rows.append({'path': c.path, 'slot': sn,
                         'type': type_display(s.get('type'), sn, src_types),
                         'value': s.get('value'), 'class': k, 'note': note})
    _render(rows, args,
            lambda r: (f"{r['class']:<8} {r['path']}.{r['slot']}"
                       + (f"={r['value']}" if r['value'] is not None else '')
                       + f"  <{r['type']}>  {r['note']}"),
            empty='(no slots matched)')


def cmd_grep(bog, args):
    rx = re.compile(args.regex, re.I)
    rows = []
    for c in bog.handle_map.values():
        if rx.search(c.path) or rx.search(c.type_):
            rows.append({'kind': 'comp', 'path': c.path, 'type': c.type_, 'handle': c.handle})
        for sn in c.slots:
            if rx.search(sn):
                rows.append({'kind': 'slot', 'path': f'{c.path}.{sn}',
                             'type': c.slots[sn].get('type'), 'handle': c.handle})
    _render(rows, args, lambda r: f"{r['kind']:<5} h:{r['handle']:<8} {r['path']}  <{r['type'] or ''}>",
            empty='(no matches)')


def cmd_diff(bog, args):
    other = Bog(args.bogB)
    a_paths = {c.path: c for c in bog.handle_map.values()}
    b_paths = {c.path: c for c in other.handle_map.values()}
    added = sorted(set(b_paths) - set(a_paths))
    removed = sorted(set(a_paths) - set(b_paths))
    changed = []
    for p in sorted(set(a_paths) & set(b_paths)):
        sa, sb = a_paths[p].slots, b_paths[p].slots
        for sn in sorted(set(sa) | set(sb)):
            va = (sa.get(sn) or {}).get('value')
            vb = (sb.get(sn) or {}).get('value')
            if va != vb:
                changed.append({'path': f'{p}.{sn}', 'a': va, 'b': vb})
    if args.json:
        print(json.dumps({'added': added, 'removed': removed, 'changed': changed}, indent=2))
        return
    for p in added:
        print(f"+ {p}  <{b_paths[p].type_}>")
    for p in removed:
        print(f"- {p}  <{a_paths[p].type_}>")
    for r in changed:
        print(f"~ {r['path']}  {r['a']} -> {r['b']}")
    if not (added or removed or changed):
        print('(identical component/slot sets)')


# synthetic bog exercising: tree, composite property (StatusNumeric.value child), simple slot,
# module prefix, cross-component link resolution, a CROSSED tile (evap1 <- unit 3), an own-module
# relay into a writable with/without fallback, and an auto mode slot.
_SELFTEST_XML = """<?xml version='1.0' encoding='UTF-8'?>
<bajaObjectGraph version='4.0'>
 <p n='Station' h='1' t='b:Station' m='b=baja CRP=ColdRoomPan DPCD=DashboardPan c=control'>
  <p n='Panel' h='10' t='DPCD:RoomPanel'>
   <p n='setpoint' t='b:StatusNumeric'>
    <p n="value" v="3.0"/>
   </p>
   <p n="differentialUp" v="1.5"/>
   <p n='Link' t='b:Link'>
    <p n="sourceOrd" v="h:30"/>
    <p n="sourceSlotName" v="valveOut"/>
    <p n="targetSlotName" v="evap1ValveState"/>
   </p>
  </p>
  <p n='Logic' h='20' t='CRP:ColdRoom'>
   <p n='setpoint' t='b:StatusNumeric'>
    <p n="value" v="3.0"/>
   </p>
   <p n="valveMode" v="auto"/>
   <p n='EvaporatorUnit_3' h='30' t='CRP:EvaporatorUnit'>
    <p n='valveOut' t='b:StatusBoolean'>
     <p n="value" v="false"/>
    </p>
   </p>
   <p n='Link' t='b:Link'>
    <p n="sourceOrd" v="h:10"/>
    <p n="sourceSlotName" v="setpoint"/>
    <p n="targetSlotName" v="setpoint"/>
   </p>
   <p n='Link1' t='b:Link'>
    <p n="sourceOrd" v="h:10"/>
    <p n="sourceSlotName" v="evap1FanMode"/>
    <p n="targetSlotName" v="fanMode"/>
   </p>
  </p>
  <p n='Drivers' h='40' t='c:BooleanWritable'>
   <p n='ro1' h='41' t='c:BooleanWritable'>
    <p n='fallback' t='b:StatusBoolean'>
     <p n="value" v="false"/>
    </p>
    <p n='Link' t='b:Link'>
     <p n="sourceOrd" v="h:30"/>
     <p n="sourceSlotName" v="valveOut"/>
     <p n="targetSlotName" v="in10"/>
    </p>
   </p>
   <p n='ro2' h='42' t='c:BooleanWritable'>
    <p n='Link' t='b:Link'>
     <p n="sourceOrd" v="h:30"/>
     <p n="sourceSlotName" v="valveOut"/>
     <p n="targetSlotName" v="in10"/>
    </p>
   </p>
  </p>
  <p n='DisplayService' h='50' t='disp:BtDisplayService' m='disp=btsDisp bac=bacnet'>
   <p n='pointCache' h='51' t='disp:PointCache'>
    <p n='bts$3abacref$3adopr$3d5_100_85_8_101' h='52' t='disp:PointCacheObj'>
     <p n="value" m="bac=bacnet" t="bac:BacnetBinaryPv" v="inactive"/>
     <p n="polledTime" t="b:AbsTime" v="2022-04-18T12:12:54.046-05:00"/>
    </p>
    <p n='bts$3abacref$3adopr$3d2_50_85_8_101' h='53' t='disp:PointCacheObj'>
     <p n="value" t="b:Float" v="72.5"/>
     <p n="polledTime" t="b:AbsTime" v="2026-09-03T00:00:00.000-05:00"/>
    </p>
   </p>
  </p>
 </p>
</bajaObjectGraph>""".splitlines()


def cmd_selftest(bog_ignored, args):
    b = Bog('<selftest>', lines=_SELFTEST_XML)
    fails = []

    def check(cond, label):
        (print(f'  ok   {label}') if cond else fails.append(label))
        if not cond:
            print(f'  FAIL {label}')

    check(set(b.handle_map) == {'1', '10', '20', '30', '40', '41', '42', '50', '51', '52', '53'},
          'all handled components parsed')
    check(b.handle_map['10'].path == 'Station/Panel', 'path built from tree (Station/Panel)')
    check(b.handle_map['20'].parent_h == '1', 'parent handle tracked')
    check(b.handle_map['30'].parent_h == '20', 'nested EvaporatorUnit parent handle tracked')
    check('setpoint' in b.handle_map['10'].slots, 'composite property recorded as slot')
    check(b.handle_map['10'].slots['setpoint']['type'] == 'b:StatusNumeric', 'composite slot type')
    check(b.handle_map['10'].slots['setpoint'].get('value') == '3.0',
          'nested StatusNumeric.value child surfaced on the slot (not None)')
    check((b.handle_map['10'].slots['setpoint'].get('child') or {}).get('value') == '3.0',
          'nested child dict captured (the child-ORD write target)')
    check(type_display('', 'differentialUp', {'differentialUp': 'double'}) == 'double (from source)',
          '--src fills a bog-absent type from source')
    check(type_display('', 'x', {}) == 'frozen simple (type in source)',
          'bog-absent type without --src labelled frozen simple (not untyped)')
    check(b.handle_map['10'].slots['differentialUp']['value'] == '1.5', 'simple slot value')
    check(b.prefix_map.get('CRP') == 'ColdRoomPan', 'module prefix decl parsed')
    # link resolution: Panel.setpoint feeds Logic.setpoint
    logic_links = [b.link_row(lk) for lk in b.link_list if lk.get('container_h') == '20' and lk.get('tgt_slot') == 'setpoint']
    check(len(logic_links) == 1 and logic_links[0]['source'] == 'Station/Panel.setpoint'
          and logic_links[0]['target'] == 'Station/Logic.setpoint'
          and logic_links[0]['src_resolved'],
          'cross-component link sourceOrd h:10 resolved to a path')
    # regression: --to/--from accept an h:handle, not only a path (false-negative fixed 2026-09-10)
    check(_match_ref('20', 'Station/Logic', 'setpoint', 'h:20')
          and not _match_ref('20', 'Station/Logic', 'setpoint', 'h:99')
          and _match_ref('10', 'Station/Panel', 'setpoint', 'h:10'),
          '--to/--from match an endpoint by h:handle exactly')
    check(_match_ref('20', 'Station/Logic', 'setpoint', 'Logic')
          and _match_ref('10', 'Station/Panel', 'setpoint', 'Panel'),
          '--to/--from still match by path when the needle is not a handle')
    # --slot is endpoint-aware: Panel.evap1FanMode --> Logic.fanMode must NOT answer
    # "does Panel.fanMode link out?" (--from Panel --slot fanMode), but must answer
    # --from Panel --slot evap1FanMode, --to Logic --slot fanMode, and --slot fanMode alone.
    from types import SimpleNamespace as _NS
    fan = [lk for lk in b.link_list if lk.get('tgt_slot') == 'fanMode']
    check(len(fan) == 1 and not _slot_filter(fan[0], _NS(slot='fanMode', from_='Panel', to=None)),
          '--from X --slot S filters the SOURCE slot (target named S is not a hit)')
    check(_slot_filter(fan[0], _NS(slot='evap1FanMode', from_='Panel', to=None))
          and _slot_filter(fan[0], _NS(slot='fanMode', from_=None, to='Logic'))
          and _slot_filter(fan[0], _NS(slot='fanMode', from_=None, to=None)),
          '--slot matches the source end with --from, the target end with --to, either end alone')
    check(_slot_filter(fan[0], _NS(slot='fanMode', from_='Panel', to=None, slot_any=True)),
          '--slot-any restores either-end matching')
    k, _ = writability('b:StatusNumeric', 'setpoint')
    check(k == 'complex', 'StatusNumeric classified as complex (child-leaf write)')
    k2, _ = writability('b:Double', 'differentialUp')
    check(k2 == 'simple', 'plain b:Double classified simple')
    check(writability('double', 'x')[0] == 'simple', 'lowercase Java primitive double classified simple')
    check(writability('NumericPoint', 'x')[0] == 'other', 'NumericPoint not false-matched as simple')
    k3, _ = writability('', 'someMode')
    check(k3 == 'bare', 'untyped value slot classified bare')

    # new-command pins — run each command end-to-end and assert the fact it must report
    import io, contextlib

    def run(fn, **kw):
        ns = argparse.Namespace(json=False, csv=False, module=None, src=None, all=False, **kw)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            fn(b, ns)
        return buf.getvalue()

    check(b.handle_map['41'].has_fallback and not b.handle_map['42'].has_fallback,
          'relay data: ro1 has a fallback, ro2 has none (CHECK11 view)')
    check('2 own-module->writable relay targets; 1 WITHOUT' in run(cmd_relays),
          'relays: 2 targets, 1 without fallback')
    check('CROSSED' in run(cmd_tiles) and 'evap1' in run(cmd_tiles),
          'tiles: evap1 tile flagged CROSSED (fed by EvaporatorUnit_3)')
    check('0 active priority-array override' in run(cmd_hoa),
          'hoa: 0 active overrides, mode slot auto (CHECK8)')
    check(run(cmd_path, handle='h:30').strip() == 'Station/Logic/EvaporatorUnit_3',
          'path: handle -> path reverse lookup')
    check('Station/Panel' in run(cmd_find, type='DPCD:RoomPanel'),
          'find: flat list by type')

    # --- bug-fix + new-command pins (2026-09-18): handle-less typed slots, types, pointcache ---
    check(b.handle_map['52'].value_type == 'bac:BacnetBinaryPv',
          'handle-less `value` wrapper type captured on the PointCacheObj (the bug fix)')
    # the silent-zero: bac:BacnetBinaryPv is ONLY a value wrapper; plain find must NOT print a bare zero
    out_noslots = run(cmd_find, type='bac:BacnetBinaryPv', slots=False)
    check('handle-less slot' in out_noslots and 'rerun with --slots' in out_noslots,
          'find: bac:BacnetBinaryPv with no --slots warns instead of a silent zero')
    check('Station/DisplayService/pointCache' in run(cmd_find, type='bac:BacnetBinaryPv', slots=True),
          'find --slots: the handle-less bac:BacnetBinaryPv value wrapper is now listed')
    types_out = run(cmd_types, slots=True, type_filter=None)
    check('disp:PointCacheObj' in types_out and 'bac:BacnetBinaryPv' in types_out,
          'types --slots: component types AND handle-less slot types counted')
    pc_out = run(cmd_pointcache, device=None, stale=False, live=False, stale_before=None, summary=False)
    check('binary-value:100@dev101' in pc_out and 'present-value' in pc_out,
          'pointcache: bacref dopr ORD decoded to obj-type:inst@dev + property name')
    check('STALE' in pc_out and 'live' in pc_out,
          'pointcache: freshness classified (2022 STALE vs 2026 live)')
    pc_stale = run(cmd_pointcache, device='101', stale=True, live=False, stale_before=None, summary=False)
    check('2022-04-18' in pc_stale and '2026-09-03' not in pc_stale,
          'pointcache --stale --device: filters to the dead binding only')
    if fails:
        print(f'\nSELFTEST FAILED: {len(fails)} check(s)')
        sys.exit(1)
    print('\nSELFTEST OK')


OWN_MODULES = frozenset({'ColdRoomPan', 'DashboardPan', 'CompPan'})


def _source_slot_names(root):
    """Global set of slot names declared by @NiagaraProperty across a src tree (for --dangling)."""
    return set(source_types(root).keys())


def cmd_relays(bog, args):
    """CHECK11 view: own-module output linked into a writable proxy point, fallback + writeOnUp.
    A writable with an own-module source and NO explicit fallback HOLDS its last state on a
    stop/reload (B810) — the relay stays energized. writeOnUp is absent from the bog (defaults
    true, so a device-DOWN self-corrects) unless persisted."""
    rows = []
    for lk in bog.link_list:
        src = bog.handle_map.get(lk.get('src_h'))
        cont = bog.handle_map.get(lk.get('container_h'))
        if not (src and cont and cont.is_writable):
            continue
        if args.module and src.module != args.module and src.pfx != args.module:
            continue
        if not args.module and src.module not in OWN_MODULES:
            continue
        won = cont.slots.get('writeOnUp', {}).get('value')
        rows.append({'target': cont.path, 'type': cont.simple_type(),
                     'source': f"{src.path}.{lk.get('src_slot')}",
                     'fallback': 'yes' if cont.has_fallback else 'NO',
                     'writeOnUp': won if won is not None else 'default(true)'})
    rows.sort(key=lambda r: (r['fallback'] != 'NO', r['target']))
    no_fb = sum(1 for r in rows if r['fallback'] == 'NO')
    _render(rows, args,
            lambda r: f"{r['fallback']:<3} fb  {r['target']}  <{r['type']}>  <- {r['source']}  writeOnUp={r['writeOnUp']}",
            empty='(no own-module relays)')
    if not (getattr(args, 'json', False) or getattr(args, 'csv', False)):
        print(f"# {len(rows)} own-module->writable relay targets; {no_fb} WITHOUT a fallback "
              f"(hold last state on stop/reload — B810)")


def cmd_hoa(bog, args):
    """CHECK8 view: every HOA/mode slot with its persisted value; flag non-auto leftovers.
    Defaults to OWN modules (RoomPanel *Mode slots are TRANSIENT, absent from the bog; the
    persisted mode slots live on the CRP logic). --all also scans driver writables' priority
    arrays. States: AUTO (null), config (a persisted mode enum, e.g. fanRunMode=runOnDelay),
    OVERRIDE (in1..in8 priority-array value — the CHECK8 leftover)."""
    rows = []
    overrides = auto = config = 0
    for c in bog.handle_map.values():
        own = c.module in OWN_MODULES
        if args.module:
            if c.pfx != args.module and c.module != args.module:
                continue
        elif not (own or args.all):
            continue
        for sn, s in c.slots.items():
            is_prio = bool(re.match(r'in[1-8]$', sn))
            if not (sn.endswith('Mode') or is_prio):
                continue
            v = s.get('value')
            has_val = (v or '').lower() not in ('', 'false', '0', 'null')
            if is_prio and has_val:
                state = 'OVERRIDE'; overrides += 1
            elif has_val:
                state = 'config'; config += 1
            else:
                state = 'AUTO'; auto += 1
            rows.append({'slot': f'{c.path}.{sn}', 'value': v if v is not None else '(auto/null)',
                         'state': state})
    rows.sort(key=lambda r: ({'OVERRIDE': 0, 'config': 1, 'AUTO': 2}[r['state']], r['slot']))
    _render(rows, args, lambda r: f"{r['state']:<8} {r['slot']} = {r['value']}", empty='(no HOA/mode slots)')
    if not (getattr(args, 'json', False) or getattr(args, 'csv', False)):
        print(f"# {len(rows)} HOA/mode slots; {auto} AUTO/null; {config} persisted config-mode; "
              f"{overrides} active priority-array override(s) [CHECK8]")


def cmd_tiles(bog, args):
    """CHECK18 view: per RoomPanel, the evapN dashboard tile -> EvaporatorUnit_M wiring, flagging
    a CROSSED tile (dashboard tile number != physical unit number, e.g. Cuarto1 units 1/3)."""
    rows = []
    rp = sorted((c for c in bog.handle_map.values() if c.simple_type() == 'RoomPanel'),
                key=lambda c: c.path)
    for room in rp:
        for lk in bog.link_list:
            if lk.get('container_h') != room.handle:
                continue
            tgt = lk.get('tgt_slot') or ''
            m = re.match(r'evap(\d+)(ValveState|FanState)$', tgt)
            if not m:
                continue
            src = bog.handle_map.get(lk.get('src_h'))
            um = re.search(r'EvaporatorUnit_?(\d+)?$', src.path if src else '')
            unit = um.group(1) if (um and um.group(1)) else '1'
            tile = m.group(1)
            rows.append({'room': room.name, 'tile': f'evap{tile}{m.group(2)}',
                         'unit': src.path.split('/')[-1] if src else '?',
                         'crossed': 'CROSSED' if tile != unit else 'ok'})
    rows.sort(key=lambda r: (r['room'], r['tile']))
    _render(rows, args, lambda r: f"{r['crossed']:<7} {r['room']}.{r['tile']}  <- {r['unit']}",
            empty='(no RoomPanel tiles)')
    if not (getattr(args, 'json', False) or getattr(args, 'csv', False)):
        crossed = sum(1 for r in rows if r['crossed'] == 'CROSSED')
        print(f"# {len(rows)} tile links; {crossed} CROSSED (tile number != unit number)")


def cmd_path(bog, args):
    h = args.handle[2:] if args.handle.startswith('h:') else args.handle
    c = bog.handle_map.get(h)
    if not c:
        print(f'h:{h}: no such handle'); sys.exit(1)
    if getattr(args, 'json', False):
        print(json.dumps({'handle': h, 'path': c.path, 'type': c.type_})); return
    print(c.path)


def _type_matcher(want):
    """A predicate that matches PFX:Type exactly OR by the bare trailing Type name."""
    simple = want.split(':')[-1]
    def is_t(tp):
        if not tp:
            return False
        return tp == want or (tp.split(':')[-1] if ':' in tp else tp) == simple
    return is_t


def _slot_type_hits(bog, is_t):
    """Yield (comp, slot_path, slot_type) for every handle-LESS typed slot matching is_t:
    the `value` wrapper AND any other recorded value slot. This is what the flat handle
    index alone cannot see (the bog-nav silent-zero bug this fixes)."""
    for c in bog.handle_map.values():
        if c.value_type and is_t(c.value_type):
            yield c, c.path + '.value', c.value_type
        for sn, sl in c.slots.items():
            if is_t(sl.get('type', '')):
                yield c, c.path + '.' + sn, sl['type']


def cmd_find(bog, args):
    want = args.type
    is_t = _type_matcher(want)
    rows = [{'handle': c.handle, 'path': c.path, 'type': c.type_, 'kind': 'component'}
            for c in sorted(bog.handle_map.values(), key=lambda c: c.path)
            if is_t(c.type_)]
    include_slots = getattr(args, 'slots', False)
    if include_slots:
        slot_rows = [{'handle': c.handle, 'path': p, 'type': t, 'kind': 'slot'}
                     for c, p, t in _slot_type_hits(bog, is_t)]
        rows += sorted(slot_rows, key=lambda r: r['path'])
    if not rows and not include_slots:
        # silent-zero guard: a type that lives only as a handle-less slot (e.g. bac:BacnetBinaryPv)
        # used to return a bare "(no components)" and mislead. Say the slots are there instead.
        hidden = sum(1 for _ in _slot_type_hits(bog, is_t))
        if hidden:
            print(f'(no COMPONENTS of type {want}, but {hidden} handle-less slot(s) of it exist '
                  f'-- rerun with --slots to list them)')
            return
    _render(rows, args,
            lambda r: f"h:{r['handle']:<8} {r['path']}  <{r['type']}>  [{r['kind']}]",
            empty=f'(no components or slots of type {want})',
            cols=['handle', 'path', 'type', 'kind'])


def cmd_types(bog, args):
    """Histogram of component types -- characterises an unknown bog in one call.
    --slots also counts handle-less typed slots (value wrappers etc.)."""
    from collections import Counter
    comp = Counter(c.type_ for c in bog.handle_map.values())
    rows = [{'count': n, 'type': t, 'kind': 'component'} for t, n in comp.most_common()]
    if getattr(args, 'slots', False):
        slot = Counter()
        for c in bog.handle_map.values():
            if c.value_type:
                slot[c.value_type] += 1
            for sl in c.slots.values():
                if sl.get('type'):
                    slot[sl['type']] += 1
        rows += [{'count': n, 'type': t, 'kind': 'slot'} for t, n in slot.most_common()]
    grep = getattr(args, 'type_filter', None)
    if grep:
        rows = [r for r in rows if grep.lower() in r['type'].lower()]
    _render(rows, args, lambda r: f"{r['count']:8}  {r['type']:34} [{r['kind']}]",
            empty='(no components)', cols=['count', 'type', 'kind'])


# BACnet enum decode -- the small subset that appears in Alerton PointCache ORDs.
BACNET_OBJTYPE = {'0': 'analog-input', '1': 'analog-output', '2': 'analog-value',
                  '3': 'binary-input', '4': 'binary-output', '5': 'binary-value',
                  '8': 'device', '10': 'file', '13': 'multistate-input',
                  '14': 'multistate-output', '19': 'multistate-value', '20': 'trend-log'}
BACNET_PROP = {'28': 'description', '36': 'event-state', '70': 'model-name',
               '75': 'object-identifier', '77': 'object-name', '79': 'object-type',
               '81': 'out-of-service', '85': 'present-value', '87': 'priority-array',
               '103': 'reliability', '111': 'status-flags', '117': 'units'}


def _decode_bacref(name):
    """Alerton DisplayService ORD key -> (form, obj_type, obj_inst, prop, dev).
    Encodings: `$3a`=':', `$3d`='='. Forms seen: dopr=<objType>_<objInst>_<propId>_8_<devInst>
    and devobjid=<devInst>_<objType>_<objInst>."""
    dec = name.replace('$3a', ':').replace('$3d', '=')
    m = re.search(r'bacref:([a-z]+)=(.+)$', dec)
    if not m:
        return ('', '', '', '', '')
    form, fields = m.group(1), m.group(2)
    p = fields.split('_')
    if form == 'dopr' and len(p) == 5:
        return (form, p[0], p[1], p[2], p[4])
    if form == 'devobjid' and len(p) >= 3:
        return (form, p[1], p[2], '', p[0])
    return (form, '', '', '', '')


def cmd_pointcache(bog, args):
    """Alerton Compass DisplayService PointCache: every point-property read Compass caches
    for its screens, decoded from the bacref ORD, with the last value and freshness.
    Answers 'what points does Compass show, and which bindings are dead?' -- the lens the
    generic tree/find commands miss because Compass is NOT a Tridium point model."""
    objs = [c for c in bog.handle_map.values()
            if c.type_ == 'disp:PointCacheObj' or c.simple_type() == 'PointCacheObj']
    if not objs:
        print('(no disp:PointCache in this bog -- not an Alerton Compass station, or no cache)')
        return
    rows = []
    for c in objs:
        form, ot, oi, prop, dev = _decode_bacref(c.name)
        poll = (c.slots.get('polledTime') or {}).get('value', '') or ''
        rows.append({
            'coordinate': f"{BACNET_OBJTYPE.get(ot, ot or '?')}:{oi}@dev{dev}",
            'device': dev, 'obj_type': BACNET_OBJTYPE.get(ot, ot), 'obj_inst': oi,
            'property': BACNET_PROP.get(prop, prop), 'value': c.value_val or '',
            'polled': poll, 'year': poll[:4],
        })
    newest = max((r['year'] for r in rows if r['year']), default='')
    cutoff = getattr(args, 'stale_before', None) or newest
    for r in rows:
        r['fresh'] = 'STALE' if (r['year'] and r['year'] < cutoff) else ('live' if r['year'] else '?')
    dev_f = getattr(args, 'device', None)
    if dev_f:
        rows = [r for r in rows if r['device'] == str(dev_f)]
    if getattr(args, 'stale', False):
        rows = [r for r in rows if r['fresh'] == 'STALE']
    if getattr(args, 'live', False):
        rows = [r for r in rows if r['fresh'] == 'live']
    rows.sort(key=lambda r: (r['device'], r['obj_type'], int(r['obj_inst']) if r['obj_inst'].isdigit() else 0))
    if getattr(args, 'summary', False) and not (args.json or args.csv):
        from collections import Counter
        yr = Counter(r['year'] for r in rows if r['year'])
        st = Counter(r['fresh'] for r in rows)
        total = len(rows)
        print(f"PointCache objects: {total}   (stale cutoff year: {cutoff})")
        for y in sorted(yr):
            print(f"  polled {y}: {yr[y]}")
        stale = st.get('STALE', 0)
        print(f"  STALE {stale} / live {st.get('live', 0)}"
              + (f"  = {100*stale/total:.1f}% stale" if total else ''))
        return
    _render(rows, args,
            lambda r: f"{r['coordinate']:24} {r['property']:16} = {str(r['value'])[:14]:14} "
                      f"polled {r['polled'][:10]:11} {r['fresh']}",
            empty='(no matching PointCache objects)',
            cols=['coordinate', 'device', 'obj_type', 'obj_inst', 'property', 'value', 'polled', 'fresh'])


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--json', action='store_true', help='machine JSON output')
    common.add_argument('--csv', action='store_true', help='CSV output (header + rows)')

    p = argparse.ArgumentParser(prog='bog-nav.py', description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                parents=[common])
    p.add_argument('bog', nargs='?', help='config.bog (ZIP) or a bare file.xml (omit for selftest)')
    sub = p.add_subparsers(dest='cmd', required=True)

    t = sub.add_parser('tree', parents=[common], help='component tree')
    t.add_argument('--type', help='filter by PFX:Type (or bare Type)')
    t.add_argument('--depth', type=int, help='max depth')
    t.set_defaults(func=cmd_tree)

    s = sub.add_parser('slot', parents=[common], help='a component\'s slots + children')
    s.add_argument('ref', help='path or h:handle')
    s.add_argument('slotname', nargs='?', help='a specific slot')
    s.add_argument('--src', help='module src root: fill a bog-absent type from @NiagaraProperty')
    s.set_defaults(func=cmd_slot)

    l = sub.add_parser('links', parents=[common], help='links, sourceOrd resolved to paths')
    l.add_argument('--to', help='target path/component')
    l.add_argument('--from', dest='from_', help='source path/component')
    l.add_argument('--slot', help='exact slot name on the --from source end / the --to target end (either end when neither is given)')
    l.add_argument('--slot-any', dest='slot_any', action='store_true', help='--slot matches either end regardless of --from/--to (pre-2026-09-06 behaviour)')
    l.add_argument('--dangling', action='store_true', help='only links whose tgt slot is absent from source (needs --src)')
    l.add_argument('--src', help='module src root: resolve --dangling (CHECK7)')
    l.set_defaults(func=cmd_links)

    h = sub.add_parser('handle', parents=[common], help='component at a handle + its links')
    h.add_argument('handle', help='h:xxxx or xxxx')
    h.set_defaults(func=cmd_handle)

    pa = sub.add_parser('path', parents=[common], help='reverse: handle -> component path')
    pa.add_argument('handle', help='h:xxxx or xxxx')
    pa.set_defaults(func=cmd_path)

    fi = sub.add_parser('find', parents=[common], help='flat list of components of a type')
    fi.add_argument('--type', required=True, help='PFX:Type (or bare Type)')
    fi.add_argument('--slots', action='store_true',
                    help='also match handle-less typed slots (value wrappers) the index alone misses')
    fi.set_defaults(func=cmd_find)

    ty = sub.add_parser('types', parents=[common],
                        help='histogram of component types (characterise an unknown bog)')
    ty.add_argument('--slots', action='store_true',
                    help='also count handle-less typed slots (value wrappers etc.)')
    ty.add_argument('--grep', dest='type_filter', help='only types whose name contains this substring')
    ty.set_defaults(func=cmd_types)

    pc = sub.add_parser('pointcache', parents=[common],
                        help='Alerton Compass DisplayService PointCache: decode bacref ORDs + freshness')
    pc.add_argument('--device', help='only this owning device instance')
    pc.add_argument('--stale', action='store_true', help='only stale rows')
    pc.add_argument('--live', action='store_true', help='only fresh rows')
    pc.add_argument('--stale-before', dest='stale_before',
                    help='year YYYY; rows polled before it are STALE (default: newest year in the cache)')
    pc.add_argument('--summary', action='store_true', help='print only the freshness/year summary')
    pc.set_defaults(func=cmd_pointcache)

    w = sub.add_parser('writable', parents=[common], help='classify direct value slots by external write shape')
    w.add_argument('--module', help='filter by module prefix or name')
    w.add_argument('--klass', choices=['simple', 'complex', 'bare', 'other'],
                   help='only this write class')
    w.add_argument('--src', help='module src root: fill a bog-absent type from @NiagaraProperty')
    w.set_defaults(func=cmd_writable)

    r = sub.add_parser('relays', parents=[common], help='CHECK11: own-module output -> writable proxy, fallback + writeOnUp')
    r.add_argument('--module', help='filter by source module prefix or name')
    r.set_defaults(func=cmd_relays)

    ho = sub.add_parser('hoa', parents=[common], help='CHECK8: HOA/mode slots + values, flag non-auto leftovers')
    ho.add_argument('--module', help='filter by module prefix or name')
    ho.add_argument('--all', action='store_true', help='also scan driver writables (priority arrays)')
    ho.set_defaults(func=cmd_hoa)

    ti = sub.add_parser('tiles', parents=[common], help='CHECK18: per-RoomPanel evapN tile -> unit wiring, flag crossed')
    ti.set_defaults(func=cmd_tiles)

    g = sub.add_parser('grep', parents=[common], help='regex over component paths, types, slot names')
    g.add_argument('regex')
    g.set_defaults(func=cmd_grep)

    d = sub.add_parser('diff', parents=[common], help='delta vs another bog')
    d.add_argument('bogB', help='the other config.bog|file.xml')
    d.set_defaults(func=cmd_diff)

    st = sub.add_parser('selftest', parents=[common], help='run in-memory parser/query assertions (no file needed)')
    st.set_defaults(func=cmd_selftest)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == 'selftest':
        args.func(None, args)
        return
    if not args.bog:
        sys.stderr.write('bog-nav: a config.bog|file.xml is required for this command\n')
        sys.exit(2)
    bog = Bog(args.bog)
    args.func(bog, args)


if __name__ == '__main__':
    if sys.version_info[0] < 3:
        sys.stderr.write('bog-nav: requires python3\n')
        sys.exit(3)
    main()
