#!/usr/bin/env python3
"""
dashboard-preview — local preview server for ANY Niagara N4/N5 dashboard (-ux) module.

Used as-is from niagara-research (N4 kit tool): it serves whatever rc/ folder
--rc points to and mocks the servlet API, with no N4-specific paths, so it
applies unchanged to an N5 dashboard module's rc/ folder.

Iterate on the design (HTML/CSS/JS) of a servlet-based dashboard WITHOUT the
gradle build + sign + deploy cycle: this serves the module's real `rc/` folder
over http://localhost and mocks the servlet API, so you edit → refresh → see.

It is a REUSABLE project tool (not tied to one module): point it at any dashboard
module's rc/ with --rc, and give the servlet mount prefix with --prefix. It
faithfully reproduces the real BWebServlet behaviour so front-end bugs surface
here first:
  * <prefix>/                 -> <rc>/index.html
  * <prefix>/<path>           -> <rc>/<path>        (config.html, img/..., css/..., js/...)
  * GET  <prefix>/api/<name>  -> mock JSON (see --mock)
  * POST <prefix>/api/<name>  -> {"ok":true} and logs the body
  * XHR GUARD enforced: any /api/* request WITHOUT header
    'X-Requested-With: XMLHttpRequest' is 302-redirected to index.html, exactly
    like the chihuahua-style dispatch guard — so a page that forgets the header
    shows "--" here too, before you ever compile. (This is what caught the real
    DashboardPan header regression — see docs/module-best-practices.md §2.)

MOCK DATA (--mock): the servlet's own JSON contract is module-specific, so supply it:
  --mock <file.json>   serve this file verbatim for every GET /api/<name>.
  (none)               serve {} — layout/palette iteration still works (values show
                       as "--"); pass --mock once you want live-looking data.
For an ANIMATED mock (jittered values, status colors), a module may ship its own
thin wrapper (see the DashboardPan-ux/preview-server.py worked example, which builds
the {v,st} payload in code). This generic tool keeps to static/empty by design.

CONFIG-LOGIN FLOW MOCK (--config-login): previews the C9 R14 "second login inside the
dashboard before any write" UX on the REAL rc/ with zero module edits. Injects a native-
looking modal + a session chip + a change_log strip into the served HTML and adds STATEFUL
endpoints that mirror the R14 servlet contract:
  POST <prefix>/api/config/login   {user,pass} -> 200 {ok,user,ttl} + cookie | 401 {error:"auth"}
  POST <prefix>/api/config/logout  -> 200, session cleared
  GET  <prefix>/api/config/session -> {active,user,remaining}
  POST <prefix>/api/*          -> 403 {error:"config_login_required"} without a live session;
                                  with one: 200 + a change_log row (surface "B", config_session)
  GET  <prefix>/__mock/change_log -> the rows (what the R7 mirror would write)
The SPA's own fetch() to /api/* is intercepted: no session -> the modal opens, the write is
held, and re-issued after login. Demo password: --config-password (default 1234); session
TTL: --config-ttl seconds (default 300 = the HMI product default, sliding on each write; logout ends it at once).

USAGE:
  python3 tools/dashboard-preview.py --rc <module>/src/rc --prefix /dashboardpan
  python3 tools/dashboard-preview.py --rc ./src/rc --prefix /mymod --port 9000 --mock mock.json
then open http://localhost:<port><prefix>/

Requires only Python 3 stdlib. Ctrl+C to stop.
"""
import argparse
import json
import os
import re
import secrets
import sys
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MIME = {
    ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8", ".json": "application/json",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml", ".ico": "image/x-icon", ".map": "application/json",
    ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf", ".eot": "application/vnd.ms-fontobject",
}


EDITOR_SNIPPET = """
<style id="__ed_css">
  #__ed{position:fixed;top:10px;left:10px;z-index:2147483647;width:300px;max-height:92vh;
        overflow:auto;background:rgba(20,22,26,.94);color:#e6e9ee;font:12px system-ui,sans-serif;
        border:1px solid #3a3f47;border-radius:10px;box-shadow:0 12px 40px -12px #000;padding:12px}
  #__ed h4{margin:0 0 6px;font-size:12px;letter-spacing:.06em}
  #__ed .hint{color:#9aa2ad;font-size:11px;line-height:1.5;margin-bottom:8px}
  #__ed table{width:100%;border-collapse:collapse;font-size:11px}
  #__ed th,#__ed td{padding:2px 3px;text-align:left;border-bottom:1px solid #2a2f37;white-space:nowrap}
  #__ed th{color:#9aa2ad;font-weight:600}
  #__ed td b{color:#7fd1a8}
  #__ed .btns{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
  #__ed button{background:#2b303a;color:#e6e9ee;border:1px solid #3a3f47;border-radius:6px;
               padding:6px 8px;font-size:11px;cursor:pointer}
  #__ed button:hover{background:#353b46}
  #__ed .warn{background:#3a2b2b;border-color:#5a3a3a}
  #__ed textarea{width:100%;height:70px;margin-top:8px;background:#11141a;color:#cfe;border:1px solid #2a2f37;
                 border-radius:6px;font:11px monospace;padding:6px;display:none}
  #__ed .ok{color:#7fd1a8;font-size:11px;min-height:14px;margin-top:4px}
</style>
<script id="__ed_js">
(function(){
  if (window.__labelEditor) return; window.__labelEditor = true;
  function ready(){
    if (typeof ui==='undefined' || typeof SENSORS==='undefined'){ return setTimeout(ready,150); }
    ui.editPuntos = true;
    var box=document.createElement('div'); box.id='__ed';
    box.innerHTML =
      '<h4>EDITOR DE LABELS (solo preview)</h4>'+
      '<div class="hint">Abr\\u00ed un cuarto (clic en la lista de la derecha). '+
      'Arrastr\\u00e1 el <b>punto</b> (c\\u00edrculo) y la <b>etiqueta</b> para moverlos. '+
      'Los valores se actualizan abajo. Copi\\u00e1 y pas\\u00e1melos, o los aplico yo.</div>'+
      '<div id="__ed_room"></div>'+
      '<table><thead><tr><th>tag</th><th>rx,ry</th><th>rlx,rly</th><th>side</th></tr></thead>'+
      '<tbody id="__ed_body"></tbody></table>'+
      '<div class="btns">'+
      '<button id="__ed_copy">Copiar valores</button>'+
      '<button id="__ed_all">Copiar TODO</button>'+
      '<button id="__ed_reset" class="warn">Reset respaldo local</button>'+
      '</div><div class="ok" id="__ed_ok"></div><textarea id="__ed_ta" readonly></textarea>';
    document.body.appendChild(box);
    var fc=document.getElementById('frameC'); if(fc) fc.classList.add('edit');

    function rows(all){
      return SENSORS.filter(function(s){ return all || s.cuarto===ui.cuarto; })
        .map(function(s){
          return s.tag+': rx:'+(+s.rx).toFixed(2)+', ry:'+(+s.ry).toFixed(2)+
                 ', rlx:'+(+s.rlx).toFixed(2)+', rly:'+(+s.rly).toFixed(2)+', rside:"'+s.rside+'"';
        }).join('\\n');
    }
    function render(){
      var fc2=document.getElementById('frameC'); if(fc2) fc2.classList.add('edit');
      if(ui) ui.editPuntos=true;
      var r=document.getElementById('__ed_room');
      var b=document.getElementById('__ed_body');
      if(ui.cuarto==null){ r.textContent='Ning\\u00fan cuarto abierto.'; b.innerHTML=''; return; }
      var nm=(typeof CUARTOS!=='undefined'&&CUARTOS.find)?(CUARTOS.find(function(c){return c.id===ui.cuarto;})||{}).nombre:'';
      r.innerHTML='<b>'+(nm||('Cuarto '+ui.cuarto))+'</b>';
      var html='';
      SENSORS.filter(function(s){return s.cuarto===ui.cuarto;}).forEach(function(s){
        html+='<tr><td>'+s.tag+'</td><td><b>'+(+s.rx).toFixed(2)+','+(+s.ry).toFixed(2)+
              '</b></td><td>'+(+s.rlx).toFixed(2)+','+(+s.rly).toFixed(2)+'</td><td>'+s.rside+'</td></tr>';
      });
      b.innerHTML=html;
    }
    function copy(txt,msg){
      var ok=document.getElementById('__ed_ok'); var ta=document.getElementById('__ed_ta');
      ta.style.display='block'; ta.value=txt; ta.select();
      try{ (navigator.clipboard&&navigator.clipboard.writeText)?navigator.clipboard.writeText(txt):document.execCommand('copy'); ok.textContent=msg+' (copiado)'; }
      catch(e){ ok.textContent=msg+' (selecciona y Ctrl+C)'; }
    }
    document.getElementById('__ed_copy').onclick=function(){
      if(ui.cuarto==null){ document.getElementById('__ed_ok').textContent='Abr\\u00ed un cuarto primero.'; return; }
      copy(rows(false),'Cuarto '+ui.cuarto);
    };
    document.getElementById('__ed_all').onclick=function(){ copy(rows(true),'Todos los cuartos'); };
    document.getElementById('__ed_reset').onclick=function(){
      try{ localStorage.removeItem('panccadia.puntos.v11'); }catch(e){}
      document.getElementById('__ed_ok').textContent='Respaldo local borrado. Recargando...';
      setTimeout(function(){ location.reload(); },500);
    };
    setInterval(render,250); render();
  }
  ready();
})();
</script>
"""

CONFIG_LOGIN_SNIPPET = r"""
<style id="__cl_css">
  #__cl{position:fixed;inset:0;z-index:2147483000;display:none;align-items:center;justify-content:center;
        background:rgba(27,28,23,.55)}
  #__cl.open{display:flex}
  #__cl .card{width:min(440px,92vw);background:var(--surface,#fff);border:1px solid var(--line,#e2ded3);
        box-shadow:0 30px 90px rgba(27,28,23,.35);font-family:inherit;color:var(--ink,#1b1c17)}
  #__cl .ch{padding:13px 20px;border-bottom:1px solid var(--line-2,#eeebe3);font-family:var(--display,inherit);font-size:16px}
  #__cl .body{padding:16px 20px 18px}
  #__cl p{margin:0 0 11px;font-size:11px;line-height:1.8;color:var(--muted,#8b8a7c)}
  #__cl label{display:block;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted,#8b8a7c);margin:8px 0 4px}
  #__cl input{width:100%;box-sizing:border-box;min-height:44px;font-size:15px;padding:8px 12px;background:var(--surface-2,#faf9f5);
        border:1px solid var(--line,#e2ded3);color:var(--ink,#1b1c17)}
  #__cl .acts{display:flex;gap:8px;margin-top:14px;align-items:center;justify-content:flex-end}
  #__cl button{min-height:44px;min-width:110px;padding:8px 16px;font-size:13px;letter-spacing:.06em;cursor:pointer;
        border:1px solid var(--line,#e2ded3);background:var(--surface-2,#faf9f5);color:var(--ink,#1b1c17)}
  #__cl button.pri{background:var(--sage,#6c715d);border-color:var(--sage-d,#545948);color:#fff}
  #__cl .err{display:none;color:var(--alarm,#b23f2f);font-size:11px;margin-top:8px}
  #__cl .err.on{display:block}
  #__chip{position:fixed;top:64px;right:12px;z-index:2147482999;display:none;align-items:center;gap:10px;
        background:var(--surface,#fff);border:1px solid var(--line,#e2ded3);padding:6px 10px 6px 12px;font-size:11px;
        letter-spacing:.06em;color:var(--ink,#1b1c17);box-shadow:0 8px 24px rgba(27,28,23,.18)}
  #__chip.on{display:flex}
  #__chip b{color:var(--sage-d,#545948)}
  #__chip button{min-height:34px;padding:4px 10px;font-size:11px;cursor:pointer;border:1px solid var(--line,#e2ded3);
        background:var(--surface-2,#faf9f5);color:var(--ink,#1b1c17)}
  #__log{display:none!important;position:fixed;right:12px;bottom:12px;z-index:2147482998;width:min(520px,94vw);background:var(--surface,#fff);
        border:1px solid var(--line,#e2ded3);box-shadow:0 8px 24px rgba(27,28,23,.18);font-size:11px;color:var(--ink,#1b1c17)}
  #__log .h{padding:6px 10px;border-bottom:1px solid var(--line-2,#eeebe3);letter-spacing:.12em;text-transform:uppercase;
        color:var(--muted,#8b8a7c);font-size:10px;cursor:pointer;display:flex;justify-content:space-between}
  #__log table{width:100%;border-collapse:collapse;font-family:var(--mono,monospace);font-size:10px}
  #__log td{padding:3px 8px;border-bottom:1px solid var(--line-2,#eeebe3);white-space:nowrap}
  #__log.min table{display:none}
</style>
<div id="__cl" role="dialog" aria-modal="true"><div class="card">
  <div class="ch">Confirmar identidad para escribir</div>
  <div class="body">
    <p>Esta pantalla usa una sesi&oacute;n compartida del panel. Para <b>cambiar un valor</b> se pide tu usuario de la
       estaci&oacute;n: el cambio queda registrado a tu nombre. La sesi&oacute;n de configuraci&oacute;n dura
       <b><span id="__cl_ttl">--</span></b> y se cierra al pulsar <b>Salir</b>.</p>
    <label for="__cl_u">Usuario (estaci&oacute;n)</label><input id="__cl_u" autocomplete="username" autocapitalize="off">
    <label for="__cl_p">Contrase&ntilde;a</label><input id="__cl_p" type="password" autocomplete="current-password">
    <div class="err" id="__cl_err">Credenciales inv&aacute;lidas. Int&eacute;ntalo de nuevo.</div>
    <div class="acts"><button type="button" id="__cl_cancel">Cancelar</button><button type="button" class="pri" id="__cl_ok">Entrar</button></div>
  </div></div></div>
<div id="__chip"><span>&#128274; <b id="__chip_u"></b> &middot; <span id="__chip_t">--:--</span></span><button type="button" id="__chip_out">Salir</button></div>
<div id="__log" class="min"><div class="h" id="__log_h"><span>Registro de cambios (mock change_log, superficie B)</span><span id="__log_n">0</span></div><table><tbody id="__log_b"></tbody></table></div>
<script id="__cl_js">
(function(){
  var P="__PREFIX__", sess={active:false,user:null,remaining:0}, pending=null, tick=null;
  var $=function(i){return document.getElementById(i)};
  function xhr(){return {"X-Requested-With":"XMLHttpRequest","Content-Type":"application/json"}}
  var rawFetch=window.fetch.bind(window);
  function fmt(s){s=Math.max(0,s|0);return (s/60|0)+":"+("0"+(s%60)).slice(-2)}
  function paint(){ $("__chip").classList.toggle("on",!!sess.active); if(sess.active){$("__chip_u").textContent=sess.user;$("__chip_t").textContent=fmt(sess.remaining);} }
  function refresh(){ return rawFetch(P+"/api/config/session",{headers:xhr()}).then(function(r){return r.json()}).then(function(j){sess=j;paint();$("__cl_ttl").textContent=fmt(j.ttl||0);return j}).catch(function(){}) }
  function loop(){ clearInterval(tick); tick=setInterval(function(){ if(sess.active){sess.remaining--; if(sess.remaining<=0){sess.active=false;refresh();} paint();} },1000) }
  function open(){ $("__cl_err").classList.remove("on"); $("__cl_p").value=""; $("__cl").classList.add("open"); setTimeout(function(){($("__cl_u").value?$("__cl_p"):$("__cl_u")).focus()},50) }
  function close(){ $("__cl").classList.remove("open") }
  function isWrite(url,init){ try{ var u=new URL(url,location.href); return (init&&String(init.method||"GET").toUpperCase()==="POST") && u.pathname.indexOf(P+"/api/")===0; }catch(e){return false} }
  window.fetch=function(url,init){
    if(!isWrite(url,init)) return rawFetch(url,init);
    if(sess.active) return rawFetch(url,init).then(function(r){ if(r.status===403){ return hold(url,init); } logRefresh(); return r; });
    return hold(url,init);
  };
  function hold(url,init){ return new Promise(function(res,rej){ pending={url:url,init:init,res:res,rej:rej}; open(); }) }
  $("__cl_cancel").onclick=function(){ close(); if(pending){ var p=pending; pending=null; p.res(new Response(JSON.stringify({ok:false,error:"config_login_cancelled"}),{status:403,headers:{"Content-Type":"application/json"}})); } };
  $("__cl_ok").onclick=function(){
    var u=$("__cl_u").value.trim(), pw=$("__cl_p").value;
    rawFetch(P+"/api/config/login",{method:"POST",headers:xhr(),body:JSON.stringify({user:u,pass:pw})}).then(function(r){
      if(r.status!==200){ $("__cl_err").classList.add("on"); $("__cl_p").value=""; $("__cl_p").focus(); return; }
      return r.json().then(function(j){ sess={active:true,user:j.user,remaining:j.ttl,ttl:j.ttl}; paint(); loop(); close();
        if(pending){ var p=pending; pending=null; rawFetch(p.url,p.init).then(function(rr){ logRefresh(); refresh(); p.res(rr); },p.rej); } });
    });
  };
  $("__cl_p").addEventListener("keydown",function(e){ if(e.key==="Enter") $("__cl_ok").click(); });
  $("__chip_out").onclick=function(){ rawFetch(P+"/api/config/logout",{method:"POST",headers:xhr()}).then(function(){ sess={active:false,user:null,remaining:0}; paint(); }) };
  $("__log_h").onclick=function(){ $("__log").classList.toggle("min") };
  function logRefresh(){ rawFetch(P+"/__mock/change_log",{headers:xhr()}).then(function(r){return r.json()}).then(function(rows){
    $("__log_n").textContent=rows.length; var b=$("__log_b"); b.innerHTML="";
    rows.slice(-6).reverse().forEach(function(x){ var tr=document.createElement("tr");
      tr.innerHTML="<td>"+x.ts+"</td><td>"+x.user_email+"</td><td>"+(x.room||"")+"/"+x.slot+"</td><td>"+x.old_value+" &rarr; "+x.new_value+"</td><td>"+x.surface+"</td>"; b.appendChild(tr); });
    if(rows.length) $("__log").classList.remove("min");
  }).catch(function(){}) }
  refresh().then(loop); logRefresh();
})();
</script>
"""


# ---------------------------------------------------------------------------
# AUTO-MOCK: parse a *Reader.java and generate plausible {v,st} equipment data
# ---------------------------------------------------------------------------

def _parse_string_arrays(src):
    """Extract all String[] array declarations from Java source (regex only)."""
    arrays = {}
    for m in re.finditer(r'String\[\]\s+(\w+)\s*=\s*\{([^}]+)\}', src, re.DOTALL):
        name = m.group(1)
        items = re.findall(r'"([^"]*)"', m.group(2))
        if items:
            arrays[name] = items
    return arrays


def _classify_reader_arrays(arrays):
    """Heuristically classify extracted arrays into (entities, numeric_slots, label_slots)."""
    entities = []
    numeric_slots = []
    label_slots = []
    leftover = {}

    for name, items in arrays.items():
        nu = name.upper()
        if 'LABEL' in nu:
            label_slots = items
        elif 'NUM' in nu or ('SLOT' in nu and 'LABEL' not in nu and 'DISPLAY' in nu):
            numeric_slots = items
        elif 'DISPLAY' in nu and 'SLOT' in nu:
            numeric_slots = items
        elif 'NUM' in nu and 'SLOT' in nu:
            numeric_slots = items
        else:
            leftover[name] = items

    # Fill numeric_slots from a bare *SLOT* array if still empty
    if not numeric_slots:
        for name, items in list(leftover.items()):
            if 'SLOT' in name.upper():
                numeric_slots = items
                del leftover[name]
                break

    # Entity array: items start with uppercase or contain a digit (e.g. "Unit1")
    for name, items in leftover.items():
        if items and (items[0][0].isupper() or re.search(r'\d', items[0])):
            entities = items
            break

    return entities, numeric_slots, label_slots


def parse_reader_java(path):
    """Parse a *Reader.java and return (entities, numeric_slots, label_slots)."""
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    return _classify_reader_arrays(_parse_string_arrays(src))


def find_reader_java(rc_dir):
    """Auto-locate *Reader.java in the sibling src/ tree next to rc_dir."""
    # rc_dir is typically .../ModuleUx/src/rc  -> parent is .../ModuleUx/src/
    src_dir = os.path.dirname(rc_dir)
    for root, _dirs, files in os.walk(src_dir):
        for fname in files:
            if fname.endswith('Reader.java'):
                return os.path.join(root, fname)
    return None


_SLOT_VALUE_RULES = [
    (r'temp|temperature',      lambda ei, si: round(5.0 + ei * 1.3 + si * 0.7, 1)),
    (r'current|amp',           lambda ei, si: round(8.0 + ei * 0.5 + si * 0.4, 1)),
    (r'pressure|psig|suction', lambda ei, si: round(150.0 + ei * 5 + si * 2.0, 1)),
    (r'voltage|volt',          lambda ei, si: round(24.0 + ei * 0.3, 1)),
    (r'state|status|mode',     lambda ei, si: ei % 4),   # ordinals 0-3
    (r'humid|rh',              lambda ei, si: round(50.0 + ei * 3, 1)),
    (r'flow',                  lambda ei, si: round(200.0 + ei * 10, 1)),
    (r'power|kw',              lambda ei, si: round(1.5 + ei * 0.3, 2)),
]


def _plausible_value(slot, entity_idx, slot_idx):
    low = slot.lower()
    for pattern, fn in _SLOT_VALUE_RULES:
        if re.search(pattern, low):
            return fn(entity_idx, slot_idx)
    return round(10.0 + entity_idx * 1.1 + slot_idx * 0.5, 1)


def generate_auto_mock(entities, numeric_slots, label_slots):
    """
    Build the flat {Entity/slot: {v, st}} map.

    Status injection (covers all required badge types):
      entity[1]/slot[0] -> fault  (v=null — value untrustworthy)
      entity[2]/slot[1] -> stale  (v=last-known — kept for display)
      entity[3]/slot[2] -> overridden (v=value — override wins)
      all others        -> ok

    unitState-like slots cycle ordinals 0-3 across entities.
    Label slots always emit st:ok with the entity name / section variant.
    """
    STATUS_INJECT = {(1, 0): 'fault', (2, 1): 'stale', (3, 2): 'overridden'}
    SECTIONS = ['Zona Norte', 'Zona Sur', 'Zona Este', 'Zona Oeste']
    result = {}

    for ei, entity in enumerate(entities):
        for si, slot in enumerate(numeric_slots):
            st = STATUS_INJECT.get((ei, si), 'ok')
            v = None if st == 'fault' else _plausible_value(slot, ei, si)
            result['%s/%s' % (entity, slot)] = {'v': v, 'st': st}

        for slot in label_slots:
            if re.search(r'name|display', slot, re.IGNORECASE):
                v = entity
            else:
                v = SECTIONS[ei % len(SECTIONS)]
            result['%s/%s' % (entity, slot)] = {'v': v, 'st': 'ok'}

    return result


def make_handler(rc_dir, prefix, mock_obj, editor=False, config_login=None, live_base_url=None):
    # --config-login state: ONE shared kiosk panel -> one config session at a time (R14/D8b).
    SESS = {"token": None, "user": None, "expires": 0.0}
    CHANGE_LOG = []

    class Handler(BaseHTTPRequestHandler):
        def _cookie_token(self):
            c = self.headers.get("Cookie", "") or ""
            for part in c.split(";"):
                k, _, v = part.strip().partition("=")
                if k == "dp_config_session":
                    return v
            return None

        def _sess_active(self):
            return bool(SESS["token"]) and time.time() < SESS["expires"] and self._cookie_token() == SESS["token"]

        def _sess_touch(self):
            SESS["expires"] = time.time() + float(config_login["ttl"])

        def _json_cookie(self, obj, cookie, code=200):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Set-Cookie", cookie)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            sys.stderr.write("  %s\n" % (fmt % args))

        def _has_xhr(self):
            return self.headers.get("X-Requested-With", "") == "XMLHttpRequest"

        def _json(self, obj, code=200):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _redirect(self, location):
            self.send_response(302)
            self.send_header("Location", location)
            self.end_headers()

        def _strip(self, path):
            path = path.split("?", 1)[0]
            if prefix and path.startswith(prefix):
                path = path[len(prefix):]
            return path or "/"

        def _serve_file(self, rel):
            rel = rel.lstrip("/")
            if rel in ("", "/"):
                rel = "index.html"
            if ".." in rel or rel.startswith(("/", "\\")):
                self.send_error(404)
                return
            full = os.path.join(rc_dir, *rel.split("/"))
            if not os.path.isfile(full):
                self.send_error(404, "Not found: %s" % rel)
                return
            with open(full, "rb") as f:
                data = f.read()
            ext = os.path.splitext(full)[1].lower()
            if (editor or config_login) and ext == ".html":
                txt = data.decode("utf-8", "replace")
                snip = (EDITOR_SNIPPET if editor else "") + \
                       (CONFIG_LOGIN_SNIPPET.replace("__PREFIX__", prefix or "") if config_login else "")
                low = txt.lower()
                idx = low.rfind("</body>")
                txt = (txt[:idx] + snip + txt[idx:]) if idx != -1 else (txt + snip)
                data = txt.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")  # always fresh while iterating
            self.end_headers()
            self.wfile.write(data)

        def _hmi(self):
            # WEB-HMI10/CF frame: a 1280x800 bezel around the live local dashboard
            # (same-origin localhost iframe -> its scripts run, unlike the artifact CSP).
            frame = ("""<!doctype html><html><head><meta charset="utf-8">
<title>HMI 1280x800 preview</title><style>
 html,body{margin:0;height:100%%;background:#0b0e12;color:#c7ced8;
   font:13px system-ui,sans-serif;display:flex;flex-direction:column;
   align-items:center;justify-content:center;overflow:hidden}
 #cap{margin:10px 0 8px;letter-spacing:.12em;color:#8b93a1;font-size:11px}
 #device{background:#171a1f;border:1px solid #2a2f37;border-radius:22px;padding:22px;
   box-shadow:0 20px 60px -20px #000;transform-origin:top center}
 #dot{width:7px;height:7px;border-radius:50%%;background:#2a2f37;margin:0 auto 12px}
 iframe{width:1280px;height:800px;border:0;display:block;background:#fff;border-radius:4px}
</style></head><body>
<div id="cap">HMI 10.1&quot; capacitivo &middot; 1280&times;800</div>
<div id="device"><div id="dot"></div><iframe src="%s/" title="dashboard"></iframe></div>
<script>var d=document.getElementById('device');
 function fit(){d.style.transform='scale('+Math.min(1,(innerWidth-60)/1324,(innerHeight-96)/892)+')';}
 addEventListener('resize',fit);fit();</script></body></html>""" % (prefix or "")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(frame)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(frame)

        def _proxy_api(self, api_path):
            """Proxy an /api/* request to live_base_url, forwarding the XHR header."""
            url = live_base_url.rstrip('/') + (prefix or '') + api_path
            req = urllib.request.Request(url, headers={'X-Requested-With': 'XMLHttpRequest'})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = resp.read()
                    ct = resp.headers.get('Content-Type', 'application/json')
                self.send_response(200)
                self.send_header('Content-Type', ct)
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)
            except Exception as exc:
                self._json({'error': str(exc)}, 502)

        def do_GET(self):
            p = self._strip(self.path)
            if p == "/hmi":
                self._hmi()
                return
            if config_login and p in ("/api/config/session", "/__mock/change_log"):
                if not self._has_xhr():
                    self._redirect((prefix or "") + "/index.html")
                    return
                if p == "/api/config/session":
                    act = self._sess_active()
                    self._json({"active": act, "user": SESS["user"] if act else None,
                                "remaining": int(max(0, SESS["expires"] - time.time())) if act else 0,
                                "ttl": int(config_login["ttl"])})
                else:
                    self._json(CHANGE_LOG)
                return
            if p.startswith("/api/"):
                if not self._has_xhr():
                    self._redirect((prefix or "") + "/index.html")
                    return
                if live_base_url:
                    self._proxy_api(p)
                else:
                    self._json(mock_obj)   # same mock for any /api/<name> GET
                return
            self._serve_file(p)

        def do_POST(self):
            p = self._strip(self.path)
            if p.startswith("/api/") and not self._has_xhr():
                self._redirect((prefix or "") + "/index.html")
                return
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(length).decode("utf-8", "replace") if length else ""
            sys.stderr.write("  [POST %s] %s\n" % (p, body))
            if config_login and p in ("/api/config/login", "/api/config/logout"):
                if not self._has_xhr():
                    self._redirect((prefix or "") + "/index.html")
                    return
                if p == "/api/config/logout":
                    SESS.update(token=None, user=None, expires=0.0)
                    self._json_cookie({"ok": True}, "dp_config_session=; Path=%s/; Max-Age=0; SameSite=Lax" % (prefix or ""))
                    return
                try:
                    req = json.loads(body or "{}")
                except ValueError:
                    req = {}
                user = str(req.get("user", "")).strip()
                # the real R14 servlet re-auths against the STATION user DB; the mock accepts one demo password
                if not user or str(req.get("pass", "")) != config_login["password"]:
                    self._json({"ok": False, "error": "auth"}, 401)
                    return
                SESS.update(token=secrets.token_hex(16), user=user)
                self._sess_touch()
                self._json_cookie({"ok": True, "user": user, "ttl": int(config_login["ttl"])},
                                  "dp_config_session=%s; Path=%s/; SameSite=Lax" % (SESS["token"], prefix or ""))
                return
            if config_login and p.startswith("/api/"):
                if not self._sess_active():
                    self._json({"ok": False, "error": "config_login_required"}, 403)
                    return
                self._sess_touch()   # sliding TTL: every write extends the session
                try:
                    req = json.loads(body or "{}")
                except ValueError:
                    req = {}
                ord_ = str(req.get("ord", ""))
                room, _, slot = ord_.partition("/")
                old = None
                try:   # best-effort "old" from the GET mock, mirroring the real pre-write GET
                    old = mock_obj.get(ord_, mock_obj.get(slot, {})).get("v") if isinstance(mock_obj, dict) else None
                except Exception:
                    old = None
                CHANGE_LOG.append({"ts": time.strftime("%H:%M:%S"), "user_email": SESS["user"],
                                   "config_session": SESS["token"][:8], "room": room or None, "slot": slot or ord_,
                                   "old_value": old, "new_value": req.get("value"), "area": "control" if slot.endswith("Mode") else "config",
                                   "surface": "B", "result": 200, "ok": True})
            self._json({"ok": True})

    return Handler


def main():
    ap = argparse.ArgumentParser(description="Local preview server for a Niagara dashboard -ux module.")
    ap.add_argument("--rc", default="./src/rc", help="path to the module's rc/ folder (default ./src/rc)")
    ap.add_argument("--prefix", default="/dashboardpan", help="servlet mount prefix (default /dashboardpan)")
    ap.add_argument("--port", type=int, default=8080, help="port (default 8080)")
    ap.add_argument("--mock", help="JSON file served for every GET /api/<name> (default: empty {})")
    ap.add_argument("--auto-mock", action="store_true",
                    help="generate equipment mock by parsing the module's *Reader.java; "
                         "mutually exclusive with --mock and --live")
    ap.add_argument("--reader", metavar="Reader.java",
                    help="path to the *Reader.java when using --auto-mock; "
                         "if omitted the file is auto-located under the sibling src/ of --rc")
    ap.add_argument("--live", metavar="BASE_URL",
                    help="proxy /api/* requests to BASE_URL/<prefix>/api/* (real station data); "
                         "mutually exclusive with --mock and --auto-mock")
    ap.add_argument("--config-login", action="store_true",
                    help="preview the R14 'second login before any write' flow: injects a native modal + session chip + "
                         "change_log strip and adds stateful /config/login|logout|session mock endpoints; writes need a session")
    ap.add_argument("--config-password", default="1234", help="demo password accepted by the mock login (default 1234)")
    ap.add_argument("--config-ttl", type=int, default=300, help="mock config-session TTL in seconds, sliding (default 300 = the HMI product default, lead 2026-09-06)")
    ap.add_argument("--editor", action="store_true",
                    help="inject a preview-only label editor (drag points/labels, export rx/ry/rlx/rly/rside); "
                         "never touches the module rc/")
    args = ap.parse_args()

    # --- mutual exclusion ---
    mode_count = sum([bool(args.mock), args.auto_mock, bool(args.live)])
    if mode_count > 1:
        ap.error("--mock, --auto-mock, and --live are mutually exclusive; pick one")

    rc_dir = os.path.abspath(args.rc)
    if not os.path.isdir(rc_dir):
        sys.exit("ERROR: --rc no es un directorio: %s" % rc_dir)
    prefix = "/" + args.prefix.strip("/") if args.prefix.strip("/") else ""

    mock_obj = {}
    live_base_url = None
    mock_label = "(vacio)"

    if args.mock:
        with open(args.mock, "r", encoding="utf-8") as f:
            mock_obj = json.load(f)
        mock_label = args.mock

    elif args.auto_mock:
        reader_path = args.reader
        if not reader_path:
            reader_path = find_reader_java(rc_dir)
        if not reader_path or not os.path.isfile(reader_path):
            sys.exit("ERROR: --auto-mock: no se encontro *Reader.java. "
                     "Especifica --reader <path> o asegurate de que exista bajo el src/ del modulo.")
        entities, numeric_slots, label_slots = parse_reader_java(reader_path)
        if not entities:
            sys.exit("ERROR: --auto-mock: no se pudo extraer el array de entidades de %s" % reader_path)
        mock_obj = generate_auto_mock(entities, numeric_slots, label_slots)
        mock_label = "auto-mock desde %s (%d entidades, %d slots numericos, %d label slots)" % (
            os.path.basename(reader_path), len(entities), len(numeric_slots), len(label_slots))
        sys.stderr.write("  [auto-mock] entidades: %s\n" % entities)
        sys.stderr.write("  [auto-mock] num_slots:  %s\n" % numeric_slots)
        sys.stderr.write("  [auto-mock] label_slots:%s\n" % label_slots)
        sys.stderr.write("  [auto-mock] keys generadas: %d\n" % len(mock_obj))

    elif args.live:
        live_base_url = args.live.rstrip('/')
        mock_label = "live proxy -> %s" % live_base_url

    else:
        sys.stderr.write("  (sin --mock/--auto-mock/--live: /api/* devuelve {} — el diseño/paleta se ve, los valores salen '--')\n")

    config_login = {"password": args.config_password, "ttl": args.config_ttl} if args.config_login else None
    srv = ThreadingHTTPServer(("127.0.0.1", args.port),
                              make_handler(rc_dir, prefix, mock_obj, args.editor, config_login, live_base_url))
    print("dashboard-preview -> http://localhost:%d%s/" % (args.port, prefix))
    print("  serving: %s" % rc_dir)
    print("  mock:    %s" % mock_label)
    if args.editor:
        print("  editor:  ON (editor de labels inyectado; NO toca el modulo)")
    if config_login:
        print("  config-login: ON — cualquier usuario + contrasena '%s', sesion %ds (deslizante); "
              "escribir sin sesion -> 403 + modal; Salir cierra la sesion" % (config_login["password"], config_login["ttl"]))
    print("  Ctrl+C para detener. Edita rc/ y refresca (sin recompilar).")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\ndetenido.")


if __name__ == "__main__":
    main()
