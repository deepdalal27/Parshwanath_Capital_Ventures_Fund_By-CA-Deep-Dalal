"""Build one issuer's workbooks from its facts file and refresh the website index.

Usage (from the repo root):
    python3 ipo-analysis/toolkit/build_issuer.py <slug>      # one issuer
    python3 ipo-analysis/toolkit/build_issuer.py --index     # only rebuild data/index.json

Reads   ipo-analysis/companies/<slug>/facts.json  (figures, see FACTS_SCHEMA.md)
        ipo-analysis/companies/<slug>/meta.json   (judgement: call, headline, flags - written by the analyst)
Writes  ipo-analysis/companies/<slug>/<SLUG>_01_Screening.xlsx, _02_Anchor_QIB.xlsx, _03_Valuation.xlsx
        meta.json["model"]  - headline outputs recalculated from the workbooks (all three scenarios)
        ipo-analysis/data/index.json - one summary row per issuer for the website
"""
import datetime as dt
import glob
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # ipo-analysis/
sys.path.insert(0, HERE)

import build_anchor      # noqa: E402
import build_screening   # noqa: E402
import build_valuation   # noqa: E402
from calc import recalc  # noqa: E402

INDEX_FIELDS = ["slug", "company", "platform", "stage", "filed_on", "analysed_on", "sector", "brlm",
                "issue_size_cr", "price_band", "call", "headline", "red_flags", "doc_url", "status"]


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
    meta.setdefault("analysed_on", dt.date.today().isoformat())
    json.dump(meta, open(meta_p, "w"), indent=2, ensure_ascii=False)
    print(f"built {slug}: {list(files.values())}")


def rebuild_index():
    rows = []
    for mp in sorted(glob.glob(os.path.join(ROOT, "companies", "*", "meta.json"))):
        m = json.load(open(mp))
        row = {k: m.get(k) for k in INDEX_FIELDS}
        row["slug"] = row["slug"] or os.path.basename(os.path.dirname(mp))
        row["neutral"] = (m.get("model") or {}).get("neutral")
        rows.append(row)
    rows.sort(key=lambda r: (r.get("filed_on") or ""), reverse=True)
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
