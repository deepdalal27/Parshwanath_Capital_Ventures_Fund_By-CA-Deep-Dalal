/* Issuer dashboard - renders companies/<slug>/charts.json into decision-first sections.
   Used by view.html (website) and report.html (PDF). Requires charts.js. */
(function (G) {
  "use strict";
  var K = G.IPOCharts, fmt = K.fmt, esc = K.esc;
  var STATUS = {
    FAIL: { cls: "st-crit", icon: "✕", label: "Fail" }, WATCH: { cls: "st-warn", icon: "!", label: "Watch" },
    PASS: { cls: "st-good", icon: "✓", label: "Pass" }, OPEN: { cls: "st-open", icon: "○", label: "Open" },
    "N.A.": { cls: "st-na", icon: "–", label: "N.A." }, GUARD: { cls: "st-serious", icon: "▲", label: "Model guard" },
    GAP: { cls: "st-open", icon: "?", label: "Data gap" }
  };
  function chip(s) { var t = STATUS[s] || STATUS.OPEN; return '<span class="chip ' + t.cls + '"><b>' + t.icon + "</b>" + t.label + "</span>"; }
  function section(root, id, title, sub) {
    var s = document.createElement("section"); s.className = "dash-sec"; s.id = id;
    s.innerHTML = '<div class="dash-h"><h2>' + esc(title) + "</h2>" + (sub ? '<p class="sub">' + esc(sub) + "</p>" : "") + "</div>";
    root.appendChild(s); return s;
  }
  function card(parent, cls) { var d = document.createElement("div"); d.className = "viz-card " + (cls || ""); parent.appendChild(d); return d; }
  function grid(parent, cls) { var d = document.createElement("div"); d.className = "dash-grid " + (cls || ""); parent.appendChild(d); return d; }

  function render(root, ch, meta, opt) {
    opt = opt || {};
    var W = opt.chartWidth;              // fixed width for print; undefined = fit container
    root.innerHTML = "";
    var h = ch.history || {}, yrs = h.years || [], v = ch.valuation || {}, sc = v.scenarios || {};

    /* ---------- 1. decision strip + KPI tiles */
    var s1 = section(root, "d-decision", "Decision summary", "Key numbers and the call, with every figure traceable to the note and the workbooks.");
    var c = ch.counts || {};
    var strip = document.createElement("div"); strip.className = "decision";
    strip.innerHTML = '<div class="decision__call"><span class="lbl">Call</span><span class="val">' + esc(meta.call || "Pending") + "</span>" +
      '<span class="lbl">Stage</span><span class="val sm">' + esc((meta.platform || "") + " · " + (meta.stage || "")) + "</span></div>" +
      '<div class="decision__head">' + esc(meta.headline || "") + "</div>" +
      '<div class="decision__score">' + chip("FAIL") + " " + (c.fail || 0) + "&nbsp;&nbsp;" + chip("WATCH") + " " + (c.watch || 0) +
      "&nbsp;&nbsp;" + chip("PASS") + " " + (c.pass || 0) + "&nbsp;&nbsp;" + chip("OPEN") + " " + (c.open || 0) + "</div>";
    s1.appendChild(strip);
    var tiles = document.createElement("div"); tiles.className = "tiles";
    tiles.innerHTML = (ch.kpis || []).map(function (k) {
      var tone = k.tone ? " tone-" + k.tone : "";
      var sub = k.sub ? '<div class="tile__sub">' + esc(k.sub) + (k.subval != null ? ": <b>" + fmt(k.subval, k.subfmt) + "</b>" : "") + "</div>" : "";
      var badge = k.tone === "bad" ? chip("WATCH") : k.tone === "good" ? chip("PASS") : "";
      return '<div class="tile' + tone + '"><div class="tile__lbl">' + esc(k.label) + "</div><div class=\"tile__val\">" + fmt(k.value, k.fmt) + "</div>" + sub + (badge ? '<div class="tile__badge">' + badge + "</div>" : "") + "</div>";
    }).join("");
    s1.appendChild(tiles);

    /* ---------- 2. where to focus */
    var s2 = section(root, "d-focus", "Where to focus", "Items ranked by severity: failed checks, then watch items, model guards and open data gaps. The right column lists what checked out.");
    var g2 = grid(s2);
    var f1 = card(g2, "focus");
    f1.innerHTML = '<div class="viz-title">Focus here (' + (ch.focus || []).length + ")</div><ol class=\"focus-list\">" + (ch.focus || []).map(function (f) {
      return "<li>" + chip(f.level) + " <b>" + esc(f.title) + "</b>" + (f.page ? ' <span class="pg">' + esc(f.page) + "</span>" : "") + "<div>" + esc(f.detail) + "</div></li>";
    }).join("") + "</ol>";
    var f2 = card(g2, "comfort");
    f2.innerHTML = '<div class="viz-title">Comfort points (' + (ch.comfort || []).length + ")</div><ul class=\"focus-list\">" + (ch.comfort || []).map(function (f) {
      return "<li>" + chip("PASS") + " <b>" + esc(f.title) + "</b>" + (f.page ? ' <span class="pg">' + esc(f.page) + "</span>" : "") + "<div>" + esc(f.detail) + "</div></li>";
    }).join("") + "</ul>";

    /* ---------- 3. scorecard */
    var s3 = section(root, "d-score", "Forensic scorecard", "Ten forensic checks and seven regulatory checks.");
    var tb = document.createElement("div"); tb.className = "tbl-wrap";
    tb.innerHTML = "<table class=\"score\"><thead><tr><th>#</th><th>Check</th><th>Result</th><th>Finding</th><th>Page</th></tr></thead><tbody>" +
      (ch.scorecard || []).map(function (r) { return "<tr><td>" + esc(r.id) + "</td><td>" + esc(r.check) + "</td><td>" + chip(r.status) + "</td><td>" + esc(r.finding || "") + "</td><td>" + esc(r.page || "") + "</td></tr>"; }).join("") + "</tbody></table>";
    s3.appendChild(tb);

    /* ---------- 4. financial performance */
    var s4 = section(root, "d-fin", "Financial performance", "Restated figures, Rs crore. Hover a mark for its value; open \"Data table\" under any chart for the numbers.");
    var g4 = grid(s4);
    K.columns(card(g4), { title: "Revenue from operations", subtitle: "Rs crore", categories: yrs, series: [{ name: "Revenue", values: h.revenue }], fmt: "int", labelAll: true, width: W });
    K.columns(card(g4), { title: "EBITDA and PAT", subtitle: "Rs crore", categories: yrs, series: [{ name: "EBITDA", values: h.ebitda }, { name: "PAT", values: h.pat }], fmt: "int", labelLast: true, width: W });
    K.lines(card(g4), { title: "Margins", subtitle: "% of revenue", categories: yrs, series: [{ name: "EBITDA margin", values: h.ebitda_margin }, { name: "PAT margin", values: h.pat_margin }], fmt: "pct", axisFmt: "pct0", width: W });
    K.columns(card(g4), { title: "Cash conversion: PAT vs operating cash flow", subtitle: "Rs crore. Profit that does not become cash shows as the gap.", categories: yrs,
      series: [{ name: "PAT", values: h.pat }, { name: "Cash flow from operations", values: h.cfo }], fmt: "int", labelLast: true, width: W });
    K.columns(card(g4), { title: "Working capital build-up", subtitle: "Rs crore, year end", categories: yrs,
      series: [{ name: "Inventory", values: h.inventory }, { name: "Receivables", values: h.receivables }, { name: "Payables", values: h.payables }], fmt: "int", width: W });
    if (h.volume) K.columns(card(g4), { title: "Volume", subtitle: h.volume_unit || "", categories: yrs, series: [{ name: "Volume", values: h.volume }], fmt: "int", labelAll: true, width: W });
    else K.lines(card(g4), { title: "Net working capital", subtitle: "% of revenue", categories: yrs, series: [{ name: "NWC % revenue", values: h.nwc_pct }], fmt: "pct", axisFmt: "pct0", width: W });

    /* ---------- 5. valuation */
    var s5 = section(root, "d-val", "Valuation", "DCF and peer-relative values shown separately, then blended 60:40. Reference: " + (v.reference_note || "price band"));
    var marks = [{ label: "Reference", value: v.reference }];
    if (v.floor && v.cap && v.floor !== v.cap) marks = [{ label: "Floor", value: v.floor }, { label: "Cap", value: v.cap }];
    K.football(card(s5, "wide"), { title: "Valuation range per share (Bear – Neutral – Bull)", subtitle: "Bar spans Bear to Bull; dot is Neutral. Vertical line is the reference price.",
      rows: [
        { label: "DCF", lo: (sc.bear || {}).dcf, mid: (sc.neutral || {}).dcf, hi: (sc.bull || {}).dcf, color: K.colors.s1 },
        { label: "Peer relative", lo: null, mid: (sc.neutral || {}).relative, hi: null, color: K.colors.s3 },
        { label: "Blended 60:40", lo: (sc.bear || {}).blended, mid: (sc.neutral || {}).blended, hi: (sc.bull || {}).blended, color: K.colors.s2 }
      ], marks: marks, width: W });
    var g5 = grid(s5);
    var sumc = card(g5);
    sumc.innerHTML = '<div class="viz-title">Scenario summary</div><table class="mini"><thead><tr><th>Rs/share</th><th>DCF</th><th>Relative</th><th>Blended</th><th>vs reference</th></tr></thead><tbody>' +
      ["bear", "neutral", "bull"].map(function (k) { var x = sc[k] || {}; return "<tr><td>" + k.charAt(0).toUpperCase() + k.slice(1) + "</td><td>" + fmt(x.dcf, "rs") + "</td><td>" + fmt(x.relative, "rs") + "</td><td><b>" + fmt(x.blended, "rs") + "</b></td><td>" + fmt(x.upside_cap, "pct") + "</td></tr>"; }).join("") +
      "</tbody></table><div class=\"kv2\"><span>WACC</span><b>" + fmt(v.wacc, "pct") + "</b><span>Terminal value share of EV</span><b>" + fmt(v.tv_share, "pct") + "</b></div>" +
      '<div class="viz-title" style="margin-top:12px">Reverse DCF: what the reference price needs</div><table class="mini"><thead><tr><th>Lever</th><th>Required</th><th>Actual</th></tr></thead><tbody>' +
      ((v.reverse || {}).levers || []).map(function (l) { var r = typeof l.required === "number" ? fmt(l.required, "pct") : l.required; return "<tr><td>" + esc(String(l.label || "").replace(/^Lever \d - /, "")) + "</td><td>" + esc(r) + "</td><td>" + fmt(l.actual, "pct") + "</td></tr>"; }).join("") +
      "</tbody></table>" + ((v.reverse || {}).sentence ? '<p class="note-s">' + esc(v.reverse.sentence) + "</p>" : "");
    var d = ch.dcf || {};
    K.columns(card(g5), { title: "DCF projection (Neutral): free cash flow to firm", subtitle: "Rs crore; Y0 is the latest audited year", categories: d.years || [], series: [{ name: "FCFF", values: d.fcff }], fmt: "int", labelAll: true, width: W });
    var sv = ch.sensitivity || {};
    if (sv.wacc_g) K.heatmap(card(g5), { title: "Sensitivity: WACC vs terminal growth", subtitle: "Value per share (Rs). Blue above, red below the reference.", rows: sv.wacc_g.rows, cols: sv.wacc_g.cols, values: sv.wacc_g.values, rowFmt: "pct", colFmt: "pct", rowLabel: "WACC", colLabel: "Terminal growth", ref: v.reference, center: [2, 2], width: W });
    if (sv.nwc_margin) K.heatmap(card(g5), { title: "Sensitivity: working capital vs EBITDA margin", subtitle: "Value per share (Rs). The lever that moves value most deserves the most diligence.", rows: sv.nwc_margin.rows, cols: sv.nwc_margin.cols, values: sv.nwc_margin.values, rowFmt: "pct0", colFmt: "pct", rowLabel: "NWC % rev", colLabel: "EBITDA margin", ref: v.reference, center: [2, 2], width: W });
    var peers = ch.peers || [];
    if (peers.length) {
      var med = function (key) { var a = peers.filter(function (p) { return !p.issuer && p[key] != null; }).map(function (p) { return p[key]; }).sort(function (x, y) { return x - y; }); return a.length ? (a.length % 2 ? a[(a.length - 1) / 2] : (a[a.length / 2 - 1] + a[a.length / 2]) / 2) : null; };
      K.hbars(card(g5), { title: "Peer P/E", subtitle: "Issuer at reference price (orange) vs listed peers named in the offer document", items: peers.map(function (p) { return { label: p.name, value: p.pe, highlight: p.issuer }; }), fmt: "x", ref: med("pe"), refLabel: "peer median", labelWidth: 210, width: W });
      K.hbars(card(g5), { title: "Peer P/B", subtitle: "Issuer on post-issue net worth", items: peers.map(function (p) { return { label: p.name, value: p.pb, highlight: p.issuer }; }), fmt: "x", ref: med("pb"), refLabel: "peer median", labelWidth: 210, width: W });
    }

    /* ---------- 6. offer */
    var of = ch.offer || {};
    if ((of.structure || []).length) {
      var s6 = section(root, "d-offer", "Offer structure and supply", "How the issue is split, where an AIF can bid as anchor, and shares that unlock after listing.");
      K.stack(card(s6, "wide"), { title: "Issue split by investor category (Rs " + fmt(of.issue_cr, "int") + " cr net offer)", subtitle: "The open anchor pool is the part an AIF competes for; allocation is discretionary.", segments: of.structure, width: W });
      if ((of.overhang || []).length) {
        var oc = card(s6, "wide");
        oc.innerHTML = '<div class="viz-title">Lock-in expiries known from the offer document</div><table class="mini"><thead><tr><th>Holder</th><th>Shares (lakh)</th><th>Lock-in (days from allotment)</th></tr></thead><tbody>' +
          of.overhang.map(function (o) { return "<tr><td>" + esc(o.label) + "</td><td>" + fmt(o.shares_lakh) + "</td><td>" + esc(o.days) + "</td></tr>"; }).join("") + "</tbody></table><p class=\"note-s\">Anchor tranches (30 / 90 days) and promoter lock-ins are dated once the RHP fixes the allotment date.</p>";
      }
    }

    /* ---------- 7. merchant bankers */
    var b = ch.brlm || {};
    if ((b.bankers || []).length) {
      var s7 = section(root, "d-brlm", "Merchant bankers", "Lead managers' recent issues: listing-day open vs issue price (offer-document data) and post-listing moves.");
      var g7 = grid(s7);
      b.bankers.forEach(function (bk) {
        var cc = card(g7);
        var sm = bk.summary || {}, rows = Object.keys(sm).map(function (y) { var x = sm[y] || {}; return "<tr><td>" + esc(y) + "</td><td>" + (x.ipos != null ? x.ipos : "–") + "</td><td>" + (x.amount_rs_m ? fmt(x.amount_rs_m / 10, "int") : "–") + "</td></tr>"; }).join("");
        cc.innerHTML = '<div class="viz-title">' + esc(bk.name) + '</div><p class="note-s"><b>Listed:</b> ' + esc(bk.listed || "–") + "<br><b>Owner:</b> " + esc(bk.owner || "–") + "</p>" +
          '<table class="mini"><thead><tr><th>Financial year</th><th>IPOs</th><th>Raised (Rs cr)</th></tr></thead><tbody>' + rows + "</tbody></table>";
      });
      if ((b.issues || []).length) {
        K.hbars(card(s7, "wide"), { title: "Listing-day open vs issue price", subtitle: "Recent issues handled by this offer's lead managers", items: b.issues.map(function (i) { return { label: i.issuer.replace(/ (Limited|Ltd)$/, ""), value: i.listing_gain, note: i.sector + (i.d30 != null ? " · 30-day: " + fmt(i.d30, "pct") : "") }; }), fmt: "pct", axisFmt: "pct0", diverging: true, labelWidth: 230, width: W });
        K.hbars(card(s7, "wide"), { title: "Issuers' revenue growth, FY24 → FY26", subtitle: "Secondary-source financials, unverified (see note)", items: b.issues.map(function (i) { return { label: i.issuer.replace(/ (Limited|Ltd)$/, ""), value: i.rev_growth, note: i.pat_growth != null ? "PAT growth " + fmt(i.pat_growth, "pct") : "PAT growth n.a." }; }), fmt: "pct", axisFmt: "pct0", diverging: true, labelWidth: 230, width: W });
      }
    }

    /* ---------- 8. SWOT */
    var sw = ch.swot || meta.swot;
    if (sw) {
      var s8 = section(root, "d-swot", "SWOT", "Each point carries its figure and page reference in the note.");
      var q = document.createElement("div"); q.className = "swot";
      [["strengths", "Strengths"], ["weaknesses", "Weaknesses"], ["opportunities", "Opportunities"], ["threats", "Threats"]].forEach(function (p) {
        q.innerHTML += '<div class="swot__q swot--' + p[0] + '"><h3>' + p[1] + "</h3><ul>" + (sw[p[0]] || []).map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul></div>";
      });
      s8.appendChild(q);
    }
  }

  G.IPODashboard = { render: render, chip: chip };
})(window);
