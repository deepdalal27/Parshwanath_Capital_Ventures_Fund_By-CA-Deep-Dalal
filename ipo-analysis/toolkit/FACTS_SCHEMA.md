# Issuer files: `facts.json` and `meta.json`

Each issuer lives in `ipo-analysis/companies/<slug>/`. `<slug>` is lower-case with hyphens, for example `abc-industries-ltd`.

| File | Who writes it | Contents |
|---|---|---|
| `facts.json` | analyst / routine | **Figures only**, exactly as restated, each with a page cite where the schema allows |
| `meta.json` | analyst / routine | **Judgement**: call, headline, red flags, plus listing details for the website |
| `note.md` | analyst / routine | The due-diligence note (Markdown), rendered on the website |
| `*.xlsx` | `build_issuer.py` | Generated. Never edit by hand in the repo; download and edit your copy |

**Rule: never invent a figure.** Leave a key out and its cell stays **blank** in the workbook, a declared gap.
Log the gap in `facts.screening.gaps` and in the note's data-gaps table.
Only house-policy keys (tax rate, CAPM inputs, g = 4.5%, blend weights, lock-in days and so on) fall back to defaults.

Units: Rs crore; valuation share counts in **crore**; overhang share counts in **lakh**; percentages as decimals (`0.25`);
dates as `"YYYY-MM-DD"`.

## facts.json

```jsonc
{
  "screening": {
    "basis":  { "name": "", "platform": "Mainboard|SME", "stage": "DRHP|RHP|Addendum|Prospectus",
                "doc_date": "2026-09-30", "aud_to": "2026-06-30", "band": "Yes|No", "brlm": "",
                "outside": "none", "bid_cat": "Anchor", "exit": "2-3 year hold (assumed)" },
    // [FY-3, FY-2, FY-1 (latest), stub as reported]  - use null for a period not disclosed
    "items":  { "rev": [], "oth": [], "pbt": [], "ctax": [], "dtax": [], "pat": [], "cfo": [],
                "rpt_s": [], "rpt_p": [], "nw": [], "recv": [], "inv": [], "pay": [], "cl": [], "gw": [], "reval": [] },
    "cites":  { "rev": "p. 312", "cfo": "p. 318" },
    "single": { "top1c": 0.0, "top10c": 0.0, "top1s": 0.0, "geo": 0.0, "fresh_net": 0.0, "waca": 0.0, "offer": 0.0 },
    // keys "1".."10" (forensic checks) and "R1".."R7" (regulatory); status PASS|WATCH|FAIL|N.A.|OPEN
    "checks": { "2": { "status": "WATCH", "page": "p. 318", "finding": "Cumulative CFO/PAT 41%" } },
    "gaps":   [ { "item": "", "severity": "High|Medium|Low", "source": "MCA / BSE / NSE" } ]
  },
  "anchor": {
    "inputs": { "name": "", "board": "Mainboard", "offer": null, "anchor_px": null, "issue": 0, "emp": 0, "shr": 0,
                "qib_pct": 0.5, "nii_pct": 0.15, "rii_pct": 0.35, "anc_pct": 0.6, "mf_anc": 0.3333, "ins_anc": 0.0667,
                "bid_date": null, "allot_date": null, "list_date": null },
    "paths":  { "Bear": [null, null, null], "Neutral": [null, null, null], "Bull": [null, null, null] },
    "total_shares_lakh": 0,
    "overhang": [ ["Pre-issue non-promoter shareholders", 0, 180, "p. 98"],
                  ["Promoter minimum contribution", 0, 540, "p. 96"] ]
  },
  "valuation": {
    "inputs":  { "name": "", "pre_sh": 0, "esop": 0, "fresh": 0, "fresh_sh_fixed": 0, "ofs_sh": 0,
                 "floor": null, "cap": null, "obj_net": 0, "exp_pct": 0, "gcp_pct": 0, "ipo_capex": 0,
                 "rev0": 0, "rev_prev": 0, "ebitda0": 0, "da0": 0, "pat0": 0, "nw0": 0, "nd0": 0,
                 "nwc0": 0, "nwc_prev": 0, "capex0": 0 },
    // [Bear, Neutral, Bull]
    "drivers":   { "g1": [], "g2": [], "g3": [], "g4": [], "g5": [], "m": [], "nwc": [], "roic": [] },
    "rationale": { "g1": "Order book Rs X cr = 1.4x FY26 revenue (p. 201)" },
    // [name, include Y/N, business-model match, basis, CMP, shares (cr), net debt, revenue, EBITDA, PAT, net worth, rev growth]
    "peers": [ ["Peer Ltd", "Y", "Same model", "Consolidated", 0, 0, 0, 0, 0, 0, 0, 0] ]
  }
}
```

Optional valuation overrides (house policy, defaults apply if absent): `tax rf beta erp size csp kd dw g w_dcf w_pe w_eve w_pb rel_disc capex_y1`.

## meta.json

```json
{
  "slug": "abc-industries-ltd",
  "company": "ABC Industries Limited",
  "platform": "Mainboard",
  "stage": "DRHP",
  "filed_on": "2026-09-30",
  "doc_url": "https://www.sebi.gov.in/...",
  "sector": "Specialty chemicals",
  "brlm": "XYZ Capital",
  "issue_size_cr": 0,
  "price_band": null,
  "call": "Subscribe | Avoid | Neutral | Screen only",
  "exit_route": "2-3 year hold (assumed)",
  "headline": "One sentence: what decides this issue.",
  "red_flags": ["CFO 41% of PAT over 3 years", "Top supplier 74%, no supply contract"],
  "status": "analysed"
}
```

`build_issuer.py` adds `files`, `analysed_on` and `model` (DCF / relative / blended per scenario, guard flags,
objects floor and reverse-DCF sentence) and then rewrites `data/index.json`.
