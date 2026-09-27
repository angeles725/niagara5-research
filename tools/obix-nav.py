#!/usr/bin/env python3
"""obix-nav — fast facade<->rt auditor for a Niagara JACE over oBIX.

Ported from niagara-research (N4 kit tool, originally written for the
PANCCADIA station) for the niagara5-research corpus. Adaptation: the N4
original hardcoded a PANCCADIA-specific --base default
(https://127.0.0.1:18443/obix) and a --pass-file default pointing at a
session-specific scratchpad path from that earlier investigation. Neither
default is meaningful for any N5 target, so both are now REQUIRED explicit
arguments — this tool must never silently point at a stale, unrelated
station. The room/facade/Condensadoras business logic below is unchanged and
remains PANCCADIA-shaped; it is only structurally useful if/when an N5 target
station has an equivalent oBIX-exposed facade.

One oBIX Batch read pulls hundreds of slot values in a single round-trip, so a
whole-station audit takes ~1s instead of dozens of curls.

WHAT IT ANSWERS
  - The real evaporator mapping per room (dashboard evapM -> physical
    EvaporatorUnit_X), auto-detected from coilTemp (the asymmetric discriminator).
  - Whether each per-evap control slot on the FACADE (RoomPanel) agrees with its
    rt target (BEvaporatorUnit) under that mapping -> OK / DIFF / MISSING.
  - The Condensadoras facade vs CompressorControl.

READ-ONLY. Never writes. Auth: HTTP Basic, user API, password from --pass-file.
TLS: JACE cert is self-signed -> verification disabled on purpose.

Usage:
  python3 tools/obix-nav.py --base <url> --pass-file <path> map   [--room N] [--json]
  python3 tools/obix-nav.py --base <url> --pass-file <path> dump  <room>
  python3 tools/obix-nav.py --base <url> --pass-file <path> read  <ord>
  python3 tools/obix-nav.py --base <url> --pass-file <path> cond

--base and --pass-file are REQUIRED — there is no default target.
"""
import argparse, os, ssl, sys, urllib.request, re
from base64 import b64encode

# Rooms -> ColdRoom container. Cuarto5 is comfort (20C split), no per-evap defrost.
ROOMS = {1: "ColdRoom_1", 2: "ColdRoom_2", 3: "ColdRoom_3", 4: "ColdRoom_4", 5: "ColdRoom_5"}

# Per-evap facade slot -> rt slot on the mapped EvaporatorUnit. {M} = dashboard
# evap index (1..3); the rt side is resolved through the detected mapping.
CONTROL = {
    "evap{M}Setpoint":            "evapSetpoint",
    "evap{M}DifferentialUp":      "evapDifferentialUp",
    "evap{M}DifferentialDown":    "evapDifferentialDown",
    "evap{M}CoolOnSensorFault":   "evapCoolOnSensorFault",
    "evap{M}StartDelay":          "startDelay",
    "evap{M}FreezeActive":        "freezeActive",      # rt->facade READ
    "evap{M}FreezeSetpoint":      "freezeSetpoint",
    "evap{M}FreezeDiffStop":      "freezeDiffStop",
    "evap{M}FreezeDiffRestart":   "freezeDiffRestart",
}
# Per-evap defrost lives on each unit's own BDefrostController child.
DEFROST = {
    "evap{M}DefrostInterval":          "DefrostController/interval",
    "evap{M}DefrostDuration":          "DefrostController/duration",
    "evap{M}TerminateOnResistanceTemp":"DefrostController/terminateOnResistanceTemp",
    "evap{M}ResistanceTempThreshold":  "DefrostController/resistanceTempThreshold",
}
COND = {  # Condensadoras facade -> Programacion/CompressorControl
    "highPressure":   "dischargePressure",
    "lowPressure1":   "suctionPressure",
    "lowPressure2":   "suctionPressure2",
    "amps1": "amps1", "amps2": "amps2", "amps3": "amps3",
    "hours1": "condenser1Hours", "hours2": "condenser2Hours", "hours3": "condenser3Hours",
    "comp1State": "condenser1", "comp2State": "condenser2", "comp3State": "condenser3",
}

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def _auth(pw):
    return "Basic " + b64encode(("API:" + pw).encode()).decode()


def batch(base, pw, ords, timeout=25):
    """POST an oBIX BatchIn of Reads; return {ord: (tag, val_or_None)}.
    Batch URIs are ABSOLUTE server paths and MUST keep the /obix prefix."""
    prefix = base[:base.rfind("/obix")] + "/obix"  # -> https://host/obix
    items = "".join(
        '<uri is="obix:Read" val="{}/config{}"/>'.format(prefix, o) for o in ords)
    body = ('<list is="obix:BatchIn">' + items + "</list>").encode()
    req = urllib.request.Request(base + "/batch/", data=body, method="POST")
    req.add_header("Authorization", _auth(pw))
    req.add_header("Content-Type", "text/xml")
    with urllib.request.urlopen(req, context=_ctx, timeout=timeout) as r:
        xml = r.read().decode("utf-8", "replace")
    # BatchOut preserves order; split on top-level element boundaries.
    out, i = {}, 0
    # Each result element carries href=".../config<ord>/" and (for values) val=.
    for m in re.finditer(r'<(real|bool|int|reltime|str|abstime|enum|err)\b([^>]*)/?>', xml):
        tag, attrs = m.group(1), m.group(2)
        href = re.search(r'href="[^"]*?/config([^"]*?)/?"', attrs)
        if not href:
            continue
        o = href.group(1)
        if o in out:
            continue
        v = re.search(r'\bval="([^"]*)"', attrs)
        out[o] = (tag, None if tag == "err" else (v.group(1) if v else None))
    # Fall back to input order for any the regex missed.
    for o in ords:
        out.setdefault(o, ("err", None))
    return out


def num(pair):
    tag, v = pair
    if v is None:
        return None
    try:
        return float(v)
    except ValueError:
        return v  # bool string etc.


def list_units(base, pw, coldroom):
    """Return the EvaporatorUnit child names of a ColdRoom, via one GET."""
    req = urllib.request.Request(base + "/config/Programacion/" + coldroom + "/")
    req.add_header("Authorization", _auth(pw))
    try:
        with urllib.request.urlopen(req, context=_ctx, timeout=15) as r:
            xml = r.read().decode("utf-8", "replace")
    except Exception as e:
        return []
    names = re.findall(r'href="(?:[^"]*/)?(EvaporatorUnit[0-9_]*)/"', xml)
    seen = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return sorted(seen)


def has_child(base, pw, path, child):
    """True if oBIX component at /Programacion/<path> has a direct <child>/ href."""
    req = urllib.request.Request(base + "/config/Programacion/" + path + "/")
    req.add_header("Authorization", _auth(pw))
    try:
        with urllib.request.urlopen(req, context=_ctx, timeout=15) as r:
            xml = r.read().decode("utf-8", "replace")
    except Exception:
        return False
    return re.search(r'href="(?:[^"]*/)?' + re.escape(child) + r'/"', xml) is not None


def detect_map(base, pw, coldroom, units):
    """Map dashboard evapM (by facade evapTempM) to physical unit (by coilTemp)."""
    n = len(units)
    room_i = int(coldroom.split("_")[1])
    fac = ["/Services/DashboardService/Cuarto%d/evapTemp%d" % (room_i, m) for m in range(1, n + 1)]
    rt = ["/Programacion/%s/%s/coilTemp" % (coldroom, u) for u in units]
    vals = batch(base, pw, fac + rt)
    fmap = {}
    for m in range(1, n + 1):
        fv = num(vals.get(fac[m - 1].replace("/config", ""), ("err", None)))
        # match to the unit coilTemp that equals it
        best = None
        for u in units:
            uv = num(vals.get(("/Programacion/%s/%s/coilTemp" % (coldroom, u)), ("err", None)))
            if fv is not None and uv is not None and abs(float(fv) - float(uv)) < 1e-6:
                best = u
                break
        fmap[m] = best
    return fmap


def cmd_map(a, base, pw):
    rooms = [a.room] if a.room else list(ROOMS)
    for ri in rooms:
        cr = ROOMS[ri]
        units = list_units(base, pw, cr)
        if not units:
            print("Cuarto%d (%s): sin EvaporatorUnit legibles" % (ri, cr)); continue
        fmap = detect_map(base, pw, cr, units)
        crossed = any(fmap.get(m) not in (None, "EvaporatorUnit_%d" % m, "EvaporatorUnit") for m in fmap)
        print("\n=== Cuarto%d (%s) — %d evaporador(es) — mapeo: %s ===" % (
            ri, cr, len(units), "CRUZADO" if crossed else "directo"))
        for m, u in fmap.items():
            print("  dash evap%d  ->  %s" % (m, u or "??"))
        # Defrost structure: per-evap controllers relocated? room-level disabled?
        room_ctrl = has_child(base, pw, cr, "DefrostController")
        per = [u for u in units if has_child(base, pw, cr + "/" + u, "DefrostController")]
        print("  defrost: room-level DefrostController=%s | per-evap=%d/%d %s" % (
            "PRESENTE" if room_ctrl else "no", len(per), len(units), per))
        # Build the compare batch for every control/defrost slot under this mapping.
        ords, meta = [], []
        for m, u in fmap.items():
            if not u:
                continue
            for ftpl, rslot in {**CONTROL, **DEFROST}.items():
                fslot = ftpl.format(M=m)
                fo = "/Services/DashboardService/Cuarto%d/%s" % (ri, fslot)
                ro = "/Programacion/%s/%s/%s" % (cr, u, rslot)
                ords += [fo, ro]; meta.append((m, fslot, rslot, fo, ro))
        vals = batch(base, pw, ords)
        miss = []
        for m, fslot, rslot, fo, ro in meta:
            fv = vals.get(fo, ("err", None)); rv = vals.get(ro, ("err", None))
            if fv[0] == "err" and rv[0] == "err":
                continue  # slot family absent (e.g. no resistance defrost) -> skip
            if rv[0] == "err":
                miss.append("  MISSING rt   %s (facade=%s, rt slot ausente)" % (rslot, fv[1])); continue
            if fv[0] == "err":
                miss.append("  MISSING fac  %s" % fslot); continue
            fn, rn = num(fv), num(rv)
            same = (str(fn) == str(rn)) or (isinstance(fn, float) and isinstance(rn, float) and abs(fn - rn) < 1e-6)
            if not same:
                miss.append("  DIFF  evap%d %s=%s  !=  rt %s=%s" % (m, fslot, fv[1], rslot, rv[1]))
        if miss:
            print(" Diferencias/faltantes:")
            print("\n".join(miss))
        else:
            print(" Todos los slots de control/defrost COINCIDEN facade<->rt.")


def comp_links(base, pw, path):
    """Return the BLinks whose TARGET is the component at /Programacion|/Services<path>.
    oBIX exposes each as <obj is='baja:Link'> with display
    'Indirect: <src>.<sslot> -> slot:/<tgtpath>.<tslot>'.
    Yields (src_ref, src_slot, tgt_slot)."""
    p = path if path.startswith("/") else "/" + path
    if not (p.startswith("/Programacion") or p.startswith("/Services")):
        p = ("/Services" if p.startswith("/DashboardService") or p.startswith("/Cuarto") or p.startswith("/Condensadoras") else "/Programacion") + p
    url = base + "/config" + p + "/"
    req = urllib.request.Request(url)
    req.add_header("Authorization", _auth(pw))
    try:
        with urllib.request.urlopen(req, context=_ctx, timeout=15) as r:
            xml = r.read().decode("utf-8", "replace")
    except Exception:
        return []
    out = []
    for d in re.findall(r'display="Indirect: ([^"]*)"', xml):
        d = d.replace("&#x2192;", "->")
        m = re.match(r'\s*(\S+)\.(\S+)\s*->\s*slot:/\S+\.(\S+)\s*$', d)
        if m:
            out.append((m.group(1), m.group(2), m.group(3)))
    return out


# Expected facade source-slot for each rt control slot (per dash evap index M).
# rt control slots that must have SOME facade link. The operator owns which evapM
# drives each unit, so we only flag a slot with NO link at all (MISSING), never the
# source choice. evapCoolOnSensorFault and freeze are intentionally out of scope.
EXPECT_SLOTS = ["evapSetpoint", "evapDifferentialUp", "evapDifferentialDown",
                "startDelay", "valveMode", "fanMode"]


def cmd_wiring(a, base, pw):
    rooms = [a.room] if a.room else [1, 2, 3, 4]
    for ri in rooms:
        cr = ROOMS[ri]
        units = list_units(base, pw, cr)
        if not units:
            print("Cuarto%d: sin unidades" % ri); continue
        fmap = detect_map(base, pw, cr, units)          # dash M -> unit
        umap = {u: m for m, u in fmap.items() if u}     # unit -> dash M
        crossed = any(fmap.get(m) not in (None, "EvaporatorUnit_%d" % m, "EvaporatorUnit") for m in fmap)
        print("\n=== Cuarto%d (%s) — mapeo %s: %s ===" % (
            ri, cr, "CRUZADO" if crossed else "directo",
            "  ".join("evap%d->%s" % (m, u) for m, u in fmap.items())))
        room_ctrl = has_child(base, pw, cr, "DefrostController")
        per = [u for u in units if has_child(base, pw, cr + "/" + u, "DefrostController")]
        print("  defrost: room-level=%s  per-evap=%d/%d" % ("SÍ" if room_ctrl else "no", len(per), len(units)))
        for u in units:
            m = umap.get(u)
            links = {t: s for (_r, s, t) in comp_links(base, pw, cr + "/" + u)}
            faltan = [s for s in EXPECT_SLOTS if s not in links]
            # defrost config links live on the unit's DefrostController
            if has_child(base, pw, cr + "/" + u, "DefrostController"):
                dl = {t: s for (_r, s, t) in comp_links(base, pw, cr + "/" + u + "/DefrostController")}
                for s in ("interval", "duration"):
                    if s not in dl:
                        faltan.append("DefrostController." + s)
            else:
                faltan.append("SIN DefrostController")
            if faltan:
                print("  -- %s (dash evap%s) -- FALTAN: %s" % (u, m, ", ".join(faltan)))
            else:
                print("  -- %s (dash evap%s) -- completo" % (u, m))


ROOM_AIR = {1: True, 2: True, 3: False, 4: True}  # Cuarto3 = resistance (−20)


def rt_secs(v):
    """PT8H0S / PT30M0S / PT5S -> seconds. None on parse fail."""
    if not v or not v.startswith("PT"):
        return None
    tot, num = 0.0, ""
    for ch in v[2:]:
        if ch.isdigit() or ch == ".":
            num += ch
        elif ch == "H": tot += float(num or 0) * 3600; num = ""
        elif ch == "M": tot += float(num or 0) * 60; num = ""
        elif ch == "S": tot += float(num or 0); num = ""
    return tot


def cmd_config(a, base, pw):
    rooms = [a.room] if a.room else [1, 2, 3, 4]
    US = ["evapSetpoint", "evapDifferentialUp", "evapDifferentialDown", "evapCoolOnSensorFault",
          "freezeProtect", "freezeSetpoint", "freezeDiffStop", "freezeDiffRestart",
          "hasDefrost", "airDefrost", "fanRunMode", "startDelay"]
    DS = ["mode", "interval", "duration", "terminateOnResistanceTemp", "resistanceTempThreshold", "staggerDelay"]
    for ri in rooms:
        cr = ROOMS[ri]; air = ROOM_AIR[ri]
        units = list_units(base, pw, cr)
        print("\n=== Cuarto%d (%s) — %s ===" % (ri, cr, "AIRE" if air else "RESISTENCIA (−20)"))
        for u in units:
            base_u = "/Programacion/%s/%s/" % (cr, u)
            has_ctrl = has_child(base, pw, cr + "/" + u, "DefrostController")
            ords = [base_u + s for s in US] + ([base_u + "DefrostController/" + s for s in DS] if has_ctrl else [])
            v = batch(base, pw, ords)
            g = lambda s: v.get(base_u + s, ("err", None))[1]
            gd = lambda s: v.get(base_u + "DefrostController/" + s, ("err", None))[1]
            flags = []
            sp = num(v.get(base_u + "evapSetpoint", ("err", None)))
            du = num(v.get(base_u + "evapDifferentialUp", ("err", None)))
            dd = num(v.get(base_u + "evapDifferentialDown", ("err", None)))
            fs = num(v.get(base_u + "freezeSetpoint", ("err", None)))
            fst = num(v.get(base_u + "freezeDiffStop", ("err", None)))
            fr = num(v.get(base_u + "freezeDiffRestart", ("err", None)))
            # freeze intentionally out of scope (protección anti-hielo desactivada por decisión)
            if g("hasDefrost") != "true": flags.append("hasDefrost=%s (debe true)" % g("hasDefrost"))
            if g("airDefrost") != ("true" if air else "false"): flags.append("airDefrost=%s (debe %s)" % (g("airDefrost"), air))
            if isinstance(du, float) and du <= 0: flags.append("evapDifferentialUp=0 (sin histéresis)")
            if isinstance(dd, float) and dd <= 0: flags.append("evapDifferentialDown=0 (sin histéresis)")
            if has_ctrl:
                iv = rt_secs(gd("interval")); dr = rt_secs(gd("duration"))
                term = gd("terminateOnResistanceTemp"); thr = num(v.get(base_u + "DefrostController/resistanceTempThreshold", ("err", None)))
                if iv is not None and iv <= 0: flags.append("DefrostController.interval=0")
                if dr is not None and dr <= 0: flags.append("DefrostController.duration=0")
                if iv is not None and dr is not None and iv <= dr:
                    flags.append("interval(%s) <= duration(%s) — deshiela más seguido que su propia duración" % (gd("interval"), gd("duration")))
                elif iv is not None and iv < 1800:
                    flags.append("interval=%s muy corto (<30 min) — ¿typo? (los demás cuartos ~4h)" % gd("interval"))
                if not air and term != "true": flags.append("terminateOnResistanceTemp=%s (Cuarto3 debe true)" % term)
                if air and term == "true": flags.append("terminateOnResistanceTemp=true (aire no lleva)")
                if not air and isinstance(thr, float) and thr <= 0: flags.append("resistanceTempThreshold=0 (Cuarto3 lo necesita)")
            else:
                flags.append("SIN DefrostController per-evap")
            print("  -- %s --  sp=%s diffUp=%s diffDn=%s cool=%s | freeze prot=%s sp=%s stop=%s rest=%s | hasDef=%s air=%s fan=%s startDelay=%s" % (
                u, g("evapSetpoint"), g("evapDifferentialUp"), g("evapDifferentialDown"), g("evapCoolOnSensorFault"),
                g("freezeProtect"), g("freezeSetpoint"), g("freezeDiffStop"), g("freezeDiffRestart"),
                g("hasDefrost"), g("airDefrost"), g("fanRunMode"), g("startDelay")))
            if has_ctrl:
                print("      defrost: mode=%s interval=%s duration=%s term=%s thr=%s stagger=%s" % (
                    gd("mode"), gd("interval"), gd("duration"), gd("terminateOnResistanceTemp"), gd("resistanceTempThreshold"), gd("staggerDelay")))
            for f in flags:
                print("      ⚠ " + f)


def cmd_cond(a, base, pw):
    fac = ["/Services/DashboardService/Condensadoras/" + s for s in COND]
    rt = ["/Programacion/CompressorControl/" + COND[s] for s in COND]
    vals = batch(base, pw, fac + rt)
    print("=== Condensadoras facade vs CompressorControl ===")
    for s in COND:
        fv = vals.get("/Services/DashboardService/Condensadoras/" + s, ("err", None))
        rv = vals.get("/Programacion/CompressorControl/" + COND[s], ("err", None))
        tag = "OK" if fv[1] == rv[1] and fv[0] != "err" else ("MISSING" if fv[0] == "err" or rv[0] == "err" else "DIFF")
        print("  %-8s %-14s facade=%s  rt=%s  [%s]" % (tag, s, fv[1], rv[1], COND[s]))


def cmd_read(a, base, pw):
    o = a.ord if a.ord.startswith("/") else "/" + a.ord
    print(batch(base, pw, [o]))


def cmd_dump(a, base, pw):
    ri = int(a.room); cr = ROOMS[ri]
    units = list_units(base, pw, cr)
    fac = "/Services/DashboardService/Cuarto%d/" % ri
    req = urllib.request.Request(base + "/config" + fac)
    req.add_header("Authorization", _auth(pw))
    with urllib.request.urlopen(req, context=_ctx, timeout=15) as r:
        xml = r.read().decode("utf-8", "replace")
    slots = re.findall(r'href="[^"]*?/Cuarto%d/([A-Za-z0-9_]+)/?"' % ri, xml)
    ords = [fac + s for s in dict.fromkeys(slots)]
    vals = batch(base, pw, ords)
    print("=== Cuarto%d facade (%d slots) ===" % (ri, len(ords)))
    for o in ords:
        print("  %-26s %s" % (o.split("/")[-1], vals.get(o)))
    print("  units rt:", units)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="oBIX base URL, e.g. https://host:18443/obix (no default)")
    ap.add_argument("--pass-file", required=True, help="path to a file holding the API user password (no default)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("map"); m.add_argument("--room", type=int); m.add_argument("--json", action="store_true")
    sub.add_parser("cond")
    w = sub.add_parser("wiring"); w.add_argument("--room", type=int)
    c = sub.add_parser("config"); c.add_argument("--room", type=int)
    r = sub.add_parser("read"); r.add_argument("ord")
    d = sub.add_parser("dump"); d.add_argument("room")
    a = ap.parse_args()
    if not os.path.exists(a.pass_file):
        sys.exit("No pass file: " + a.pass_file)
    pw = open(a.pass_file).read().strip()
    base = a.base.rstrip("/")
    {"map": cmd_map, "cond": cmd_cond, "wiring": cmd_wiring, "config": cmd_config, "read": cmd_read, "dump": cmd_dump}[a.cmd](a, base, pw)


if __name__ == "__main__":
    main()
