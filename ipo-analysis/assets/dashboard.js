/* Issuer dashboard - renders companies/<slug>/charts.json (and the note) in the Fund's nine-part report order:
   1 Business, 2 Industry, 3 Moat and SWOT, 4 Management and governance, 5 Historical financials, 6 Outlook and projections,
   7 Valuation (DCF and P2P), 8 Areas to watch and growth drivers, 9 Conclusion, then an appendix.
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
  var PARTS = [
    [1, "Business of the company"], [2, "Industry outlook"], [3, "Moat and SWOT analysis"],
    [4, "Management analysis and governance"], [5, "Historical financials and ratios"], [6, "Future outlook and projections"],
    [7, "Valuation: DCF and peer comparison (P2P)"], [8, "Areas to watch and growth drivers"], [9, "Conclusion"]
  ];
  function chip(s) { var t = STATUS[s] || STATUS.OPEN; return '<span class="chip ' + t.cls + '"><b>' + t.icon + "</b>" + t.label + "</span>"; }
  function section(root, id, title, sub) {
    var s = document.createElement("section"); s.className = "dash-sec"; s.id = id;
    s.innerHTML = '<div class="dash-h"><h2>' + esc(title) + "</h2>" + (sub ? '<p class="sub">' + esc(sub) + "</p>" : "") + "</div>";
    root.appendChild(s); return s;
  }
  function card(parent, cls) { var d = document.createElement("div"); d.className = "viz-card " + (cls || ""); parent.appendChild(d); return d; }
  function grid(parent, cls) { var d = document.createElement("div"); d.className = "dash-grid " + (cls || ""); parent.appendChild(d); return d; }

  /* Split note.md at its "## " headings: "## 1. ..." to "## 9. ..." are the nine parts, "## Appendix ..." the appendix. */
  function splitNote(md) {
    var out = { intro: "", parts: {}, appendix: [], structured: false };
    if (!md) return out;
    var chunks = md.split(/^## /m);
    out.intro = chunks.shift().replace(/^# .*$/m, "").trim();
    chunks.forEach(function (c) {
      var nl = c.indexOf("\n"), title = (nl < 0 ? c : c.slice(0, nl)).trim(), body = nl < 0 ? "" : c.slice(nl + 1).trim();
      var m = /^([1-9])\.\s/.exec(title);
      if (m) { out.parts[m[1]] = body; out.structured = true; }
      else if (/^appendix/i.test(title)) out.appendix.push({ title: title, body: body });
    });
    return out;
  }
  function dropSub(md, title) {          // remove one "### title" subsection when a chart or panel replaces it
    if (!md) return md;
    var re = new RegExp("^### " + title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "[\\s\\S]*?(?=^### |(?![\\s\\S]))", "m");
    return md.replace(re, "");
  }
  function prose(parent, md, toHtml) {
    if (!md || !toHtml) return;
    var a = document.createElement("article"); a.className = "note note--sec"; a.innerHTML = toHtml(md); parent.appendChild(a);
  }
  function decisionStrip(parent, meta) {
    var strip = document.createElement("div"); strip.className = "decision";
    strip.innerHTML = '<div class="decision__call"><span class="lbl">Call</span><span class="val">' + esc(meta.call || "Pending") + "</span>" +
      '<span class="lbl">Stage</span><span class="val sm">' + esc((meta.platform || "") + " · " + (meta.stage || "")) + "</span></div>" +
      '<div class="decision__head">' + esc(meta.headline || "") + "</div>" +
      (meta.business_stage ? '<div class="decision__score"><span class="lbl">Business stage</span> ' + esc(meta.business_stage) + "</div>" : "");
    parent.appendChild(strip);
  }

  function render(root, ch, meta, opt) {
    opt = opt || {};
    var W = opt.chartWidth;              // fixed width for print; undefined = fit container
    var toHtml = opt.md, note = splitNote(opt.note || "");
    root.innerHTML = "";
    var h = ch.history || {}, yrs = h.years || [], v = ch.valuation || {}, sc = v.scenarios || {}, d = ch.dcf || {};
    var P = function (n) { return note.parts[String(n)]; };
    var S = {};
    var open = function (n, sub) { S[n] = section(root, "d-s" + n, n + ". " + PARTS[n - 1][1], sub); return S[n]; };

    /* ---------- at a glance */
    var g0 = section(root, "d-glance", "At a glance", "The call, the key numbers and the basis of the analysis.");
    decisionStrip(g0, meta);
    var tiles = document.createElement("div"); tiles.className = "tiles";
    tiles.innerHTML = (ch.kpis || []).map(function (k) {
      var sub = k.sub ? '<div class="tile__sub">' + esc(k.sub) + (k.subval != null ? ": <b>" + fmt(k.subval, k.subfmt) + "</b>" : "") + "</div>" : "";
      return '<div class="tile"><div class="tile__lbl">' + esc(k.label) + "</div><div class=\"tile__val\">" + fmt(k.value, k.fmt) + "</div>" + sub + "</div>";
    }).join("");
    g0.appendChild(tiles);
    prose(g0, note.intro, toHtml);

    /* ---------- 1, 2: business and industry (written analysis) */
    if (P(1)) prose(open(1), P(1), toHtml);
    if (P(2)) prose(open(2), P(2), toHtml);

    /* ---------- 3: moat and SWOT */
    var sw = ch.swot || meta.swot;
    if (P(3) || sw) {
      var s3 = open(3);
      var moat = P(3);
      if (sw) moat = dropSub(moat, "SWOT");   // the quadrant below replaces the SWOT table
      prose(s3, moat, toHtml);
      if (sw) {
        var q = document.createElement("div"); q.className = "swot";
        [["strengths", "Strengths"], ["weaknesses", "Weaknesses"], ["opportunities", "Opportunities"], ["threats", "Threats"]].forEach(function (p) {
          q.innerHTML += '<div class="swot__q swot--' + p[0] + '"><h3>' + p[1] + "</h3><ul>" + (sw[p[0]] || []).map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul></div>";
        });
        s3.appendChild(q);
      }
    }

    /* ---------- 4: management and governance */
    if (P(4)) prose(open(4), P(4), toHtml);

    /* ---------- 5: historical financials and ratios */
    var s5 = open(5, "Restated figures, Rs crore. Hover a mark for its value; open \"Data table\" under any chart for the numbers.");
    var eq = ch.earnings_quality;
    prose(s5, eq ? dropSub(P(5), "Is the reported P/E right?") : P(5), toHtml);
    if (eq) {
      var ec = card(s5, "wide"), yy = eq.years || [];
      ec.innerHTML = '<div class="viz-title">Is the reported P/E right? Earnings quality at Rs ' + fmt(eq.price) + "</div>" +
        '<p class="note-s"><b>' + esc(eq.verdict) + "</b></p>" +
        '<table class="mini"><thead><tr><th>Basis</th><th>PAT (Rs cr)</th><th>EPS (Rs)</th><th>P/E</th></tr></thead><tbody>' +
        (eq.rows || []).map(function (r) { return "<tr><td>" + esc(r.basis) + "</td><td>" + fmt(r.pat) + "</td><td>" + fmt(r.eps) + "</td><td><b>" + (r.pe != null ? fmt(r.pe, "x") : "n.m.") + "</b></td></tr>"; }).join("") +
        "</tbody></table>" +
        '<div class="viz-title" style="margin-top:12px">Items found (pre-tax, Rs crore; negative reduces profit)</div><div class="tbl-wrap"><table class="mini"><thead><tr><th>Item and reason</th>' +
        yy.map(function (y) { return "<th>" + esc(y) + "</th>"; }).join("") + "<th>In adjusted P/E</th><th>Confidence</th><th>" + esc(yy[yy.length - 1] || "") + " P/E if applied</th><th>Page</th></tr></thead><tbody>" +
        (eq.adjustments || []).map(function (a) {
          return "<tr><td><b>" + esc(a.item) + "</b>" + (a.reason ? "<br>" + esc(a.reason) : "") + "</td>" + (a.pre_tax || []).map(function (x) { return "<td>" + fmt(x) + "</td>"; }).join("") +
            "<td>" + (a.include ? chip("WATCH").replace("Watch", "Yes") : "No (information)") + "</td><td>" + esc(a.confidence || "") + "</td><td>" + (a.pe_if_applied != null ? fmt(a.pe_if_applied, "x") : "n.m.") + "</td><td>" + esc(a.page || "") + "</td></tr>";
        }).join("") + "</tbody></table></div>" +
        ((eq.checked || []).length ? '<div class="viz-title" style="margin-top:12px">Also checked, no adjustment needed</div><ul class="focus-list">' +
          eq.checked.map(function (c) { return "<li>" + chip("PASS") + " " + esc(c) + "</li>"; }).join("") + "</ul>" : "");
    }
    var g5 = grid(s5);
    K.columns(card(g5), { title: "Revenue from operations", subtitle: "Rs crore", categories: yrs, series: [{ name: "Revenue", values: h.revenue }], fmt: "int", labelAll: true, width: W });
    K.columns(card(g5), { title: "EBITDA and PAT", subtitle: "Rs crore", categories: yrs, series: [{ name: "EBITDA", values: h.ebitda }, { name: "PAT", values: h.pat }], fmt: "int", labelLast: true, width: W });
    K.lines(card(g5), { title: "Margins", subtitle: "% of revenue", categories: yrs, series: [{ name: "EBITDA margin", values: h.ebitda_margin }, { name: "PAT margin", values: h.pat_margin }], fmt: "pct", axisFmt: "pct0", width: W });
    K.columns(card(g5), { title: "Profit and operating cash flow", subtitle: "Rs crore", categories: yrs,
      series: [{ name: "PAT", values: h.pat }, { name: "Cash flow from operations", values: h.cfo }], fmt: "int", labelLast: true, width: W });
    K.columns(card(g5), { title: "Working capital", subtitle: "Rs crore, year end", categories: yrs,
      series: [{ name: "Inventory", values: h.inventory }, { name: "Receivables", values: h.receivables }, { name: "Payables", values: h.payables }], fmt: "int", width: W });
    if (h.volume) K.columns(card(g5), { title: "Volume", subtitle: h.volume_unit || "", categories: yrs, series: [{ name: "Volume", values: h.volume }], fmt: "int", labelAll: true, width: W });
    else K.lines(card(g5), { title: "Net working capital", subtitle: "% of revenue", categories: yrs, series: [{ name: "NWC % revenue", values: h.nwc_pct }], fmt: "pct", axisFmt: "pct0", width: W });

    /* ---------- 6: future outlook and projections */
    var s6 = open(6, "Neutral case from the valuation model; Bear and Bull are in the valuation workbook.");
    prose(s6, P(6), toHtml);
    if ((d.revenue || []).length) {
      var g6 = grid(s6);
      K.columns(card(g6), { title: "Projected revenue and EBITDA (Neutral)", subtitle: "Rs crore; Y0 is the latest audited year", categories: d.years || [],
        series: [{ name: "Revenue", values: d.revenue }, { name: "EBITDA", values: d.ebitda }], fmt: "int", labelLast: true, width: W });
      K.columns(card(g6), { title: "Projected free cash flow to firm (Neutral)", subtitle: "Rs crore", categories: d.years || [], series: [{ name: "FCFF", values: d.fcff }], fmt: "int", labelAll: true, width: W });
    }

    /* ---------- 7: valuation, DCF and P2P */
    var s7 = open(7, "DCF and peer values shown separately, then blended. Reference: " + (v.reference_note || "price band"));
    var marks = [{ label: "Reference", value: v.reference }];
    if (v.floor && v.cap && v.floor !== v.cap) marks = [{ label: "Floor", value: v.floor }, { label: "Cap", value: v.cap }];
    K.football(card(s7, "wide"), { title: "Value per share (Bear – Neutral – Bull)", subtitle: "Bar spans Bear to Bull; dot is Neutral. Vertical lines mark the price band.",
      rows: [
        { label: "DCF", lo: (sc.bear || {}).dcf, mid: (sc.neutral || {}).dcf, hi: (sc.bull || {}).dcf, color: K.colors.s1 },
        { label: "Peer relative", lo: null, mid: (sc.neutral || {}).relative, hi: null, color: K.colors.s3 },
        { label: "Fair value (blend)", lo: (sc.bear || {}).blended, mid: (sc.neutral || {}).blended, hi: (sc.bull || {}).blended, color: K.colors.s2 }
      ], marks: marks, width: W });
    var peers = ch.peers || [];
    if (peers.length) {
      var gp = grid(s7);
      var med = function (key) { var a = peers.filter(function (p) { return !p.issuer && p[key] != null; }).map(function (p) { return p[key]; }).sort(function (x, y) { return x - y; }); return a.length ? (a.length % 2 ? a[(a.length - 1) / 2] : (a[a.length / 2 - 1] + a[a.length / 2]) / 2) : null; };
      K.hbars(card(gp), { title: "Peer P/E", subtitle: "Issuer at the reference price (orange) vs listed peers", items: peers.map(function (p) { return { label: p.name, value: p.pe, highlight: p.issuer }; }), fmt: "x", ref: med("pe"), refLabel: "peer median", labelWidth: 210, width: W });
      K.hbars(card(gp), { title: "Peer P/B", subtitle: "Issuer on post-issue net worth", items: peers.map(function (p) { return { label: p.name, value: p.pb, highlight: p.issuer }; }), fmt: "x", ref: med("pb"), refLabel: "peer median", labelWidth: 210, width: W });
    }
    var g7 = grid(s7);
    var sumc = card(g7);
    sumc.innerHTML = '<div class="viz-title">Scenario summary</div><table class="mini"><thead><tr><th>Rs/share</th><th>DCF</th><th>Relative</th><th>Fair value</th><th>vs reference</th></tr></thead><tbody>' +
      ["bear", "neutral", "bull"].map(function (k) { var x = sc[k] || {}; return "<tr><td>" + k.charAt(0).toUpperCase() + k.slice(1) + "</td><td>" + fmt(x.dcf, "rs") + "</td><td>" + fmt(x.relative, "rs") + "</td><td><b>" + fmt(x.blended, "rs") + "</b></td><td>" + fmt(x.upside_cap, "pct") + "</td></tr>"; }).join("") +
      "</tbody></table><div class=\"kv2\"><span>WACC</span><b>" + fmt(v.wacc, "pct") + "</b><span>Terminal value share of EV</span><b>" + fmt(v.tv_share, "pct") + "</b></div>" +
      '<div class="viz-title" style="margin-top:12px">Reverse DCF: what the reference price assumes</div><table class="mini"><thead><tr><th>Lever</th><th>Required</th><th>Actual</th></tr></thead><tbody>' +
      ((v.reverse || {}).levers || []).map(function (l) { var r = typeof l.required === "number" ? fmt(l.required, "pct") : l.required; return "<tr><td>" + esc(String(l.label || "").replace(/^Lever \d - /, "")) + "</td><td>" + esc(r) + "</td><td>" + fmt(l.actual, "pct") + "</td></tr>"; }).join("") +
      "</tbody></table>" + ((v.reverse || {}).sentence ? '<p class="note-s">' + esc(v.reverse.sentence) + "</p>" : "");
    var sv = ch.sensitivity || {};
    if (sv.wacc_g) K.heatmap(card(g7), { title: "Sensitivity: WACC vs terminal growth", subtitle: "DCF value per share (Rs). Blue above, red below the reference.", rows: sv.wacc_g.rows, cols: sv.wacc_g.cols, values: sv.wacc_g.values, rowFmt: "pct", colFmt: "pct", rowLabel: "WACC", colLabel: "Terminal growth", ref: v.reference, center: [2, 2], width: W });
    if (sv.nwc_margin) K.heatmap(card(g7), { title: "Sensitivity: working capital vs EBITDA margin", subtitle: "DCF value per share (Rs).", rows: sv.nwc_margin.rows, cols: sv.nwc_margin.cols, values: sv.nwc_margin.values, rowFmt: "pct0", colFmt: "pct", rowLabel: "NWC % rev", colLabel: "EBITDA margin", ref: v.reference, center: [2, 2], width: W });
    prose(s7, P(7), toHtml);

    /* ---------- 8, 9: areas to watch, conclusion */
    if (P(8)) prose(open(8), P(8), toHtml);
    var s9 = open(9);
    decisionStrip(s9, meta);
    prose(s9, P(9), toHtml);

    /* ---------- appendix: offer, merchant bankers, diligence checks, note appendices */
    var sa = section(root, "d-appx", "Appendix", "Offer structure and lock-ins, lead managers' track record, diligence checks and supporting detail.");
    var of = ch.offer || {};
    if ((of.structure || []).length) {
      K.stack(card(sa, "wide"), { title: "Issue split by investor category (Rs " + fmt(of.issue_cr, "int") + " cr net offer)", subtitle: "The open anchor pool is the part an AIF competes for; allocation is discretionary.", segments: of.structure, width: W });
      if ((of.overhang || []).length) {
        var oc = card(sa, "wide");
        oc.innerHTML = '<div class="viz-title">Lock-in expiries known from the offer document</div><table class="mini"><thead><tr><th>Holder</th><th>Shares (lakh)</th><th>Lock-in (days from allotment)</th></tr></thead><tbody>' +
          of.overhang.map(function (o) { return "<tr><td>" + esc(o.label) + "</td><td>" + fmt(o.shares_lakh) + "</td><td>" + esc(o.days) + "</td></tr>"; }).join("") + "</tbody></table>";
      }
    }
    var b = ch.brlm || {};
    if ((b.bankers || []).length) {
      var gb = grid(sa);
      b.bankers.forEach(function (bk) {
        var cc = card(gb);
        var sm = bk.summary || {}, rows = Object.keys(sm).map(function (y) { var x = sm[y] || {}; return "<tr><td>" + esc(y) + "</td><td>" + (x.ipos != null ? x.ipos : "–") + "</td><td>" + (x.amount_rs_m ? fmt(x.amount_rs_m / 10, "int") : "–") + "</td></tr>"; }).join("");
        cc.innerHTML = '<div class="viz-title">Lead manager: ' + esc(bk.name) + '</div><p class="note-s"><b>Listed:</b> ' + esc(bk.listed || "–") + "<br><b>Owner:</b> " + esc(bk.owner || "–") + "</p>" +
          '<table class="mini"><thead><tr><th>Financial year</th><th>IPOs</th><th>Raised (Rs cr)</th></tr></thead><tbody>' + rows + "</tbody></table>";
      });
      if ((b.issues || []).length)
        K.hbars(card(sa, "wide"), { title: "Lead managers' recent issues: listing-day open vs issue price", subtitle: "Offer-document data", items: b.issues.map(function (i) { return { label: i.issuer.replace(/ (Limited|Ltd)$/, ""), value: i.listing_gain, note: i.sector + (i.d30 != null ? " · 30-day: " + fmt(i.d30, "pct") : "") }; }), fmt: "pct", axisFmt: "pct0", diverging: true, labelWidth: 230, width: W });
    }
    if ((ch.scorecard || []).length) {
      var tb = card(sa, "wide");
      tb.innerHTML = '<div class="viz-title">Diligence checks</div><div class="tbl-wrap"><table class="score"><thead><tr><th>#</th><th>Check</th><th>Result</th><th>Finding</th><th>Page</th></tr></thead><tbody>' +
        ch.scorecard.map(function (r) { return "<tr><td>" + esc(r.id) + "</td><td>" + esc(r.check) + "</td><td>" + chip(r.status) + "</td><td>" + esc(r.finding || "") + "</td><td>" + esc(r.page || "") + "</td></tr>"; }).join("") + "</tbody></table></div>" +
        '<p class="note-s">Under the Fund\'s rules a check is marked Fail only for a material issue; normal features of the business are Watch items, covered in part 8.</p>';
    }
    note.appendix.forEach(function (a) {
      var c2 = card(sa, "wide"); c2.innerHTML = '<div class="viz-title">' + esc(a.title) + "</div>"; prose(c2, a.body, toHtml);
    });
    return note.structured;
  }

  G.IPODashboard = { render: render, chip: chip, parts: PARTS };
})(window);
