/* IPO Desk - renders data/calendar.json + data/index.json (RHP-stage reports) and per-issuer pages. No framework. */
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

  var istToday = function () {
    var d = new Date(Date.now() + (330 + new Date().getTimezoneOffset()) * 60000);
    return d.toISOString().slice(0, 10);
  };
  var short = function (s) {
    if (!s) return "-";
    var d = new Date(s + "T00:00:00");
    return isNaN(d) ? esc(s) : d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
  };
  var upperBand = function (band) {
    var n = String(band || "").match(/\d[\d,]*(?:\.\d+)?/g);
    return n ? parseFloat(n[n.length - 1].replace(/,/g, "")) : null;
  };
  var inr = function (v, d) { return typeof v === "number" ? "Rs " + v.toLocaleString("en-IN", { maximumFractionDigits: d == null ? 0 : d }) : "-"; };
  var signed = function (v) { return typeof v === "number" ? (v > 0 ? "+" : "") + (v * 100).toFixed(1) + "%" : "-"; };
  var phase = function (i, today) {
    if (i.open_date && today < i.open_date) return "Upcoming";
    if (i.close_date && today > i.close_date) return "Closed";
    return i.open_date ? "Open" : "Upcoming";
  };
  var bandText = function (b) {
    if (!b) return "-";
    var t = String(b).replace(/\s*\(.*\)$/, "").replace(/\d[\d,]*(?:\.\d+)?/g, function (n) {
      return parseFloat(n.replace(/,/g, "")).toLocaleString("en-IN");
    });
    return esc(t);
  };

  // PAT and P/E as the company discloses them (RHP Basis for Offer Price, at the price band)
  function xx(v) { return v == null ? "-" : v.toFixed(2) + "x"; }
  function companyPe(c) {
    if (!c) return "";
    return "<div><dt>PAT " + esc(c.period || "") + " (company)</dt><dd>" + (c.pat_cr != null ? "Rs " + c.pat_cr.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " cr" : "-") + "</dd></div>" +
      '<div><dt>Company P/E at band</dt><dd title="Price band divided by the company\'s own EPS (RHP Basis for Offer Price)">' +
      (c.pe_floor_basic != null ? c.pe_floor_basic.toFixed(1) + "x - " + c.pe_cap_basic.toFixed(1) + "x" : "-") + "</dd></div>";
  }
  function companyPeRows(c) {
    if (!c) return [["Company PAT and P/E (RHP)", "Not yet recorded"]];
    var ind = c.industry_pe || {};
    return [["PAT " + (c.period || "") + " (as disclosed)", c.pat_cr != null ? "Rs " + c.pat_cr.toLocaleString("en-IN") + " cr" + (c.pat_basis ? " (" + c.pat_basis + ")" : "") : null],
      ["EPS " + (c.period || "") + " (basic / diluted)", c.eps_basic != null ? "Rs " + c.eps_basic + " / Rs " + c.eps_diluted : null],
      ["Company P/E at floor (basic / diluted)", xx(c.pe_floor_basic) + " / " + xx(c.pe_floor_diluted)],
      ["Company P/E at cap (basic / diluted)", xx(c.pe_cap_basic) + " / " + xx(c.pe_cap_diluted)],
      ["Industry peer P/E (high / low / avg, RHP)", ind.high != null ? ind.high + "x / " + ind.low + "x / " + ind.avg + "x" : null],
      ["Source of company figures", c.source]];
  }

  function issueCard(i, r, today) {
    var ph = phase(i, today), ub = upperBand(i.price_band || (r && r.price_band));
    var lot = i.lot_size || (r && r.lot_size);
    var minInv = lot && ub ? lot * ub : null;
    var status = ph === "Open" ? '<span class="chip chip--live">Open &middot; closes ' + short(i.close_date) + "</span>"
      : '<span class="chip">Opens ' + short(i.open_date) + "</span>";
    var head = '<div class="ic__top"><span class="chip chip--plain">' + esc(i.platform || (r && r.platform) || "Mainboard") + "</span>" + status +
      (r ? '<span class="ic__call">' + callBadge(r.call) + "</span>" : '<span class="ic__call"><span class="badge b-plain">In preparation</span></span>') + "</div>";
    var name = r ? '<a class="ic__name" href="view.html?c=' + encodeURIComponent(r.slug) + '">' + esc(i.company) + "</a>"
      : '<span class="ic__name">' + esc(i.company) + "</span>";
    var kv = '<dl class="ic__kv">' +
      "<div><dt>Price band</dt><dd>" + bandText(i.price_band || (r && r.price_band)) + "</dd></div>" +
      "<div><dt>Lot / min. bid</dt><dd>" + (lot ? lot + " sh" + (minInv ? " &middot; " + inr(minInv) : "") : "-") + "</dd></div>" +
      "<div><dt>Issue size</dt><dd>" + (r && r.issue_size_cr ? inr(r.issue_size_cr) + " cr" : "-") + "</dd></div>" +
      "<div><dt>Listing</dt><dd>" + short((r && r.listing_date) || i.listing_date) + "</dd></div>" + companyPe(r && r.company_pe) + "</dl>";
    var val = "";
    if (r && r.neutral) {
      var up = ub && r.neutral.blended ? r.neutral.blended / ub - 1 : r.neutral.upside_cap;
      val = '<div class="ic__val">' +
        '<div><span class="ic__lbl">Fair value (Neutral)</span><b>' + inr(r.neutral.blended) + "</b></div>" +
        '<div><span class="ic__lbl">vs upper band</span><b class="' + (up >= -0.1 ? "pos" : up < -0.3 ? "neg" : "mid") + '">' + signed(up) + "</b></div>" +
        '<div><span class="ic__lbl">Bear - Bull</span><b>' + inr(r.bear) + " - " + inr(r.bull) + "</b></div>" +
        '<div><span class="ic__lbl">Our P/E post-issue / adjusted</span><b>' + (r.pe_reported ? r.pe_reported.toFixed(1) + "x" : "-") + " / " +
        (r.pe_adjusted ? r.pe_adjusted.toFixed(1) + "x" : "-") + (r.eq_material ? ' <span class="flag-amber" title="Earnings-quality adjustments above 10%">&#9679;</span>' : "") + "</b></div></div>";
    }
    var prov = r && r.rhp_read === false ? '<p class="ic__prov">Provisional: built without the RHP, which was not retrievable (sources are stated in the report basis). It is refreshed automatically once the RHP is available.</p>' : "";
    var body = r ? prov + '<p class="ic__hl">' + esc(r.headline || "") + "</p>"
      : '<p class="ic__hl muted">The RHP is being analysed. The report is published here before the issue opens.</p>';
    var foot = r ? '<div class="ic__foot"><a class="btn" href="view.html?c=' + encodeURIComponent(r.slug) + '">Read the report</a>' +
      (r.pdf ? '<a class="btn btn--ghost" href="companies/' + encodeURIComponent(r.slug) + "/" + encodeURIComponent(r.pdf) + '" target="_blank" rel="noopener">PDF</a>' : "") +
      '<span class="small muted">' + esc(r.sector || "") + "</span></div>" : "";
    return '<article class="ic' + (ph === "Open" ? " ic--live" : "") + '">' + head + name + kv + val + body + foot + "</article>";
  }

  /* ---------------------------------------------------------------- list page */
  function initList() {
    var today = istToday();
    Promise.all([getJSON("data/index.json").catch(function () { return { issuers: [] }; }),
                 getJSON("data/calendar.json").catch(function () { return { issues: [] }; })]).then(function (res) {
      var rows = res[0].issuers || [], cal = res[1] || {}, bySlug = {};
      rows.forEach(function (r) { bySlug[r.slug] = r; });
      var issues = (cal.issues || []).slice(), seen = {};
      issues.forEach(function (i) { seen[i.slug] = 1; });
      rows.forEach(function (r) {   // reports whose issue has dropped off the exchange calendar
        if (!seen[r.slug]) issues.push({ company: r.company, slug: r.slug, platform: r.platform, price_band: r.price_band,
          open_date: r.open_date, close_date: r.close_date, lot_size: r.lot_size, listing_date: r.listing_date });
      });
      var open = [], soon = [], closed = [];
      issues.forEach(function (i) {
        var ph = phase(i, today);
        (ph === "Open" ? open : ph === "Upcoming" ? soon : closed).push(i);
      });
      var byOpen = function (a, b) { return (a.open_date || "") < (b.open_date || "") ? -1 : 1; };
      open.sort(byOpen); soon.sort(byOpen); closed.sort(function (a, b) { return byOpen(b, a); });
      $("s-open").textContent = open.length;
      $("s-soon").textContent = soon.length;
      $("s-count").textContent = rows.length;
      $("s-scan").textContent = cal.last_scan ? new Date(cal.last_scan.replace("Z", ":00Z")).toLocaleString("en-IN",
        { timeZone: "Asia/Kolkata", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }) + " IST" : "-";
      $("open-meta").textContent = "As of " + short(today) + " (IST)";
      $("g-open").innerHTML = open.length ? open.map(function (i) { return issueCard(i, bySlug[i.slug], today); }).join("")
        : '<div class="empty">No issue is open for subscription today.</div>';
      $("g-soon").innerHTML = soon.length ? soon.map(function (i) { return issueCard(i, bySlug[i.slug], today); }).join("")
        : '<div class="empty">No price band has been announced for an upcoming issue yet. New issues appear here as soon as the band is out.</div>';
      $("t-closed").innerHTML = closed.length ? closed.map(function (i) {
        var r = bySlug[i.slug], ub = upperBand(i.price_band || (r && r.price_band));
        var up = r && r.neutral && ub ? r.neutral.blended / ub - 1 : null;
        return "<tr><td>" + (r ? '<a class="co" href="view.html?c=' + encodeURIComponent(r.slug) + '">' + esc(i.company) + "</a>" : esc(i.company)) +
          '<div class="small muted">' + esc((r && r.sector) || i.platform || "") + "</div></td>" +
          '<td class="hide-sm">' + short(i.open_date) + " - " + short(i.close_date) + "</td>" +
          "<td>" + bandText(i.price_band || (r && r.price_band)) + "</td>" +
          '<td class="num">' + (r && r.neutral ? inr(r.neutral.blended) : "-") + "</td>" +
          '<td class="num">' + signed(up) + "</td>" +
          "<td>" + (r ? callBadge(r.call) : '<span class="badge b-plain">Not covered</span>') + "</td>" +
          '<td class="hide-sm">' + (r && r.pdf ? '<a href="companies/' + encodeURIComponent(r.slug) + "/" + encodeURIComponent(r.pdf) + '" target="_blank" rel="noopener">PDF</a>' : "") + "</td></tr>";
      }).join("") : '<tr><td colspan="7"><div class="empty">No closed issues in the last 30 days.</div></td></tr>';
    });
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
        ["Price band", m.price_band || "Not announced"], ["Lot size", m.lot_size], ["Subscription opens", m.open_date && date(m.open_date)],
        ["Subscription closes", m.close_date && date(m.close_date)], ["Listing", m.listing_date && date(m.listing_date)],
        ["Stage of business", m.business_stage]].concat(companyPeRows(m.company_pe)).concat([ ["Report depth", m.depth], ["Valuation reference", m.reference_note], ["Exit route underwritten", m.exit_route]]);
      $("facts").innerHTML = kv.map(function (p) { return "<dt>" + esc(p[0]) + "</dt><dd>" + (p[1] == null || p[1] === "" ? "-" : esc(p[1])) + "</dd>"; }).join("");
      var files = m.files || {}, dl = [];
      [["pdf", "Full report (.pdf)"], ["screening", "Screening checklist (.xlsx)"], ["anchor", "Anchor & QIB economics (.xlsx)"], ["valuation", "Comps & valuation model (.xlsx)"],
        ["note", "Report text (.md)"]].forEach(function (f) {
        if (files[f[0]]) dl.push('<a class="btn" href="' + base + encodeURIComponent(files[f[0]]) + '" download>' + f[1] + "</a>");
      });
      if (safeUrl(m.doc_url)) dl.push('<a class="btn btn--ghost" href="' + safeUrl(m.doc_url) + '" target="_blank" rel="noopener">Offer document (source)</a>');
      $("downloads").innerHTML = dl.join("") || '<span class="muted">No files yet.</span>';
      var toHtml = function (t) {
        if (window.marked && window.DOMPurify) return window.DOMPurify.sanitize(window.marked.parse(t));
        return "<pre style=\"white-space:pre-wrap\">" + esc(t) + "</pre>";
      };
      var notePromise = files.note
        ? fetch(base + files.note + "?t=" + Date.now(), { cache: "no-store" }).then(function (r) { return r.ok ? r.text() : ""; }).catch(function () { return ""; })
        : Promise.resolve("");
      Promise.all([getJSON(base + "charts.json").catch(function () { return null; }), notePromise]).then(function (r) {
        var ch = r[0], noteMd = r[1];
        var showFullNote = function (structured) {
          // a note written in the nine-part order is shown inside the sections; older notes appear in full below
          $("d-note").style.display = structured ? "none" : "";
          $("note").innerHTML = noteMd ? toHtml(noteMd) : '<p class="muted">Note not yet written.</p>';
        };
        if (!ch) { $("dash").innerHTML = '<p class="muted">Dashboard not available for this issuer.</p>'; showFullNote(false); return; }
        var draw = function () { return window.IPODashboard.render($("dash"), ch, m, { note: noteMd, md: toHtml }); };
        showFullNote(draw());
        var w = window.innerWidth, t;
        window.addEventListener("resize", function () {
          if (Math.abs(window.innerWidth - w) < 40) return;
          w = window.innerWidth; clearTimeout(t); t = setTimeout(draw, 200);
        });
      });
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
