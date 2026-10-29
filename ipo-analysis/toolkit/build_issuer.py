"""Build one issuer's workbooks from its facts file and refresh the website index.

Usage (from the repo root):
    python3 ipo-analysis/toolkit/build_issuer.py <slug>      # one issuer
    python3 ipo-analysis/toolkit/build_issuer.py --index     # only rebuild data/index.json

Reads   ipo-analysis/companies/<slug>/facts.json  (figures, see FACTS_SCHEMA.md)
        ipo-analysis/companies/<slug>/meta.json   (judgement: call, headline, flags - written by the analyst)
Writes  ipo-analysis/companies/<slug>/<SLUG>_01_Screening.xlsx, _02_Anchor_QIB.xlsx, _03_Valuation.xlsx,
        <SLUG>_Report.pdf (branded report from note.md)
        meta.json["model"]  - headline outputs recalculated from the workbooks (all three scenarios)
        ipo-analysis/data/index.json - one summary row per issuer for the website
"""
import datetime as dt
import glob
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # ipo-analysis/
sys.path.insert(0, HERE)

import build_anchor      # noqa: E402
import build_charts      # noqa: E402
import build_pdf         # noqa: E402
import build_screening   # noqa: E402
import build_valuation   # noqa: E402
from calc import recalc  # noqa: E402

INDEX_FIELDS = ["slug", "company", "platform", "stage", "filed_on", "analysed_on", "sector", "brlm",
                "issue_size_cr", "price_band", "open_date", "close_date", "allotment_date", "listing_date", "lot_size",
                "exchange", "depth", "rhp_read", "company_pe", "call", "business_stage", "headline", "red_flags", "doc_url", "status", "counts",
                "focus_top"]
# The desk covers RHP-stage issues only (price band known). DRHP reports are not listed on the site.
LISTED_STAGES = ("RHP", "PROSPECTUS")


CPE_START, CPE_END = "<!-- company-disclosed:start -->", "<!-- company-disclosed:end -->"


def band_ends(band):
    n = [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", band or "")]
    return (n[0], n[-1]) if n else (None, None)


def company_pe(meta):
    """Fill the P/E the company's own EPS gives at the price band (fund manager's instruction, 29-Oct-2026).

    The RHP prints the issuer's P/E as [●] until the band is fixed; the price-band advertisement then divides the band
    by the RHP's latest-full-year basic and diluted EPS. We do the same, from meta["company_pe"] (PAT and EPS as stated)."""
    c = meta.get("company_pe")
    if not c:
        if str(meta.get("stage", "")).upper() in LISTED_STAGES:
            print(f"WARNING {meta.get('slug')}: meta.company_pe missing - every report must show the company's PAT and P/E")
        return None
    lo, hi = band_ends(meta.get("price_band"))
    for kind in ("basic", "diluted"):
        eps = c.get(f"eps_{kind}")
        c[f"pe_floor_{kind}"] = round(lo / eps, 2) if lo and eps and eps > 0 else None
        c[f"pe_cap_{kind}"] = round(hi / eps, 2) if hi and eps and eps > 0 else None
    c["floor"], c["cap"] = lo, hi
    return c


def company_pe_block(meta):
    c = meta.get("company_pe")
    if not c:
        return ""
    f = lambda v, d=2: "-" if v is None else f"{v:,.{d}f}"
    x = lambda v: "-" if v is None else f"{v:.2f}x"
    per = c.get("period", "latest year")
    rows = [("Restated PAT, " + per + (" (" + c["pat_basis"] + ")" if c.get("pat_basis") else ""), "Rs " + f(c.get("pat_cr")) + " cr"),
            (f"EPS, {per} (basic / diluted)", f"Rs {f(c.get('eps_basic'))} / Rs {f(c.get('eps_diluted'))}"),
            (f"P/E at floor price Rs {f(c.get('floor'), 0)} (basic / diluted)", f"{x(c.get('pe_floor_basic'))} / {x(c.get('pe_floor_diluted'))}"),
            (f"P/E at cap price Rs {f(c.get('cap'), 0)} (basic / diluted)", f"{x(c.get('pe_cap_basic'))} / {x(c.get('pe_cap_diluted'))}")]
    ind = c.get("industry_pe") or {}
    if ind:
        rows.append(("Industry peer P/E (highest / lowest / average)",
                     " / ".join(x(ind.get(k)) for k in ("high", "low", "avg"))))
    out = [CPE_START, "### As disclosed by the company (Basis for Offer Price)", "", "| Item | As disclosed |", "|---|---|"]
    out += [f"| {a} | {b} |" for a, b in rows]
    out += ["", "Source: " + c.get("source", "RHP, Basis for Offer Price") + ". The RHP prints the issuer's P/E as [●] until the "
            "price band is fixed; the P/E shown is the band divided by the company's own EPS, the computation the price-band "
            "advertisement makes. These are pre-issue, latest-full-year figures; our own P/E elsewhere in this report is on "
            "post-issue shares." + (" " + c["note"] if c.get("note") else ""), CPE_END, ""]
    return "\n".join(out)


def inject_company_pe(note_p, meta):
    if not os.path.exists(note_p):
        return
    t = open(note_p).read()
    t = re.sub(re.escape(CPE_START) + ".*?" + re.escape(CPE_END) + "\n*", "", t, flags=re.S)
    block = company_pe_block(meta)
    if block:
        anchor = "### Is the reported P/E right?"
        t = t.replace(anchor, block + "\n" + anchor, 1) if anchor in t else t.replace("## 6.", block + "\n## 6.", 1)
    open(note_p, "w").write(t)


def num(v):
    return round(v, 4) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def model_outputs(facts):
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        for s, name in ((1, "bear"), (2, "neutral"), (3, "bull")):
            p = os.path.join(tmp, f"v{s}.xlsx")
            build_valuation.build(p, scenario=s, facts=facts.get("valuation", {}))
            x = recalc(p)
            out[name] = {"dcf": num(x.get(("SUMMARY", "C7"))), "relative": num(x.get(("SUMMARY", "C8"))),
                         "blended": num(x.get(("SUMMARY", "C9"))), "upside_floor": num(x.get(("SUMMARY", "D9"))),
                         "upside_cap": num(x.get(("SUMMARY", "E9")))}
            if s == 2:
                out["flags"] = [str(x.get(("SUMMARY", c))) for c in ("C12", "C14", "C15", "C16", "C17")
                                if isinstance(x.get(("SUMMARY", c)), str) and not str(x.get(("SUMMARY", c))).startswith(("OK", "n.a."))]
                out["reverse_dcf"] = x.get(("REVERSEDCF", "C16")) if isinstance(x.get(("REVERSEDCF", "C16")), str) else None
                out["objects_floor"] = num(x.get(("SUMMARY", "C13")))
    return out


def build(slug):
    d = os.path.join(ROOT, "companies", slug)
    facts = json.load(open(os.path.join(d, "facts.json")))
    meta_p = os.path.join(d, "meta.json")
    meta = json.load(open(meta_p)) if os.path.exists(meta_p) else {"slug": slug}
    tag = slug.upper().replace("-", "_")[:24]
    files = {
        "screening": f"{tag}_01_Screening.xlsx",
        "anchor": f"{tag}_02_Anchor_QIB.xlsx",
        "valuation": f"{tag}_03_Valuation.xlsx",
    }
    build_screening.build(os.path.join(d, files["screening"]), facts=facts.get("screening", {}))
    build_anchor.build(os.path.join(d, files["anchor"]), facts=facts.get("anchor", {}))
    build_valuation.build(os.path.join(d, files["valuation"]), scenario=2, facts=facts.get("valuation", {}))
    meta["files"] = files
    if os.path.exists(os.path.join(d, "note.md")):
        meta["files"]["note"] = "note.md"
    meta["model"] = model_outputs(facts)
    company_pe(meta)
    inject_company_pe(os.path.join(d, "note.md"), meta)
    json.dump(meta, open(meta_p, "w"), indent=2, ensure_ascii=False)   # charts and PDF read meta.json
    charts = build_charts.build(slug)
    meta["counts"] = charts["counts"]
    meta["focus_top"] = [f["title"] for f in charts["focus"][:3]]
    json.dump(meta, open(meta_p, "w"), indent=2, ensure_ascii=False)
    pdf = build_pdf.build(slug)
    if pdf:
        meta["files"]["pdf"] = pdf
    meta.setdefault("analysed_on", dt.date.today().isoformat())
    json.dump(meta, open(meta_p, "w"), indent=2, ensure_ascii=False)
    print(f"built {slug}: {list(files.values())}")


def rebuild_index():
    rows = []
    for mp in sorted(glob.glob(os.path.join(ROOT, "companies", "*", "meta.json"))):
        m = json.load(open(mp))
        if str(m.get("stage", "")).upper() not in LISTED_STAGES:
            continue
        row = {k: m.get(k) for k in INDEX_FIELDS}
        row["slug"] = row["slug"] or os.path.basename(os.path.dirname(mp))
        model = m.get("model") or {}
        row["neutral"] = model.get("neutral")
        row["bear"] = (model.get("bear") or {}).get("blended")
        row["bull"] = (model.get("bull") or {}).get("blended")
        row["pdf"] = (m.get("files") or {}).get("pdf")
        cp = os.path.join(os.path.dirname(mp), "charts.json")
        if os.path.exists(cp):
            eq = json.load(open(cp)).get("earnings_quality") or {}
            row["pe_reported"], row["pe_adjusted"] = eq.get("pe_reported"), eq.get("pe_adjusted")
            row["eq_material"] = eq.get("material")
        rows.append(row)
    rows.sort(key=lambda r: (r.get("open_date") or r.get("filed_on") or ""), reverse=True)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    out = {"updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "issuers": rows}
    json.dump(out, open(os.path.join(ROOT, "data", "index.json"), "w"), indent=2, ensure_ascii=False)
    print(f"index: {len(rows)} issuers")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    for a in args:
        if a != "--index":
            build(a)
    rebuild_index()
