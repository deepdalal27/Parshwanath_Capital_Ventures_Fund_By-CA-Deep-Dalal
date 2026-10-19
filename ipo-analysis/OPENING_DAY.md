# Opening-day IPO reports - standing instructions

A second scheduled routine reads this file every weekday morning. It finds every IPO **opening for subscription today**
and publishes a report on each one to the website by **11:30 AM - 12:00 noon IST**. Edit this file on GitHub to change what
the routine does; settings that change often live in `data/opening_calendar.json`.

All the hard rules in `ROUTINE.md` apply here too, **including hard rule 6, the investor's lens** (normal features are context, not deductions; no strict valuation stance; the fixed call rule), and also: never invent a figure, firm-approved disclaimer only, no offer-document
PDFs in the repo, analysis only from the offer document, neutral stance, grey market premium never used, branding.
The differences are listed below.

| | DRHP routine (`ROUTINE.md`) | Opening-day routine (this file) |
|---|---|---|
| Trigger | New filing with SEBI | Issue opens for subscription today |
| Document | DRHP / addendum | **RHP** (price band, anchor book, dates are known) |
| Volume | 1 a day | Every IPO opening today |
| Depth | Full | Mainboard: **full report**. SME: **snapshot** |
| Publish | PR for review | **Auto-publish**: the routine merges its own PR into `main` |

## 0. Setup
```bash
pip install -q -r ipo-analysis/toolkit/requirements.txt pypdf
(apt-get install -y -q poppler-utils || true)
```
Work out today's date in IST (`TZ=Asia/Kolkata date +%F`). If today is an exchange holiday, record the scan and stop.

## 1. Find today's openings
Read `data/opening_calendar.json`. Use the enabled `sources` to list every IPO, Mainboard and SME, whose subscription
**opens today**, and also those opening in the next 5 working days (the look-ahead). For each record: `company`,
`platform`, `open_date`, `close_date`, `price_band`, `lot_size`, `issue_size_cr`, `exchange`, `rhp_url` and `source`.
- Discovery may use the secondary calendar sources, but **dates, price band, lot size and issue size must be confirmed in the
  RHP or on BSE / NSE / SEBI** before they are published. Note what was confirmed where.
- Write today's openings to `today` and the look-ahead to `upcoming`; set `last_scan` (UTC, `YYYY-MM-DDTHH:MMZ`).
- An IPO already listed in `done` (same company and `open_date`) is skipped.
- If an issuer already has a folder in `companies/` from the DRHP routine, update that folder (same slug). The RHP report
  supersedes the DRHP note and opens with the **DRHP-to-RHP delta register** (what changed: issue size, OFS sellers,
  objects, restated numbers, new litigation, new peers).

## 2. Analyse every opening, in parallel
- Download each RHP to `/tmp` (never the repo); extract with `pdftotext -layout` (or `pypdf`); build the page map.
- Load the `drhp-due-diligence` skill if it is available and follow it, together with the spine below.
- **Run the issuers in parallel.** Spawn one subagent per issuer (the `Agent` tool), each writing only its own
  `companies/<slug>/` folder and returning its call, headline and any problems. Do not let two subagents touch
  `data/*.json`; the main session updates shared files after they finish. Mainboard issuers first if capacity is short.
- Anchor book: the anchor allotment is filed with the exchanges the working day before opening. Record the anchor
  investors, the amount, the mutual-fund share and the lock-in from the exchange filing, with its link. If it is not out
  yet, say so; never estimate it.
- Subscription at the time of writing (optional): the exchange's live day-1 subscription by category, with the time it was
  read (IST). It is a fact, not a signal, and it never moves fair value.

### Mainboard: full report
`note.md`, in this order. Every number carries an RHP page cite.
1. **Banner**: RHP date, audited-to date and staleness in days; open / close / allotment / listing dates; price band,
   lot size and minimum application amount; issue size split fresh vs OFS; exchanges.
2. **Verdict**, stated neutrally: `Subscribe` / `Neutral` / `Avoid` under the call rule in `ROUTINE.md` hard rule 6 (say which limb applied), the price it was judged at (upper band), and what decides it.
3. **Snapshot table**: revenue, EBITDA, PAT, margins, ROE, ROCE, net debt for 3 years and the stub; market cap and
   P/E, EV/EBITDA, P/B at the upper band, post-issue.
4. **Business model**: what is sold, to whom, how it is priced, how it earns its margin, what it owns vs outsources,
   revenue mix by product, customer type and geography.
5. **Stage of the business**: classify as *start-up, early growth, scaling, mature, turnaround* or *declining*, and show
   the evidence: revenue CAGR, margin trend, capex vs depreciation, free cash flow sign, reinvestment rate, market share,
   capacity utilisation. Say what the stage means for the valuation method and the risk.
6. **Industry analysis**: market size and growth, structure and fragmentation, named and unnamed competitors, regulation,
   cyclicality, entry barriers. Say who commissioned the industry report.
7. **Future prospects**: order book or pipeline, capacity being added and when (with what the proceeds fund), new products
   and markets, what management states in the RHP, and the 3-year path in Bear / Neutral / Bull with the drivers quantified.
   Say what has to go right and what is already contracted.
8. **Peer comparison (P2P)**: a table of listed peers from the RHP's "Basis for Offer Price", plus our own if the RHP list
   is thin (mark them "added by us"). Columns: CMP and date, market cap, revenue, revenue 3-year CAGR, EBITDA margin,
   PAT margin, ROE, ROCE, net debt/equity, P/E, EV/EBITDA, P/B. Put the issuer at the upper band on the same basis on the
   last row, then the peer median. Say in plain words whether the price is at a premium or a discount, and whether the
   growth and returns justify it. Peer data goes into `facts.valuation.peers`.
9. **Financials and key findings**: positives and concerns side by side.
10. **DCF valuation**: WACC build (risk-free, beta and its source, ERP, size and company-specific premia, cost of debt,
    weights), 5-year free cash flow projection per scenario, terminal growth 4.50%, terminal value as a share of EV,
    per-share value Bear / Neutral / Bull, a WACC x terminal-growth sensitivity, then the relative valuation and the blend
    (50:50, or 70:30 without listed peers; through-cycle Neutral case per hard rule 6), and the **reverse DCF**: what the upper band asks the business to deliver.
    Upside against the upper band as a percentage only.
11. **Management and governance**: promoters' background and track record; board size and independence; key managerial
    personnel and tenure; remuneration against PAT; promoter holding pre and post issue; who sells in the OFS and their
    WACA vs the price; pledges; related-party transactions in full; group companies and conflicts; litigation and
    regulatory actions against the company, promoters and directors; auditor (tenure, changes, qualifications, CARO,
    audit trail); monitoring agency. Finish with a governance read: what gives comfort and what needs watching.
12. **SWOT**: table, each item with a figure and page cite.
13. **Moat**: what protects returns (scale, cost, switching costs, brand, licences, network), how durable, what evidence.
    Say plainly when there is none.
14. **Offer, objects and anchor book**: objects arithmetic, anchor investors, MF share, quality of the book.
15. **Points to monitor**: the normal-course items an investor should track after listing, each with its number (concentration, working capital, related parties, litigation), stated once and in proportion.
16. **Merchant banker(s)**: as in `ROUTINE.md` (track record of past issues, from the RHP).
17. **What would change our view**, 18. **Risks**, 19. **Data gaps**, 20. **Appendix: diligence checks** (the ten checks in
`ROUTINE.md`; `FAIL` only for material issues), 21. **Verification**,
22. `## Disclaimer and disclosures` followed by the `short` text from `data/disclaimer.json`.

### SME: snapshot report
Two pages, same rules on sourcing and neutrality. `note.md` sections: Banner; Verdict; Snapshot table; Business model and
stage of the business (one paragraph each); Industry in brief; Future prospects in brief; Peer comparison (P2P) table;
Valuation (DCF and relative, Neutral case, plus reverse DCF); Management and governance (promoters, board, RPTs,
litigation, auditor); SWOT; Moat (one line); Points to monitor (normal-course items, in proportion; any material issue stated plainly); Merchant banker
track record (summary table); Risks; Data gaps; Disclaimer. Set `meta.depth` to `"Snapshot"`.
`facts.json` still needs the valuation inputs, drivers and peers so the model and charts build.

### meta.json additions
On top of the fields in `toolkit/FACTS_SCHEMA.md`: `stage` = `"RHP"`, `price_band` (e.g. `"Rs 285-300"`),
`open_date`, `close_date`, `allotment_date`, `listing_date`, `lot_size`, `exchange`, `depth` (`"Full"` or `"Snapshot"`),
`business_stage` (the classification from section 5), `anchor` (`{ "amount_cr": , "investors": , "mf_share": , "source": }`),
and `swot`. The call is judged at the upper band; `Screen only` is not used on opening day.

## 3. Build, verify, check
```bash
python3 ipo-analysis/toolkit/build_issuer.py <slug> [<slug> ...]
python3 ipo-analysis/toolkit/verify.py
```
`verify.py` must end with every check passed. Open `view.html?c=<slug>` through `python3 -m http.server` and check every
chart has data; open the PDF. If an issuer cannot be finished, leave it out of the publish, keep it in `today` with a note,
and finish it in a follow-up push the same day.

## 4. Auto-publish
- Move finished issuers from `today` to `done` (company, `open_date`, slug). Rebuild the index:
  `python3 ipo-analysis/toolkit/build_issuer.py --index`.
- Fetch `main` and merge it into your branch first (the DRHP routine may have changed `data/index.json`; resolve by
  re-running `--index`). Commit on a new branch, push, open a pull request titled
  `Opening-day IPO reports: <date> - <company names>`, and **merge it yourself** (squash). GitHub Pages redeploys the site.
- Timing: publish everything finished by 11:45 IST in one PR. Anything still running is published in a second PR as soon as
  it is done, with the delay stated in its description.
- Never change files outside `ipo-analysis/`. Never force-push. If the merge is refused, leave the PR open and say why.
- End with a short summary: IPOs opening today (Mainboard / SME), each with its call and upper-band upside, the merged PR
  link, the look-ahead for the next 5 working days, and any source that failed.
