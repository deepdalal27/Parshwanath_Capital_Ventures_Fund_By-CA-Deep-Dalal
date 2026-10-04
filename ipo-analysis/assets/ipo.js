/* IPO Analysis desk - renders data/index.json, data/queue.json and per-issuer pages. No framework. */
(function () {
  "use strict";

  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  var getJSON = function (url) {
    return fetch(url + (url.indexOf("?") < 0 ? "?" : "&") + "t=" + Date.now(), { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error(r.status + " " + url); return r.json(); });
  };
  var pct = function (v) { return typeof v === "number" ? (v * 100).toFixed(1) + "%" : "-"; };
  var rs = function (v) { return typeof v === "number" ? v.toLocaleString("en-IN", { maximumFractionDigits: 2 }) : "-"; };
  var date = function (s) {
    if (!s) return "-";
    var d = new Date(s + (s.length === 10 ? "T00:00:00" : ""));
    return isNaN(d) ? esc(s) : d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  };
  var callBadge = function (c) {
    var k = String(c || "").toLowerCase();
    var cls = k === "subscribe" ? "b-subscribe" : k === "avoid" ? "b-avoid" : k === "neutral" ? "b-neutral" : "b-plain";
    return '<span class="badge ' + cls + '">' + esc(c || "Pending") + "</span>";
  };
  var flagClass = function (f) { return /^(RED|DEGENERATE|INCONSISTENT)/.test(f) ? "flag-red" : /^AMBER/.test(f) ? "flag-amber" : ""; };
  var $ = function (id) { return document.getElementById(id); };
  var safeUrl = function (u) { return /^https?:\/\//i.test(String(u || "")) ? esc(u) : ""; };

  function checks(c) {
    if (!c || !window.IPODashboard) return "-";
    var ch = window.IPODashboard.chip;
    return ch("FAIL") + " " + (c.fail || 0) + " " + ch("WATCH") + " " + (c.watch || 0) + " " + ch("PASS") + " " + (c.pass || 0);
  }
  function portfolioCharts(rows) {
    if (!window.IPOCharts || !rows.length) {
      ["chart-upside", "chart-checks"].forEach(function (id) { if ($(id)) $(id).style.display = "none"; });
      return;
    }
    var nm = function (r) { return String(r.company || r.slug).replace(/ (Limited|Ltd)$/, ""); };
    var up = rows.filter(function (r) { return r.neutral && r.neutral.upside_cap != null; })
      .sort(function (a, b) { return b.neutral.upside_cap - a.neutral.upside_cap; });
    window.IPOCharts.hbars($("chart-upside"), { title: "Neutral blended value vs reference price", subtitle: "Upside / (downside) by issuer. Positive values are above the reference price.",
      items: up.map(function (r) { return { label: nm(r), value: r.neutral.upside_cap, note: (r.call || "") + " · " + (r.stage || "") }; }), fmt: "pct", axisFmt: "pct0", diverging: true, labelWidth: 180 });
    var withC = rows.filter(function (r) { return r.counts; });
    window.IPOCharts.hbars($("chart-checks"), { title: "Where diligence is needed", subtitle: "Failed plus watch-list forensic checks per issuer. More items mean more work before a decision.",
      items: withC.map(function (r) { return { label: nm(r), value: (r.counts.fail || 0) + (r.counts.watch || 0), note: (r.counts.fail || 0) + " fail, " + (r.counts.watch || 0) + " watch" }; })
        .sort(function (a, b) { return b.value - a.value; }), fmt: "int", labelWidth: 180 });
  }

  /* ---------------------------------------------------------------- list page */
  function initList() {
    var rows = [], sortKey = "filed_on", sortDir = -1;

    function render() {
      var q = $("q").value.trim().toLowerCase(), pf = $("f-platform").value, st = $("f-stage").value, cl = $("f-call").value;
      var list = rows.filter(function (r) {
        var hay = [r.company, r.sector, r.brlm, r.headline].join(" ").toLowerCase();
        return (!q || hay.indexOf(q) >= 0) && (!pf || r.platform === pf) && (!st || r.stage === st) &&
          (!cl || String(r.call || "Pending") === cl);
      }).sort(function (a, b) {
        var x = a[sortKey], y = b[sortKey];
        if (sortKey === "upside") { x = a.neutral && a.neutral.upside_cap; y = b.neutral && b.neutral.upside_cap; }
        x = x == null ? "" : x; y = y == null ? "" : y;
        return (x > y ? 1 : x < y ? -1 : 0) * sortDir;
      });
      $("count").textContent = list.length + " of " + rows.length;
      if (!rows.length) {
        $("tbody").innerHTML = '<tr><td colspan="8"><div class="empty">No offer documents analysed yet. ' +
          "New DRHP / RHP filings are picked up automatically by the scheduled analysis routine and appear here.</div></td></tr>";
        return;
      }
      $("tbody").innerHTML = list.map(function (r) {
        var n = r.neutral || {};
        var flags = (r.red_flags || []).slice(0, 3).map(function (f) { return "<li>" + esc(f) + "</li>"; }).join("");
        return "<tr>" +
          '<td><a class="co" href="view.html?c=' + encodeURIComponent(r.slug) + '">' + esc(r.company || r.slug) + "</a>" +
          '<div class="small muted">' + esc(r.sector || "") + "</div>" +
          (r.headline ? '<div class="small">' + esc(r.headline) + "</div>" : "") +
          (flags ? '<ul class="flags">' + flags + "</ul>" : "") + "</td>" +
          "<td>" + esc(r.platform || "-") + '<div class="small muted">' + esc(r.stage || "") + "</div></td>" +
          '<td class="num">' + date(r.filed_on) + "</td>" +
          '<td class="num hide-sm">' + rs(r.issue_size_cr) + "</td>" +
          '<td class="hide-sm">' + checks(r.counts) + (r.focus_top && r.focus_top.length ? '<div class="small muted">Focus: ' + esc(r.focus_top.join("; ")) + "</div>" : "") + "</td>" +
          '<td class="num">' + rs(n.blended) + "</td>" +
          '<td class="num">' + pct(n.upside_cap) + "</td>" +
          "<td>" + callBadge(r.call) + "</td></tr>";
      }).join("");
    }

    ["q", "f-platform", "f-stage", "f-call"].forEach(function (id) { $(id).addEventListener("input", render); });
    Array.prototype.forEach.call(document.querySelectorAll("th[data-k]"), function (th) {
      th.addEventListener("click", function () {
        var k = th.getAttribute("data-k");
        sortDir = sortKey === k ? -sortDir : -1; sortKey = k; render();
      });
    });

    getJSON("data/index.json").then(function (d) {
      rows = d.issuers || [];
      $("s-count").textContent = rows.length;
      $("s-updated").textContent = d.updated ? d.updated.replace("T", " ").replace("Z", " UTC") : "-";
      $("s-sub").textContent = rows.filter(function (r) { return r.call === "Subscribe"; }).length;
      render();
      portfolioCharts(rows);
    }).catch(function (e) {
      $("tbody").innerHTML = '<tr><td colspan="8"><div class="empty">Could not load data/index.json (' + esc(e.message) +
        "). Open this page through the website, not as a local file.</div></td></tr>";
    });

    getJSON("data/queue.json").then(function (d) {
      var p = d.pending || [];
      $("s-queue").textContent = p.length;
      $("queue").innerHTML = p.length ? p.map(function (f) {
        return '<div class="card"><h3>' + esc(f.company) + "</h3><p>" + esc(f.platform || "") + " &middot; " + esc(f.stage || "DRHP") +
          " &middot; filed " + date(f.filed_on) + (f.note ? "<br>" + esc(f.note) : "") + "</p>" +
          (safeUrl(f.doc_url) ? '<a class="btn btn--ghost" href="' + safeUrl(f.doc_url) + '" target="_blank" rel="noopener">Offer document</a>' : "") + "</div>";
      }).join("") : '<div class="empty">Nothing waiting. ' + (d.last_scan ? "Last scan: " + esc(d.last_scan) + "." : "") + "</div>";
      if (d.last_scan) $("s-scan").textContent = d.last_scan.replace("T", " ").replace("Z", " UTC");
    }).catch(function () { $("queue").innerHTML = '<div class="empty">Queue not available yet.</div>'; });
  }

  /* -------------------------------------------------------------- detail page */
  function initView() {
    var slug = new URLSearchParams(location.search).get("c");
    if (!slug || !/^[a-z0-9-]+$/.test(slug)) { $("title").textContent = "Issuer not found"; return; }
    var base = "companies/" + slug + "/";
    getJSON(base + "meta.json").then(function (m) {
      document.title = (m.company || slug) + " - IPO Analysis";
      $("title").textContent = m.company || slug;
      $("crumb").textContent = m.company || slug;
      $("lead").innerHTML = esc(m.headline || "");
      $("call").innerHTML = callBadge(m.call);
      var kv = [["Platform", m.platform], ["Stage", m.stage], ["Filed", date(m.filed_on)], ["Analysed", date(m.analysed_on)],
        ["Sector", m.sector], ["Lead manager(s)", m.brlm], ["Issue size (Rs cr)", rs(m.issue_size_cr)],
        ["Price band", m.price_band || "Not announced"], ["Valuation reference", m.reference_note], ["Exit route underwritten", m.exit_route]];
      $("facts").innerHTML = kv.map(function (p) { return "<dt>" + esc(p[0]) + "</dt><dd>" + (p[1] == null || p[1] === "" ? "-" : esc(p[1])) + "</dd>"; }).join("");
      getJSON(base + "charts.json").then(function (ch) {
        var draw = function () { window.IPODashboard.render($("dash"), ch, m); };
        draw();
        var w = window.innerWidth, t;
        window.addEventListener("resize", function () {
          if (Math.abs(window.innerWidth - w) < 40) return;
          w = window.innerWidth; clearTimeout(t); t = setTimeout(draw, 200);
        });
      }).catch(function () { $("dash").innerHTML = '<p class="muted">Dashboard not available for this issuer.</p>'; });
      var files = m.files || {}, dl = [];
      [["pdf", "Full report (.pdf)"], ["screening", "Screening checklist (.xlsx)"], ["anchor", "Anchor & QIB economics (.xlsx)"], ["valuation", "Comps & valuation model (.xlsx)"],
        ["note", "Due-diligence note (.md)"]].forEach(function (f) {
        if (files[f[0]]) dl.push('<a class="btn" href="' + base + encodeURIComponent(files[f[0]]) + '" download>' + f[1] + "</a>");
      });
      if (safeUrl(m.doc_url)) dl.push('<a class="btn btn--ghost" href="' + safeUrl(m.doc_url) + '" target="_blank" rel="noopener">Offer document (source)</a>');
      $("downloads").innerHTML = dl.join("") || '<span class="muted">No files yet.</span>';
      if (files.note) {
        fetch(base + files.note + "?t=" + Date.now(), { cache: "no-store" }).then(function (r) { return r.text(); }).then(function (t) {
          if (window.marked && window.DOMPurify) $("note").innerHTML = window.DOMPurify.sanitize(window.marked.parse(t));
          else { var pre = document.createElement("pre"); pre.style.whiteSpace = "pre-wrap"; pre.textContent = t; $("note").innerHTML = ""; $("note").appendChild(pre); }
        });
      } else { $("note").innerHTML = '<p class="muted">Note not yet written.</p>'; }
    }).catch(function () { $("title").textContent = "Issuer not found"; });
  }

  function initDisclaimer() {
    getJSON("data/disclaimer.json").then(function (d) {
      Array.prototype.forEach.call(document.querySelectorAll("[data-disc-short]"), function (el) { el.textContent = d.short; });
      Array.prototype.forEach.call(document.querySelectorAll("[data-disc-full]"), function (el) {
        el.innerHTML = (d.paragraphs || []).map(function (p) { return "<p>" + esc(p) + "</p>"; }).join("");
      });
    }).catch(function () { /* keep the static fallback text */ });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initDisclaimer();
    if (document.body.getAttribute("data-page") === "list") initList();
    if (document.body.getAttribute("data-page") === "view") initView();
  });
})();
