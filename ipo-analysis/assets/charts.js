/* IPO desk chart kit - dependency-free SVG charts shared by the website and the PDF report.
   Palette: validated categorical slots (blue, orange, aqua); status colours reserved for state;
   diverging blue <-> red with a neutral grey midpoint. Every chart ships a hover tooltip and a
   data-table twin, so no value is reachable by colour or hover alone. */
(function (G) {
  "use strict";
  var C = {
    s1: "#2a78d6", s2: "#eb6834", s3: "#1baf7a", ink: "#0b0b0b", ink2: "#52514e", muted: "#898781",
    grid: "#e1e0d9", base: "#c3c2b7", surface: "#ffffff", good: "#0ca30c", warn: "#fab219", serious: "#ec835a",
    crit: "#d03b3b", divLo: "#c23b3a", divMid: "#f0efec", divHi: "#256abf"
  };
  var SERIES = [C.s1, C.s2, C.s3];
  var NS = "http://www.w3.org/2000/svg";

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function fmt(v, f) {
    if (v == null || typeof v !== "number" || isNaN(v)) return "–";
    if (f === "pct") return (v * 100).toFixed(1) + "%";
    if (f === "pct0") return (v * 100).toFixed(0) + "%";
    if (f === "x") return v.toFixed(1) + "x";
    if (f === "rs") return "₹" + v.toLocaleString("en-IN", { maximumFractionDigits: 2 });
    if (f === "cr") return "₹" + v.toLocaleString("en-IN", { maximumFractionDigits: 0 }) + " cr";
    if (f === "int") return v.toLocaleString("en-IN", { maximumFractionDigits: 0 });
    return v.toLocaleString("en-IN", { maximumFractionDigits: 2 });
  }
  function niceTicks(lo, hi, n) {
    if (lo === hi) { hi = lo + 1; }
    var span = hi - lo, step = Math.pow(10, Math.floor(Math.log10(span / n))), err = span / n / step;
    step *= err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1;
    var t = [], v = Math.floor(lo / step) * step;
    for (var guard = 0; guard < 50; guard++) { t.push(+v.toFixed(10)); if (v >= hi - 1e-9) break; v += step; }
    return t;
  }
  function el(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function text(parent, x, y, s, o) {
    o = o || {};
    var t = el("text", { x: x, y: y, "font-size": o.size || 11, fill: o.fill || C.muted, "text-anchor": o.anchor || "start",
      "dominant-baseline": o.baseline || "auto", "font-weight": o.weight || 400 }, parent);
    t.textContent = s; return t;
  }
  /* column/bar path: 4px rounded data-end, square at the baseline */
  function barPath(x, y0, w, y1, r, horizontal) {
    if (!horizontal) {
      var up = y1 < y0, h = Math.abs(y1 - y0); r = Math.min(r, h, w / 2);
      if (h < 0.5) return "M" + x + "," + y0 + "h" + w;
      return up ? "M" + x + "," + y0 + "V" + (y1 + r) + "Q" + x + "," + y1 + " " + (x + r) + "," + y1 + "H" + (x + w - r) + "Q" + (x + w) + "," + y1 + " " + (x + w) + "," + (y1 + r) + "V" + y0 + "Z"
        : "M" + x + "," + y0 + "V" + (y1 - r) + "Q" + x + "," + y1 + " " + (x + r) + "," + y1 + "H" + (x + w - r) + "Q" + (x + w) + "," + y1 + " " + (x + w) + "," + (y1 - r) + "V" + y0 + "Z";
    }
    var right = y1 > y0, L = Math.abs(y1 - y0); r = Math.min(r, L, w / 2);   // here x is the band top, y0/y1 are x-coords
    if (L < 0.5) return "M" + y0 + "," + x + "v" + w;
    return right ? "M" + y0 + "," + x + "H" + (y1 - r) + "Q" + y1 + "," + x + " " + y1 + "," + (x + r) + "V" + (x + w - r) + "Q" + y1 + "," + (x + w) + " " + (y1 - r) + "," + (x + w) + "H" + y0 + "Z"
      : "M" + y0 + "," + x + "H" + (y1 + r) + "Q" + y1 + "," + x + " " + y1 + "," + (x + r) + "V" + (x + w - r) + "Q" + y1 + "," + (x + w) + " " + (y1 + r) + "," + (x + w) + "H" + y0 + "Z";
  }

  /* one shared tooltip */
  var tip;
  function tooltip(target, html) {
    target.style.cursor = "default";
    target.addEventListener("mousemove", function (ev) {
      if (!tip) { tip = document.createElement("div"); tip.className = "viz-tip"; document.body.appendChild(tip); }
      tip.innerHTML = html; tip.style.display = "block";
      var x = ev.clientX + 14, y = ev.clientY + 14;
      if (x + tip.offsetWidth > window.innerWidth - 8) x = ev.clientX - tip.offsetWidth - 14;
      tip.style.left = x + "px"; tip.style.top = y + "px";
    });
    target.addEventListener("mouseleave", function () { if (tip) tip.style.display = "none"; });
  }

  function frame(host, o) {
    host.innerHTML = "";
    host.classList.add("viz");
    if (o.title) { var h = document.createElement("div"); h.className = "viz-title"; h.textContent = o.title; host.appendChild(h); }
    if (o.subtitle) { var s = document.createElement("div"); s.className = "viz-sub"; s.textContent = o.subtitle; host.appendChild(s); }
    if (o.legend && o.legend.length > 1) {
      var lg = document.createElement("div"); lg.className = "viz-legend";
      lg.innerHTML = o.legend.map(function (l) { return '<span><i style="background:' + l.color + '"></i>' + esc(l.name) + "</span>"; }).join("");
      host.appendChild(lg);
    }
    var W = Math.max(280, Math.min(o.width || host.clientWidth || 560, 1100));
    var svg = el("svg", { viewBox: "0 0 " + W + " " + o.height, width: "100%", role: "img", "aria-label": o.title || "chart",
      style: "display:block;overflow:visible", "font-family": "Inter, system-ui, -apple-system, Segoe UI, sans-serif" });
    host.appendChild(svg);
    return { svg: svg, W: W };
  }
  function table(host, head, rows) {
    var d = document.createElement("details"); d.className = "viz-table";
    d.innerHTML = "<summary>Data table</summary><table><thead><tr>" + head.map(function (h) { return "<th>" + esc(h) + "</th>"; }).join("") +
      "</tr></thead><tbody>" + rows.map(function (r) { return "<tr>" + r.map(function (c, i) { return "<td" + (i ? ' class="n"' : "") + ">" + esc(c) + "</td>"; }).join("") + "</tr>"; }).join("") + "</tbody></table>";
    host.appendChild(d);
  }

  /* ---------------------------------------------------------------- grouped columns (handles negatives) */
  function columns(host, o) {
    var series = o.series.filter(function (s) { return s.values.some(function (v) { return v != null; }); });
    var H = o.height || 230, pad = { l: 56, r: 12, t: 16, b: 28 };
    var f = frame(host, { title: o.title, subtitle: o.subtitle, height: H, width: o.width, legend: series.map(function (s, i) { return { name: s.name, color: s.color || SERIES[i] }; }) });
    var svg = f.svg, W = f.W, all = [0];
    series.forEach(function (s) { s.values.forEach(function (v) { if (v != null) all.push(v); }); });
    var ticks = niceTicks(Math.min.apply(null, all), Math.max.apply(null, all), 4);
    var lo = ticks[0], hi = ticks[ticks.length - 1];
    var y = function (v) { return pad.t + (hi - v) / (hi - lo) * (H - pad.t - pad.b); };
    ticks.forEach(function (t) {
      el("line", { x1: pad.l, x2: W - pad.r, y1: y(t), y2: y(t), stroke: t === 0 ? C.base : C.grid, "stroke-width": 1 }, svg);
      text(svg, pad.l - 6, y(t), fmt(t, o.axisFmt || o.fmt), { anchor: "end", baseline: "middle", size: 10 });
    });
    var n = o.categories.length, band = (W - pad.l - pad.r) / n, k = series.length;
    var bw = Math.min(24, (band * 0.7 - (k - 1) * 2) / k);
    o.categories.forEach(function (cat, i) {
      var gx = pad.l + band * i + (band - (bw * k + 2 * (k - 1))) / 2;
      text(svg, pad.l + band * i + band / 2, H - 8, cat, { anchor: "middle", size: 11, fill: C.ink2 });
      series.forEach(function (s, j) {
        var v = s.values[i]; if (v == null) return;
        var x = gx + j * (bw + 2);
        var p = el("path", { d: barPath(x, y(0), bw, y(v), 4), fill: s.color || SERIES[j] }, svg);
        tooltip(p, "<b>" + esc(s.name) + "</b><br>" + esc(cat) + ": " + fmt(v, o.fmt));
        if (o.labelLast && i === n - 1 || o.labelAll) text(svg, x + bw / 2, v >= 0 ? y(v) - 5 : y(v) + 13, fmt(v, o.fmt), { anchor: "middle", size: 10, fill: C.ink2 });
      });
    });
    table(host, ["Series"].concat(o.categories), series.map(function (s) { return [s.name].concat(s.values.map(function (v) { return fmt(v, o.fmt); })); }));
  }

  /* ---------------------------------------------------------------- lines (one axis) */
  function lines(host, o) {
    var series = o.series.filter(function (s) { return s.values.some(function (v) { return v != null; }); });
    var H = o.height || 210, pad = { l: 52, r: 56, t: 16, b: 28 };
    var f = frame(host, { title: o.title, subtitle: o.subtitle, height: H, width: o.width, legend: series.map(function (s, i) { return { name: s.name, color: s.color || SERIES[i] }; }) });
    var svg = f.svg, W = f.W, all = [0];
    series.forEach(function (s) { s.values.forEach(function (v) { if (v != null) all.push(v); }); });
    var ticks = niceTicks(Math.min.apply(null, all), Math.max.apply(null, all), 4), lo = ticks[0], hi = ticks[ticks.length - 1];
    var y = function (v) { return pad.t + (hi - v) / (hi - lo) * (H - pad.t - pad.b); };
    var n = o.categories.length, x = function (i) { return pad.l + (n === 1 ? 0.5 : i / (n - 1)) * (W - pad.l - pad.r); };
    ticks.forEach(function (t) {
      el("line", { x1: pad.l, x2: W - pad.r, y1: y(t), y2: y(t), stroke: t === 0 ? C.base : C.grid, "stroke-width": 1 }, svg);
      text(svg, pad.l - 6, y(t), fmt(t, o.axisFmt || o.fmt), { anchor: "end", baseline: "middle", size: 10 });
    });
    o.categories.forEach(function (c, i) { text(svg, x(i), H - 8, c, { anchor: "middle", size: 11, fill: C.ink2 }); });
    series.forEach(function (s, j) {
      var col = s.color || SERIES[j], d = "";
      s.values.forEach(function (v, i) { if (v != null) d += (d ? "L" : "M") + x(i) + "," + y(v); });
      el("path", { d: d, fill: "none", stroke: col, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
      s.values.forEach(function (v, i) {
        if (v == null) return;
        var dot = el("circle", { cx: x(i), cy: y(v), r: 4.5, fill: col, stroke: C.surface, "stroke-width": 2 }, svg);
        var hit = el("circle", { cx: x(i), cy: y(v), r: 12, fill: "transparent" }, svg);
        tooltip(hit, "<b>" + esc(s.name) + "</b><br>" + esc(o.categories[i]) + ": " + fmt(v, o.fmt));
        if (i === s.values.length - 1) text(svg, x(i) + 9, y(v), fmt(v, o.fmt), { baseline: "middle", size: 10, fill: C.ink2 });
      });
    });
    table(host, ["Series"].concat(o.categories), series.map(function (s) { return [s.name].concat(s.values.map(function (v) { return fmt(v, o.fmt); })); }));
  }

  /* ---------------------------------------------------------------- horizontal bars (diverging if negatives) */
  function hbars(host, o) {
    if ((host.clientWidth || 600) < 480) o.labelWidth = Math.min(o.labelWidth || 190, 120);
    var items = o.items.filter(function (i) { return i.value != null; });
    var row = 30, pad = { l: o.labelWidth || 190, r: 64, t: o.ref != null ? 22 : 6, b: 22 }, H = pad.t + pad.b + row * items.length;
    var f = frame(host, { title: o.title, subtitle: o.subtitle, height: H, width: o.width });
    var svg = f.svg, W = f.W, vals = items.map(function (i) { return i.value; }).concat([0]);
    pad.l = Math.min(pad.l, Math.round(W * 0.42));
    var maxChars = Math.max(12, Math.floor(pad.l / 6.2));
    if (o.ref != null) vals.push(o.ref);
    var ticks = niceTicks(Math.min.apply(null, vals), Math.max.apply(null, vals), 4), lo = ticks[0], hi = ticks[ticks.length - 1];
    var x = function (v) { return pad.l + (v - lo) / (hi - lo) * (W - pad.l - pad.r); };
    ticks.forEach(function (t) {
      el("line", { x1: x(t), x2: x(t), y1: pad.t, y2: H - pad.b, stroke: t === 0 ? C.base : C.grid, "stroke-width": 1 }, svg);
      text(svg, x(t), H - 6, fmt(t, o.axisFmt || o.fmt), { anchor: "middle", size: 10 });
    });
    items.forEach(function (it, i) {
      var yb = pad.t + i * row + (row - 16) / 2;
      var lab = text(svg, pad.l - 8, yb + 8, it.label.length > maxChars ? it.label.slice(0, maxChars - 1) + "…" : it.label, { anchor: "end", baseline: "middle", size: 11, fill: it.highlight ? C.ink : C.ink2, weight: it.highlight ? 600 : 400 });
      var col = it.highlight ? C.s2 : (o.diverging ? (it.value >= 0 ? C.s1 : C.divLo) : C.s1);
      var p = el("path", { d: barPath(yb, x(0), 16, x(it.value), 4, true), fill: col }, svg);
      tooltip(p, "<b>" + esc(it.label) + "</b><br>" + fmt(it.value, o.fmt) + (it.note ? "<br>" + esc(it.note) : ""));
      // negative labels go left of the bar end, or just right of zero when the bar reaches the label column
      var neg = it.value < 0, lx = neg ? x(it.value) - 5 : x(it.value) + 5, anchor = neg ? "end" : "start";
      if (neg && lx - 7 * fmt(it.value, o.fmt).length < pad.l) { lx = x(0) + 5; anchor = "start"; }
      text(svg, lx, yb + 8, fmt(it.value, o.fmt), { anchor: anchor, baseline: "middle", size: 10, fill: C.ink2 });
    });
    if (o.ref != null) {
      el("line", { x1: x(o.ref), x2: x(o.ref), y1: pad.t - 4, y2: H - pad.b, stroke: C.ink, "stroke-width": 1.5 }, svg);
      text(svg, x(o.ref), pad.t - 8, (o.refLabel || "") + " " + fmt(o.ref, o.fmt), { anchor: "middle", size: 10, fill: C.ink, weight: 600 });
    }
    table(host, ["Item", o.valueLabel || "Value"], items.map(function (i) { return [i.label, fmt(i.value, o.fmt)]; }));
  }

  /* ---------------------------------------------------------------- valuation football field */
  function football(host, o) {
    var rows = o.rows, row = 40, pad = { l: 150, r: 30, t: 22, b: 24 }, H = pad.t + pad.b + row * rows.length;
    var f = frame(host, { title: o.title, subtitle: o.subtitle, height: H, width: o.width });
    var svg = f.svg, W = f.W, vals = [0];
    rows.forEach(function (r) { [r.lo, r.mid, r.hi].forEach(function (v) { if (v != null) vals.push(v); }); });
    (o.marks || []).forEach(function (m) { if (m.value != null) vals.push(m.value); });
    var ticks = niceTicks(Math.min.apply(null, vals), Math.max.apply(null, vals) * 1.05, 5), lo = ticks[0], hi = ticks[ticks.length - 1];
    var x = function (v) { return pad.l + (v - lo) / (hi - lo) * (W - pad.l - pad.r); };
    ticks.forEach(function (t) {
      el("line", { x1: x(t), x2: x(t), y1: pad.t, y2: H - pad.b, stroke: C.grid, "stroke-width": 1 }, svg);
      text(svg, x(t), H - 6, "₹" + t, { anchor: "middle", size: 10 });
    });
    rows.forEach(function (r, i) {
      var yc = pad.t + i * row + row / 2;
      text(svg, pad.l - 10, yc, r.label, { anchor: "end", baseline: "middle", size: 11, fill: C.ink, weight: 600 });
      if (r.lo != null && r.hi != null && r.hi > r.lo) {
        var bar = el("rect", { x: x(r.lo), y: yc - 9, width: Math.max(2, x(r.hi) - x(r.lo)), height: 18, rx: 4, fill: r.color || C.s1, "fill-opacity": 0.22 }, svg);
        tooltip(bar, "<b>" + esc(r.label) + "</b><br>Bear " + fmt(r.lo, "rs") + " · Neutral " + fmt(r.mid, "rs") + " · Bull " + fmt(r.hi, "rs"));
        text(svg, x(r.lo) - 4, yc, fmt(r.lo, "rs"), { anchor: "end", baseline: "middle", size: 10, fill: C.ink2 });
        text(svg, x(r.hi) + 4, yc, fmt(r.hi, "rs"), { baseline: "middle", size: 10, fill: C.ink2 });
      }
      if (r.mid != null) {
        var dot = el("circle", { cx: x(r.mid), cy: yc, r: 6, fill: r.color || C.s1, stroke: C.surface, "stroke-width": 2 }, svg);
        tooltip(dot, "<b>" + esc(r.label) + "</b><br>" + (r.lo != null ? "Neutral " : "") + fmt(r.mid, "rs"));
        if (r.lo == null) text(svg, x(r.mid) + 10, yc, fmt(r.mid, "rs"), { baseline: "middle", size: 10, fill: C.ink2 });
      }
    });
    (o.marks || []).forEach(function (m) {
      if (m.value == null) return;
      el("line", { x1: x(m.value), x2: x(m.value), y1: pad.t - 6, y2: H - pad.b, stroke: m.color || C.ink, "stroke-width": 1.5 }, svg);
      text(svg, x(m.value), pad.t - 9, m.label + " " + fmt(m.value, "rs"), { anchor: "middle", size: 10, fill: C.ink, weight: 600 });
    });
    table(host, ["Method", "Bear", "Neutral", "Bull"], rows.map(function (r) { return [r.label, fmt(r.lo, "rs"), fmt(r.mid, "rs"), fmt(r.hi, "rs")]; }));
  }

  /* ---------------------------------------------------------------- diverging heatmap vs a reference */
  function mix(a, b, t) {
    var pa = [1, 3, 5].map(function (i) { return parseInt(a.substr(i, 2), 16); }), pb = [1, 3, 5].map(function (i) { return parseInt(b.substr(i, 2), 16); });
    return "rgb(" + pa.map(function (v, i) { return Math.round(v + (pb[i] - v) * t); }).join(",") + ")";
  }
  function heatmap(host, o) {
    var R = o.rows.length, K = o.cols.length, cw = 0, ch = 34, pad = { l: 70, r: 8, t: 40, b: 8 };
    var H = pad.t + pad.b + ch * R;
    var f = frame(host, { title: o.title, subtitle: o.subtitle, height: H, width: o.width });
    var svg = f.svg, W = f.W; cw = (W - pad.l - pad.r) / K;
    text(svg, pad.l - 6, pad.t - 8, o.rowLabel || "", { anchor: "end", size: 10, weight: 600 });
    o.cols.forEach(function (c, j) { text(svg, pad.l + cw * j + cw / 2, pad.t - 8, fmt(c, o.colFmt), { anchor: "middle", size: 10, fill: C.ink2 }); });
    text(svg, pad.l + (W - pad.l - pad.r) / 2, 11, o.colLabel || "", { anchor: "middle", size: 10, weight: 600 });
    o.rows.forEach(function (r, i) {
      text(svg, pad.l - 6, pad.t + ch * i + ch / 2, fmt(r, o.rowFmt), { anchor: "end", baseline: "middle", size: 10, fill: C.ink2 });
      o.cols.forEach(function (c, j) {
        var v = o.values[i][j], t = v == null || !o.ref ? 0 : Math.max(-1, Math.min(1, (v / o.ref - 1) / 0.5));
        var fill = v == null ? C.divMid : t >= 0 ? mix(C.divMid, C.divHi, t) : mix(C.divMid, C.divLo, -t);
        var cell = el("rect", { x: pad.l + cw * j + 1, y: pad.t + ch * i + 1, width: cw - 2, height: ch - 2, rx: 3, fill: fill }, svg);
        if (o.center && i === o.center[0] && j === o.center[1]) cell.setAttribute("stroke", C.ink), cell.setAttribute("stroke-width", 1.5);
        var dark = Math.abs(t) > 0.55;
        text(svg, pad.l + cw * j + cw / 2, pad.t + ch * i + ch / 2, fmt(v, "rs"), { anchor: "middle", baseline: "middle", size: 10.5, fill: dark ? "#fff" : C.ink, weight: 500 });
        tooltip(cell, esc(o.rowLabel) + " " + fmt(r, o.rowFmt) + " · " + esc(o.colLabel) + " " + fmt(c, o.colFmt) + "<br><b>" + fmt(v, "rs") + "</b>" + (o.ref ? " (" + fmt(v / o.ref - 1, "pct") + " vs reference)" : ""));
      });
    });
    var lg = document.createElement("div"); lg.className = "viz-scale";
    lg.innerHTML = '<span>Below reference</span><i style="background:linear-gradient(90deg,' + C.divLo + "," + C.divMid + "," + C.divHi + ')"></i><span>Above reference</span>';
    host.appendChild(lg);
    table(host, [o.rowLabel + " \\ " + o.colLabel].concat(o.cols.map(function (c) { return fmt(c, o.colFmt); })),
      o.rows.map(function (r, i) { return [fmt(r, o.rowFmt)].concat(o.values[i].map(function (v) { return fmt(v, "rs"); })); }));
  }

  /* ---------------------------------------------------------------- 100% stacked bar (part-to-whole, <= 6 parts) */
  function stack(host, o) {
    var segs = o.segments.filter(function (s) { return s.value > 0; }), tot = segs.reduce(function (a, s) { return a + s.value; }, 0);
    var cols = [C.s1, "#5598e7", "#9ec5f4", C.s2, C.s3, "#4a3aa7"];
    var H = 46, f = frame(host, { title: o.title, subtitle: o.subtitle, height: H, width: o.width, legend: segs.map(function (s, i) { return { name: s.label, color: cols[i] }; }) });
    var svg = f.svg, W = f.W, x = 0;
    segs.forEach(function (s, i) {
      var w = s.value / tot * W;
      var r = el("rect", { x: x, y: 6, width: Math.max(0, w - 2), height: 26, fill: cols[i], rx: i === 0 || i === segs.length - 1 ? 4 : 0 }, svg);
      tooltip(r, "<b>" + esc(s.label) + "</b><br>" + fmt(s.value, "cr") + " · " + fmt(s.value / tot, "pct"));
      if (w > 54) text(svg, x + w / 2 - 1, 19, fmt(s.value / tot, "pct0"), { anchor: "middle", baseline: "middle", size: 10, fill: i < 2 || i === 5 ? "#fff" : C.ink, weight: 600 });
      x += w;
    });
    table(host, ["Portion", "Rs crore", "Share"], segs.map(function (s) { return [s.label, fmt(s.value, "int"), fmt(s.value / tot, "pct")]; }));
  }

  G.IPOCharts = { columns: columns, lines: lines, hbars: hbars, football: football, heatmap: heatmap, stack: stack, fmt: fmt, esc: esc, colors: C };
})(window);
