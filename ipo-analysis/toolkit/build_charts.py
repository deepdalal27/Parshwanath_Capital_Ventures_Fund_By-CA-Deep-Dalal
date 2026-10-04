"""Assemble companies/<slug>/charts.json - every number the dashboard and the PDF draw.

The website (view.html) and the PDF (report.html, printed by build_pdf.py) both render from
this one file, so the two can never disagree. Values come from facts.json, meta.json,
data/merchant_bankers.json and an independent recalculation of the three built workbooks.

Usage:  python3 ipo-analysis/toolkit/build_charts.py <slug>      (build_issuer.py calls it)
"""
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from calc import recalc  # noqa: E402

CHECK_NAMES = {
    "1": "Bonus issue / share-count consistency", "2": "Cash flow vs profit", "3": "Current vs deferred tax",
    "4": "Related-party capex & subsidiaries", "5": "Objects arithmetic as price floor", "6": "Revaluation reserve",
    "7": "Goodwill vs tangible equity", "8": "Customer / supplier / geographic concentration",
    "9": "Contingent liabilities", "10": "Investor presentation vs DRHP", "R1": "Auditor qualifications / changes",
    "R2": "CARO / audit trail", "R3": "Monitoring agency", "R4": "Eligibility re-computation",
    "R5": "SME conditions", "R6": "Lead-manager track record", "R7": "Firm means of finance",
}


def num(v):
    return round(float(v), 4) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def by_label(x, sheet, label_col="B", value_col="C", rows=range(1, 120)):
    """{label: value} for a sheet laid out as label | value."""
    out = {}
    for r in rows:
        lab = x.get((sheet, f"{label_col}{r}"))
        if isinstance(lab, str) and lab.strip():
            out[lab.strip()] = x.get((sheet, f"{value_col}{r}"))
    return out


def cagr(a, b, years):
    if not (isinstance(a, (int, float)) and isinstance(b, (int, float))) or a <= 0 or b <= 0 or years <= 0:
        return None
    return round((b / a) ** (1 / years) - 1, 4)


def build(slug):
    d = os.path.join(ROOT, "companies", slug)
    facts = json.load(open(os.path.join(d, "facts.json"), encoding="utf-8"))
    meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
    files = meta.get("files", {})
    sc, an, va = facts.get("screening", {}), facts.get("anchor", {}), facts.get("valuation", {})
    items = sc.get("items", {})
    model = meta.get("model") or {}

    xv = recalc(os.path.join(d, files["valuation"]))
    xa = recalc(os.path.join(d, files["anchor"]))
    xs = recalc(os.path.join(d, files["screening"]))

    # ---------------------------------------------------------------- history (3 FY, Rs crore)
    years = ["FY-3", "FY-2", "FY-1"]
    ly = sc.get("basis", {}).get("aud_to")
    if ly:
        fy = int(ly[:4]) % 100
        years = [f"FY{fy - 2:02d}", f"FY{fy - 1:02d}", f"FY{fy:02d}"]

    def s(k):
        v = items.get(k) or [None] * 4
        return [num(x) for x in v[:3]]

    rev, pat, cfo = s("rev"), s("pat"), s("cfo")
    inv, recv, pay = s("inv"), s("recv"), s("pay")
    pbt, oth = s("pbt"), s("oth")
    ebitda_hist = None
    if all(isinstance(x, (int, float)) for x in (va.get("inputs", {}).get("ebitda0"),)):
        ebitda_hist = [None, None, num(va["inputs"]["ebitda0"])]
    # EBITDA history from the issuer KPI if supplied in facts.kpi (optional), else latest only
    kpi = facts.get("kpi", {})
    if kpi.get("ebitda"):
        ebitda_hist = [num(x) for x in kpi["ebitda"][:3]]

    def ratio(a, b):
        return [round(x / y, 4) if isinstance(x, (int, float)) and isinstance(y, (int, float)) and y else None
                for x, y in zip(a, b)]

    nwc = [round(i + r - p, 2) if None not in (i, r, p) else None for i, r, p in zip(inv, recv, pay)]
    history = {
        "years": years, "revenue": rev, "ebitda": ebitda_hist or [None] * 3, "pat": pat, "cfo": cfo,
        "ebitda_margin": ratio(ebitda_hist or [None] * 3, rev), "pat_margin": ratio(pat, rev),
        "inventory": inv, "receivables": recv, "payables": pay, "nwc": nwc, "nwc_pct": ratio(nwc, rev),
        "unit": "Rs crore",
    }
    if kpi.get("volume"):
        history["volume"] = [num(x) for x in kpi["volume"][:3]]
        history["volume_unit"] = kpi.get("volume_unit", "")

    # ---------------------------------------------------------------- KPI tiles
    qm = by_label(xs, "QUICK METRICS")
    cum_cfo_pat = qm.get("Cumulative CFO / cumulative PAT (3 yrs)")
    cash_tax = qm.get("Cumulative cash tax rate (current tax / PBT)")
    vin = va.get("inputs", {})
    peers_pe = xv.get(("PEERS", "P14"))
    ref = num(vin.get("cap"))
    post_sh = num(xv.get(("DCF", "C36")))
    pe_ref = (ref * post_sh / vin["pat0"]) if ref and post_sh and vin.get("pat0") else None
    neutral = model.get("neutral") or {}
    kpis = [
        {"label": f"Revenue {years[2]}", "value": rev[2], "fmt": "cr",
         "sub": f"CAGR {years[0]}-{years[2]}", "subval": cagr(rev[0], rev[2], 2), "subfmt": "pct"},
        {"label": f"PAT {years[2]}", "value": pat[2], "fmt": "cr",
         "sub": f"CAGR {years[0]}-{years[2]}", "subval": cagr(pat[0], pat[2], 2), "subfmt": "pct"},
        {"label": "EBITDA margin", "value": history["ebitda_margin"][2], "fmt": "pct",
         "sub": f"{years[0]}", "subval": history["ebitda_margin"][0], "subfmt": "pct"},
        {"label": "Cash conversion (CFO / PAT, 3 yrs)", "value": num(cum_cfo_pat), "fmt": "pct",
         "tone": ("bad" if isinstance(cum_cfo_pat, (int, float)) and cum_cfo_pat < 0.7 else "good")},
        {"label": "Cash tax rate (3 yrs)", "value": num(cash_tax), "fmt": "pct",
         "tone": ("good" if isinstance(cash_tax, (int, float)) and cash_tax >= 0.2 else "warn")},
        {"label": "P/E at reference (post-issue)", "value": round(pe_ref, 2) if pe_ref else None, "fmt": "x",
         "sub": "peer median", "subval": num(peers_pe), "subfmt": "x"},
        {"label": "Blended value (Neutral)", "value": neutral.get("blended"), "fmt": "rs",
         "sub": "vs reference", "subval": neutral.get("upside_cap"), "subfmt": "pct"},
        {"label": "Reference price", "value": ref, "fmt": "rs", "sub": meta.get("reference_note") or meta.get("price_band")},
    ]

    # ---------------------------------------------------------------- scorecard + focus
    checks = sc.get("checks", {})
    score = []
    for k, name in CHECK_NAMES.items():
        c = checks.get(k, {})
        score.append({"id": k, "check": name, "status": c.get("status", "OPEN"), "page": c.get("page", ""),
                      "finding": c.get("finding", "")})
    level_rank = {"FAIL": 0, "WATCH": 1, "GUARD": 2, "GAP": 3}
    focus, comfort = [], []
    for c in score:
        if c["status"] in ("FAIL", "WATCH"):
            focus.append({"level": c["status"], "title": c["check"], "detail": c["finding"], "page": c["page"]})
        elif c["status"] == "PASS":
            comfort.append({"title": c["check"], "detail": c["finding"], "page": c["page"]})
    for g in model.get("flags") or []:
        focus.append({"level": "GUARD", "title": "Valuation model guard", "detail": g, "page": ""})
    for g in sc.get("gaps", []):
        if g.get("severity") in ("High", "Medium"):
            focus.append({"level": "GAP", "title": f"Data gap ({g['severity'].lower()})", "detail": g["item"],
                          "page": g.get("source", "")})
    focus.sort(key=lambda f: level_rank.get(f["level"], 9))

    # ---------------------------------------------------------------- valuation
    scen = {k: model.get(k) or {} for k in ("bear", "neutral", "bull")}
    valuation = {
        "reference": ref, "floor": num(vin.get("floor")), "cap": ref,
        "reference_note": meta.get("reference_note") or meta.get("price_band"),
        "scenarios": scen, "objects_floor": model.get("objects_floor"),
    }
    am = by_label(xv, "ASSUMPTIONS")
    valuation["wacc"] = num(am.get("WACC"))
    valuation["tv_share"] = num(xv.get(("DCF", "C32")))
    valuation["reverse"] = {
        "sentence": model.get("reverse_dcf"),
        "levers": [{"label": xv.get(("REVERSEDCF", f"B{r}")), "required": xv.get(("REVERSEDCF", f"D{r}")),
                    "actual": num(xv.get(("REVERSEDCF", f"E{r}")))} for r in (11, 12, 13, 14)],
    }
    dcf = {"years": ["Y0 (A)", "Y1", "Y2", "Y3", "Y4", "Y5"]}
    for key, row in (("revenue", 7), ("ebitda", 9), ("nopat", 13), ("fcff", 18)):
        dcf[key] = [num(xv.get(("DCF", f"{c}{row}"))) for c in "CDEFGH"]

    def grid(r0, r1, c0):
        cols = [num(xv.get(("SENSITIVITY", f"{c}{c0}"))) for c in "CDEFG"]
        rows = [num(xv.get(("SENSITIVITY", f"B{r}"))) for r in range(r0, r1 + 1)]
        vals = [[num(xv.get(("SENSITIVITY", f"{c}{r}"))) for c in "CDEFG"] for r in range(r0, r1 + 1)]
        return {"rows": rows, "cols": cols, "values": vals}

    sens = {"wacc_g": grid(6, 10, 5), "nwc_margin": grid(14, 18, 13)}

    peers = []
    for r in list(range(5, 13)) + [21]:
        nm = xv.get(("PEERS", f"B{r}"))
        if not nm:
            continue
        pe, pb = xv.get(("PEERS", f"P{r}")), xv.get(("PEERS", f"R{r}"))
        if not isinstance(pe, (int, float)) and not isinstance(pb, (int, float)):
            continue
        peers.append({"name": str(nm).replace(" (per share)", "").replace(" (post-issue)", ""),
                      "pe": num(pe), "pb": num(pb), "issuer": r == 21})
    if peers and peers[-1]["issuer"]:
        peers[-1]["name"] = f"{meta.get('company', slug)} at reference"

    # ---------------------------------------------------------------- offer structure + overhang
    al = by_label(xa, "ALLOCATION")
    structure = [
        {"label": "Anchor: MF reserved", "value": num(al.get("of which reserved for domestic MFs"))},
        {"label": "Anchor: insurers & pension", "value": num(al.get("of which reserved for insurers & pension funds"))},
        {"label": "Anchor: open pool", "value": num(al.get("open anchor pool (where an AIF competes)"))},
        {"label": "QIB (non-anchor)", "value": num(al.get("Net QIB (after anchor)"))},
        {"label": "Non-institutional", "value": num(al.get("Non-institutional portion"))},
        {"label": "Retail", "value": num(al.get("Retail portion"))},
    ]
    overhang = []
    for r in range(9, 20):
        cat = xa.get(("OVERHANG", f"B{r}"))
        sh = xa.get(("OVERHANG", f"C{r}"))
        days = xa.get(("OVERHANG", f"D{r}"))
        if cat and isinstance(sh, (int, float)) and sh > 0:
            overhang.append({"label": cat, "shares_lakh": num(sh), "days": days,
                             "pct_float": num(xa.get(("OVERHANG", f"G{r}")))})

    # ---------------------------------------------------------------- merchant bankers
    mb_path = os.path.join(ROOT, "data", "merchant_bankers.json")
    brlm = {"bankers": [], "issues": []}
    if os.path.exists(mb_path):
        mb = json.load(open(mb_path, encoding="utf-8"))
        names = [n.strip() for n in (meta.get("brlm") or "").split(";")]
        for full, b in mb.get("bankers", {}).items():
            if any(n and n.split()[0].lower() in full.lower() for n in names):
                brlm["bankers"].append({"name": full, "owner": b.get("owner"), "listed": b.get("listed"),
                                        "summary": b.get("summary"), "short": b.get("short")})
        shorts = {b["short"] for b in brlm["bankers"]}
        for e in mb.get("issues", []):
            if shorts & set(e.get("handled_by", [])):
                f = e.get("financials_rs_cr") or {}
                brlm["issues"].append({"issuer": e["issuer"], "sector": e["sector"], "listing_gain": e["listing_gain_pct"],
                                       "d30": e.get("d30_pct"), "rev_growth": f.get("rev_chg_pct"),
                                       "pat_growth": f.get("pat_chg_pct"), "listing_date": e["listing_date"]})

    out = {
        "slug": slug, "company": meta.get("company"), "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "kpis": kpis, "focus": focus, "comfort": comfort, "scorecard": score, "history": history,
        "valuation": valuation, "dcf": dcf, "sensitivity": sens, "peers": peers,
        "offer": {"structure": [s_ for s_ in structure if s_["value"]], "issue_cr": num(al.get("Net offer")), "overhang": overhang},
        "brlm": brlm, "swot": meta.get("swot"),
        "counts": {"fail": sum(c["status"] == "FAIL" for c in score), "watch": sum(c["status"] == "WATCH" for c in score),
                   "pass": sum(c["status"] == "PASS" for c in score), "open": sum(c["status"] == "OPEN" for c in score)},
    }
    json.dump(out, open(os.path.join(d, "charts.json"), "w"), indent=1, ensure_ascii=False)
    print(f"charts: {slug} ({len(focus)} focus items, {len(peers)} peers, {len(brlm['issues'])} lead-manager issues)")
    return out


if __name__ == "__main__":
    for a in sys.argv[1:]:
        build(a)
