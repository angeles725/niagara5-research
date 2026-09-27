/* ==========================================================================
   Module Navigator — Web Dashboard (F32)
   ES5-compatible: var, no arrow functions, no template literals, no let/const.
   Vanilla JS — no frameworks, no build step.
   ========================================================================== */

(function (window, document) {
  "use strict";

  var API = {
    ping: "/api/ping",
    stats: "/api/stats",
    modules: "/api/modules",
    module: "/api/module/",
    autocomplete: "/api/autocomplete",
    search: "/api/search",
    classProfile: "/api/class/",
    unified: "/api/unified",
    compare: "/api/compare/"
  };

  var state = {
    activeView: "search",
    autocompleteTimer: null,
    statsLoaded: false,
    modulesLoaded: false
  };

  // ------------------------------------------------------------------
  // Utilities
  // ------------------------------------------------------------------

  function $(id) { return document.getElementById(id); }
  function qsa(sel) { return document.querySelectorAll(sel); }

  function esc(s) {
    if (s === null || s === undefined) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function fmtNum(n) {
    if (n === null || n === undefined) return "-";
    return Number(n).toLocaleString();
  }

  function toast(msg, kind) {
    var el = $("toast");
    el.className = "toast show";
    if (kind) el.className += " " + kind;
    el.textContent = msg;
    setTimeout(function () {
      el.className = "toast";
    }, 2800);
  }

  function fetchJSON(url, cb, errCb) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4) return;
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          cb(JSON.parse(xhr.responseText));
        } catch (e) {
          if (errCb) errCb(e);
          else toast("parse error: " + e.message, "err");
        }
      } else {
        if (errCb) errCb(xhr.status);
        else toast("HTTP " + xhr.status + " on " + url, "err");
      }
    };
    xhr.send();
  }

  // ------------------------------------------------------------------
  // Navigation (sidebar -> views)
  // ------------------------------------------------------------------

  function showView(name) {
    state.activeView = name;
    var items = qsa(".nav-item");
    for (var i = 0; i < items.length; i++) {
      items[i].classList.remove("active");
      if (items[i].getAttribute("data-view") === name) {
        items[i].classList.add("active");
      }
    }
    var views = qsa(".view");
    for (var j = 0; j < views.length; j++) {
      views[j].classList.remove("active");
    }
    var target = $("view-" + name);
    if (target) target.classList.add("active");

    // Lazy-load data on first visit
    if (name === "stats" && !state.statsLoaded) loadStats();
    if (name === "modules" && !state.modulesLoaded) loadModules();
  }

  function bindNav() {
    var items = qsa(".nav-item");
    for (var i = 0; i < items.length; i++) {
      (function (el) {
        el.addEventListener("click", function () {
          showView(el.getAttribute("data-view"));
        });
      })(items[i]);
    }
  }

  // ------------------------------------------------------------------
  // Health check
  // ------------------------------------------------------------------

  function pingHealth() {
    var el = $("health");
    fetchJSON(API.ping, function (data) {
      if (data && data.ok) {
        el.className = "health dot-ok";
        el.textContent = "connected";
      } else {
        el.className = "health dot-err";
        el.textContent = "error";
      }
    }, function () {
      el.className = "health dot-err";
      el.textContent = "offline";
    });
  }

  // ------------------------------------------------------------------
  // VIEW: SEARCH
  // ------------------------------------------------------------------

  function renderSearchResults(data) {
    var summary = $("search-summary");
    var results = $("search-results");

    if (data.error) {
      summary.className = "summary empty";
      summary.textContent = "Error: " + data.error;
      results.innerHTML = "";
      return;
    }

    var kinds = [];
    for (var k in data.kinds) {
      if (data.kinds.hasOwnProperty(k)) {
        kinds.push(k + "=" + data.kinds[k]);
      }
    }
    summary.className = "summary";
    summary.textContent =
      "Pattern '" + data.pattern + "' : " +
      fmtNum(data.total) + " matches · showing " + data.shown +
      (kinds.length ? " · " + kinds.join(", ") : "");

    if (data.matches.length === 0) {
      results.innerHTML = '<div class="summary empty">No results.</div>';
      return;
    }

    var html = '<div class="row row-header">' +
      '<span>CLASS</span><span>KIND</span><span>LINES</span>' +
      '<span>PACKAGE · MODULE</span><span>FLAGS</span></div>';
    for (var i = 0; i < data.matches.length; i++) {
      var m = data.matches[i];
      var flag = "";
      if (m.zkm) flag = "ZKM";
      else if (m.outer_class) flag = "inner";
      html +=
        '<div class="row" data-class="' + esc(m.name) + '">' +
        '<span class="r-name">' + esc(m.name) + '</span>' +
        '<span class="r-kind">' + esc(m.kind) + '</span>' +
        '<span class="r-lines">' + (m.lines ? fmtNum(m.lines) : "-") + '</span>' +
        '<span class="r-module">' + esc(m.package || "") + "<br>" + esc(m.module || "") + '</span>' +
        '<span class="r-flag">' + esc(flag) + '</span>' +
        '</div>';
    }
    results.innerHTML = html;

    // Click -> open profile
    var rows = results.querySelectorAll(".row[data-class]");
    for (var r = 0; r < rows.length; r++) {
      (function (row) {
        row.addEventListener("click", function () {
          var cls = row.getAttribute("data-class");
          $("profile-input").value = cls;
          showView("profile");
          loadProfile(cls);
        });
      })(rows[r]);
    }
  }

  function doSearch() {
    var q = $("search-input").value.trim();
    if (!q) {
      toast("Enter a pattern", "err");
      return;
    }
    $("search-summary").className = "summary";
    $("search-summary").textContent = "Searching '" + q + "'...";
    $("search-results").innerHTML = "";
    fetchJSON(API.search + "?q=" + encodeURIComponent(q) + "&limit=200",
      renderSearchResults);
  }

  function doAutocomplete() {
    var q = $("search-input").value.trim();
    var box = $("autocomplete");
    if (q.length < 2) {
      box.innerHTML = "";
      return;
    }
    fetchJSON(API.autocomplete + "?q=" + encodeURIComponent(q) + "&limit=12",
      function (data) {
        if (!data.results || data.results.length === 0) {
          box.innerHTML = "";
          return;
        }
        var html = "";
        for (var i = 0; i < data.results.length; i++) {
          html += '<span class="ac-chip" data-cls="' + esc(data.results[i]) + '">' +
            esc(data.results[i]) + '</span>';
        }
        box.innerHTML = html;
        var chips = box.querySelectorAll(".ac-chip");
        for (var c = 0; c < chips.length; c++) {
          (function (chip) {
            chip.addEventListener("click", function () {
              var cls = chip.getAttribute("data-cls");
              $("search-input").value = cls;
              box.innerHTML = "";
              doSearch();
            });
          })(chips[c]);
        }
      });
  }

  function bindSearch() {
    $("search-btn").addEventListener("click", doSearch);
    $("search-input").addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        doSearch();
        $("autocomplete").innerHTML = "";
      }
    });
    $("search-input").addEventListener("input", function () {
      if (state.autocompleteTimer) clearTimeout(state.autocompleteTimer);
      state.autocompleteTimer = setTimeout(doAutocomplete, 180);
    });
  }

  // ------------------------------------------------------------------
  // VIEW: PROFILE
  // ------------------------------------------------------------------

  function pfield(k, v) {
    return '<span class="k">' + esc(k) + '</span><span class="v">' + v + '</span>';
  }

  function renderProfile(data) {
    var out = $("profile-output");
    if (data.error) {
      out.innerHTML = '<div class="summary empty">' + esc(data.error) + '</div>';
      return;
    }

    var impl = data.implements && data.implements.length
      ? data.implements.join(", ") : "-";
    var mods = data.modifiers && data.modifiers.length
      ? data.modifiers.join(" ") : "-";
    var inner = data.inner_classes && data.inner_classes.length
      ? data.inner_classes.slice(0, 15).join(", ") +
        (data.inner_classes.length > 15 ? " (+" + (data.inner_classes.length - 15) + " more)" : "")
      : "-";

    var zkm = data.zkm
      ? '<span class="status-warn">YES (obfuscated)</span>'
      : '<span class="status-ok">no</span>';

    var html = "";

    // Card 1: identity
    html += '<div class="pcard">';
    html += '<h3>Class Info</h3>';
    html += '<div class="pfields">';
    html += pfield("Name", esc(data.name));
    html += pfield("Package", esc(data.package || "-"));
    html += pfield("Module", esc(data.module || "-"));
    html += pfield("Kind", esc(data.kind || "-"));
    html += pfield("Modifiers", esc(mods));
    if (data.extends) html += pfield("Extends", esc(data.extends));
    html += pfield("Implements", esc(impl));
    html += pfield("Lines", fmtNum(data.lines));
    html += pfield("ZKM", zkm);
    html += pfield("Path", esc(data.path || "-"));
    html += pfield("Inner classes", esc(inner));
    html += '</div></div>';

    // Card 2: module context
    if (data.module_context) {
      var mc = data.module_context;
      html += '<div class="pcard">';
      html += '<h3>Module Context</h3>';
      html += '<div class="pfields">';
      html += pfield("Module", esc(mc.name));
      html += pfield("Type", esc(mc.type));
      html += pfield("JAR", esc(mc.jar));
      html += pfield("Java files", fmtNum(mc.java_files));
      html += pfield("Class count", fmtNum(mc.class_count));
      html += pfield("ZKM", mc.zkm ? '<span class="status-warn">YES</span>' : 'no');
      if (mc.third_party && mc.third_party.length) {
        var pills = "";
        for (var i = 0; i < mc.third_party.length && i < 12; i++) {
          pills += '<span class="pill">' + esc(mc.third_party[i]) + '</span>';
        }
        html += pfield("3rd-party", pills);
      }
      html += '</div></div>';
    }

    // Card 3: UI details (swing)
    if (data.ui) {
      var ui = data.ui;
      html += '<div class="pcard">';
      html += '<h3>UI / Swing</h3>';
      html += '<div class="pfields">';
      html += pfield("Category", esc(ui.category || "-"));
      html += pfield("Parent", esc(ui.parent || "-"));
      if (ui.titles && ui.titles.length)
        html += pfield("Titles", esc(ui.titles.join(" | ")));
      if (ui.dimensions && ui.dimensions.length)
        html += pfield("Dimensions", fmtNum(ui.dimensions.length) + " entries");
      if (ui.colors && ui.colors.length)
        html += pfield("Colors", fmtNum(ui.colors.length) + " entries");
      if (ui.fonts && ui.fonts.length)
        html += pfield("Fonts", fmtNum(ui.fonts.length) + " entries");
      if (ui.icons && ui.icons.length)
        html += pfield("Icons", fmtNum(ui.icons.length) + " entries");
      html += '</div></div>';
    }

    // Card 4: source preview
    if (data.source_preview) {
      html += '<div class="pcard">';
      html += '<h3>Source Preview (first 80 lines of ' + fmtNum(data.source_total_lines) + ')</h3>';
      html += '<pre class="source-preview">' + esc(data.source_preview) + '</pre>';
      html += '</div>';
    }

    // Card 5: cmd_profile text (for richer CLI-style output)
    if (data.profile_text) {
      html += '<div class="pcard">';
      html += '<h3>CLI Profile Output</h3>';
      html += '<pre class="source-preview">' + esc(data.profile_text) + '</pre>';
      html += '</div>';
    }

    out.innerHTML = html;
  }

  function loadProfile(name) {
    var out = $("profile-output");
    out.innerHTML = '<div class="summary">Loading profile for ' + esc(name) + '...</div>';
    fetchJSON(API.classProfile + encodeURIComponent(name), renderProfile);
  }

  function bindProfile() {
    $("profile-btn").addEventListener("click", function () {
      var n = $("profile-input").value.trim();
      if (!n) return toast("Enter a class name", "err");
      loadProfile(n);
    });
    $("profile-input").addEventListener("keydown", function (e) {
      if (e.key === "Enter") $("profile-btn").click();
    });
  }

  // ------------------------------------------------------------------
  // VIEW: MODULES
  // ------------------------------------------------------------------

  function renderModules(data) {
    var summary = $("modules-summary");
    var list = $("modules-list");

    if (data.error) {
      summary.className = "summary empty";
      summary.textContent = data.error;
      list.innerHTML = "";
      return;
    }

    summary.className = "summary";
    summary.textContent = fmtNum(data.total) + " modules";

    var html = '<div class="module-row" style="cursor:default">' +
      '<span style="color:var(--muted);font-size:10px">NAME</span>' +
      '<span style="color:var(--muted);font-size:10px">TYPE</span>' +
      '<span style="color:var(--muted);font-size:10px;text-align:right">JAVA</span>' +
      '<span style="color:var(--muted);font-size:10px;text-align:right">CLASS</span>' +
      '<span style="color:var(--muted);font-size:10px;text-align:center">ZKM</span>' +
      '<span style="color:var(--muted);font-size:10px">BC</span></div>';

    for (var i = 0; i < data.modules.length; i++) {
      var m = data.modules[i];
      html +=
        '<div class="module-row" data-mod="' + esc(m.name) + '">' +
        '<span class="mr-name">' + esc(m.name) + '</span>' +
        '<span class="mr-type">' + esc(m.type) + '</span>' +
        '<span class="mr-java">' + fmtNum(m.java_files) + '</span>' +
        '<span class="mr-class">' + fmtNum(m.class_count) + '</span>' +
        '<span class="mr-zkm">' + (m.zkm ? "Y" : "") + '</span>' +
        '<span class="mr-bc">v' + (m.bytecode || "?") + '</span>' +
        '</div>';
    }
    list.innerHTML = html;

    var rows = list.querySelectorAll(".module-row[data-mod]");
    for (var r = 0; r < rows.length; r++) {
      (function (row) {
        row.addEventListener("click", function () {
          loadModuleDetail(row.getAttribute("data-mod"));
        });
      })(rows[r]);
    }
  }

  function loadModules() {
    state.modulesLoaded = true;
    var t = $("mod-type").value;
    var zkm = $("mod-zkm").checked ? "1" : "0";
    var hc = $("mod-has-code").checked ? "1" : "";
    var url = API.modules + "?zkm=" + zkm;
    if (t) url += "&type=" + encodeURIComponent(t);
    if (hc) url += "&has_code=" + hc;
    $("modules-summary").textContent = "Loading modules...";
    $("modules-list").innerHTML = "";
    $("module-detail").innerHTML = "";
    fetchJSON(url, renderModules);
  }

  function renderModuleDetail(d) {
    var out = $("module-detail");
    if (d.error) {
      out.innerHTML = '<div class="summary empty">' + esc(d.error) + '</div>';
      return;
    }
    if (d.matches) {
      var h = '<div class="pcard"><h3>Multiple matches (' + d.match_count + ')</h3>';
      for (var i = 0; i < d.matches.length; i++) {
        var mm = d.matches[i];
        h += '<div style="padding:4px 0;font-family:var(--mono);font-size:12px">' +
          esc(mm.name) + ' · ' + esc(mm.type) +
          ' · ' + fmtNum(mm.java_files) + ' java' +
          (mm.zkm ? ' · <span class="status-warn">ZKM</span>' : '') +
          '</div>';
      }
      h += '</div>';
      out.innerHTML = h;
      return;
    }

    var html = '<div class="pcard">';
    html += '<h3>Module: ' + esc(d.name) + '</h3>';
    html += '<div class="pfields">';
    html += pfield("Parent", esc(d.parent));
    html += pfield("Type", esc(d.type));
    html += pfield("JAR", esc(d.jar));
    html += pfield("Java files", fmtNum(d.java_files));
    html += pfield("Class count", fmtNum(d.class_count));
    html += pfield("Has code", d.has_code ? '<span class="status-ok">yes</span>' : 'no');
    html += pfield("ZKM", d.zkm ? '<span class="status-warn">YES</span>' : 'no');
    html += pfield("Bytecode", "v" + d.bytecode);
    html += pfield("Vineflower", d.has_vineflower ? 'yes' : 'no');

    if (d.packages && d.packages.length) {
      var pk = "";
      for (var i = 0; i < d.packages.length && i < 30; i++) {
        pk += '<span class="pill">' + esc(d.packages[i]) + '</span>';
      }
      if (d.packages.length > 30) pk += ' (+' + (d.packages.length - 30) + ' more)';
      html += pfield("Packages (" + d.packages.length + ")", pk);
    }
    if (d.third_party && d.third_party.length) {
      var tp = "";
      for (var j = 0; j < d.third_party.length && j < 20; j++) {
        tp += '<span class="pill">' + esc(d.third_party[j]) + '</span>';
      }
      html += pfield("3rd-party", tp);
    }
    html += '</div></div>';
    out.innerHTML = html;
  }

  function loadModuleDetail(name) {
    $("module-detail").innerHTML = '<div class="summary">Loading ' + esc(name) + '...</div>';
    fetchJSON(API.module + encodeURIComponent(name), renderModuleDetail);
  }

  function bindModules() {
    $("mod-refresh").addEventListener("click", loadModules);
    $("mod-type").addEventListener("change", loadModules);
    $("mod-zkm").addEventListener("change", loadModules);
    $("mod-has-code").addEventListener("change", loadModules);
  }

  // ------------------------------------------------------------------
  // VIEW: STATS
  // ------------------------------------------------------------------

  function statCard(title, big, sub) {
    return '<div class="stat-card">' +
      '<h3>' + esc(title) + '</h3>' +
      '<div class="big">' + big + '</div>' +
      '<div class="sub">' + sub + '</div>' +
      '</div>';
  }

  function renderStats(data) {
    var grid = $("stats-grid");
    var idxBox = $("stats-indexes");
    if (data.error) {
      grid.innerHTML = '<div class="summary empty">' + esc(data.error) + '</div>';
      return;
    }
    var c = data.corpus || {};
    var ci = data.class_index || {};
    var mi = data.method_index || {};
    var fi = data.field_index || {};
    var cg = data.callgraph_index || {};
    var xr = data.xref_index || {};
    var tk = data.token_index || {};
    var st = data.string_index || {};
    var ann = data.annotations_index || {};

    var html = "";
    html += statCard("Submodules (JARs)", fmtNum(c.submodules),
      fmtNum(c.with_code) + " with code · " + fmtNum(c.without_code) + " docs/res");
    html += statCard("Unique modules", fmtNum(c.unique_modules),
      "ZKM obfuscated: " + fmtNum(c.zkm_obfuscated));
    html += statCard("Java files (decompiled)", fmtNum(c.java_files),
      "Class files: " + fmtNum(c.class_files));
    html += statCard("Unique class names", fmtNum(ci.unique_names),
      "Entries: " + fmtNum(ci.total_entries) + " · Packages: " + fmtNum(ci.packages));
    html += statCard("Method definitions", fmtNum(mi.total_definitions),
      "Unique names: " + fmtNum(mi.unique_names) + " · Constructors: " + fmtNum(mi.constructors));
    html += statCard("Field definitions", fmtNum(fi.total_definitions),
      "Static: " + fmtNum(fi.static_fields) + " · Final: " + fmtNum(fi.final_fields));
    html += statCard("Call graph edges", fmtNum(cg.total_edges),
      fmtNum(cg.caller_methods) + " callers");
    html += statCard("XRef imports", fmtNum(xr.total_import_statements),
      fmtNum(xr.total_module_dep_edges) + " module edges");
    html += statCard("Token postings (SQLite)", fmtNum(tk.total_postings),
      fmtNum(tk.unique_tokens) + " unique tokens");
    html += statCard("String constants", fmtNum(st.total_strings),
      fmtNum(st.unique_strings) + " unique");
    html += statCard("Niagara @NiagaraType", fmtNum(ann.niagara_types),
      fmtNum(ann.total_properties) + " props · " + fmtNum(ann.total_actions) + " actions");
    html += statCard("Total index size", data.total_index_size_mb + " MB",
      (data.indexes ? data.indexes.length : 0) + " index files");

    grid.innerHTML = html;

    // Index files panel
    var ih = '<h3 style="margin:0 0 10px 0;color:var(--accent);font-family:var(--mono);font-size:13px;text-transform:uppercase;letter-spacing:0.8px">Indexes on disk</h3>';
    if (data.indexes) {
      for (var i = 0; i < data.indexes.length; i++) {
        var f = data.indexes[i];
        ih += '<div class="index-row">' +
          '<span class="i-name">' + esc(f.name) + '</span>' +
          '<span class="i-size">' + f.size_mb + ' MB</span>' +
          '</div>';
      }
    }
    idxBox.innerHTML = ih;

    state.statsLoaded = true;
  }

  function loadStats() {
    $("stats-grid").innerHTML = '<div class="summary">Loading corpus stats...</div>';
    fetchJSON(API.stats, renderStats);
  }

  // ------------------------------------------------------------------
  // VIEW: UNIFIED
  // ------------------------------------------------------------------

  function renderUnified(data) {
    var sources = $("unified-sources");
    var help = $("unified-help");
    var mod = $("unified-module");
    var bog = $("unified-bog");

    if (data.error) {
      help.innerHTML = mod.innerHTML = bog.innerHTML = "";
      sources.innerHTML = '<span class="src-badge off">' + esc(data.error) + '</span>';
      return;
    }

    sources.innerHTML =
      '<span class="src-badge ' + (data.sources.help ? "ok" : "off") + '">' +
      'Help Nav: ' + (data.sources.help ? "connected" : "offline") + '</span>' +
      '<span class="src-badge ok">Module Nav: connected</span>' +
      '<span class="src-badge ' + (data.sources.bog ? "ok" : "off") + '">' +
      'BOG Nav: ' + (data.sources.bog ? "connected" : "offline") + '</span>' +
      '<span class="src-badge">Total hits: ' + fmtNum(data.totals.total) + '</span>';

    function listItems(items, kind) {
      if (!items || items.length === 0) return '<div class="muted small">(no results)</div>';
      var h = "";
      for (var i = 0; i < items.length; i++) {
        var r = items[i];
        var label = "[" + (r.type || "?") + "]";
        var name = esc(r.name || "");
        var sub = "";
        if (kind === "module") {
          if (r.type === "class") {
            sub = esc(r.module || "") + " · " + fmtNum(r.lines || 0) + " lines";
          } else if (r.type === "method") {
            sub = "in " + esc(r.class || "") + " · " + esc(r.module || "");
          }
        } else if (kind === "help") {
          if (r.type === "class") sub = esc(r.package || "");
          else if (r.type === "method") sub = "in " + esc(r.class || "");
          else if (r.type === "guide") sub = esc(r.file || r.folder || "");
        } else if (kind === "bog") {
          if (r.type === "component") sub = fmtNum(r.count || 0) + " instances";
          else if (r.type === "instance") sub = esc(r.path || "");
        }
        h += '<div class="u-item" data-name="' + name + '" data-kind="' + kind + '">' +
          '<span class="u-tag">' + esc(label) + '</span>' +
          '<strong>' + name + '</strong>' +
          (sub ? '<br><span class="muted">' + sub + '</span>' : '') +
          '</div>';
      }
      return h;
    }

    help.innerHTML = listItems(data.help, "help");
    mod.innerHTML = listItems(data.module, "module");
    bog.innerHTML = listItems(data.bog, "bog");

    // Click class entries -> open profile
    var items = document.querySelectorAll(".u-item[data-name]");
    for (var i = 0; i < items.length; i++) {
      (function (item) {
        item.addEventListener("click", function () {
          var n = item.getAttribute("data-name");
          // Best effort: only treat as class lookup if no spaces
          if (n && n.indexOf(" ") === -1) {
            $("profile-input").value = n;
            showView("profile");
            loadProfile(n);
          }
        });
      })(items[i]);
    }
  }

  function doUnified() {
    var q = $("unified-input").value.trim();
    if (!q) return toast("Enter a query", "err");
    $("unified-sources").innerHTML = '<span class="src-badge">Searching...</span>';
    $("unified-help").innerHTML = $("unified-module").innerHTML = $("unified-bog").innerHTML = "";
    fetchJSON(API.unified + "?q=" + encodeURIComponent(q) + "&limit=15", renderUnified);
  }

  function bindUnified() {
    $("unified-btn").addEventListener("click", doUnified);
    $("unified-input").addEventListener("keydown", function (e) {
      if (e.key === "Enter") doUnified();
    });
  }

  // ------------------------------------------------------------------
  // VIEW: COMPARE
  // ------------------------------------------------------------------

  function renderCompare(data) {
    var out = $("compare-output");
    if (data.error) {
      out.textContent = "Error: " + data.error;
      return;
    }
    out.textContent = data.text || "(no output)";
  }

  function doCompare() {
    var n = $("compare-input").value.trim();
    if (!n) return toast("Enter a class name", "err");
    $("compare-output").textContent = "Comparing " + n + "... (Help + Module + BOG)";
    fetchJSON(API.compare + encodeURIComponent(n), renderCompare);
  }

  function bindCompare() {
    $("compare-btn").addEventListener("click", doCompare);
    $("compare-input").addEventListener("keydown", function (e) {
      if (e.key === "Enter") doCompare();
    });
  }

  // ------------------------------------------------------------------
  // INIT
  // ------------------------------------------------------------------

  function init() {
    bindNav();
    bindSearch();
    bindProfile();
    bindModules();
    bindUnified();
    bindCompare();
    pingHealth();
    showView("search");
    // Seed example
    $("search-input").focus();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})(window, document);
