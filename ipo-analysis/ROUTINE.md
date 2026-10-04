# Scheduled IPO analysis routine - standing instructions

The scheduled Claude routine reads this file on every run. Edit it on GitHub to change what the routine does;
the next run picks up the change. Settings that change often live in `data/sources.json`.

## Hard rules (override everything below)

1. **Never invent a figure.** If the document is silent, leave the key out of `facts.json` (the workbook cell stays blank),
   and add the item to `facts.screening.gaps` and to the note's data-gaps table with a severity.
2. **Disclaimer: use the firm-approved text, never write your own.** It lives in `data/disclaimer.json`. The website,
   every Excel workbook and every PDF read it automatically. End each `note.md` with the heading
   `## Disclaimer and disclosures` followed by the `short` text from that file. To change the wording, edit `disclaimer.json` only.
3. **Never commit offer-document PDFs** (size and copyright). Link to the source URL in `meta.json.doc_url`.
4. If a source cannot be reached or a PDF cannot be read, **leave the filing in the queue with a note**. The issuer analysis comes
   only from the offer document; never from memory, news articles or aggregator summaries. The single exception is the
   merchant-banker section (current prices, issuer financials, ownership), which may use secondary sources only if each one is
   named and marked unverified.
5. **Neutral stance, always.** Everything published here is public and is the Fund's own analytical view, not advocacy.
   - Give strengths and concerns equal care and prominence. Every positive and every negative carries its number and page cite.
   - No loaded language ("alarming", "stellar", "red flag" as rhetoric). Use plain factual verbs.
   - The call (`Subscribe` / `Neutral` / `Avoid` / `Screen only`) follows from the evidence and the valuation. Lean neither way by default.
   - When the evidence is mixed, say so and say what would resolve it.
   - No position sizing. Upside as a percentage only.
6. Grey market premium is never used and never moves fair value.
7. **Branding:** every output carries the fund logo, the fund name and registration, "Fund Manager: CA Deep Dalal" and
   "Sponsor: Jignesh Shah". The toolkit adds these to Excel and PDF automatically; never strip them.
8. **One offer document per day.** `max_per_run` in `data/sources.json` is 1. Do not raise it without the fund manager's instruction.

## Each run

### 0. Setup
```bash
pip install -q -r ipo-analysis/toolkit/requirements.txt pypdf
(apt-get install -y -q poppler-utils || true)   # pdftotext / pdftoppm if available
```

### 1. Scan for new filings
Read `data/sources.json`. For each source with `"enabled": true`, list the offer documents filed
since `scan_from` (DRHP, RHP, addendum, prospectus; mainboard and SME). For each filing record:
`company`, `platform` (Mainboard/SME), `stage`, `filed_on` (YYYY-MM-DD), `doc_url` (direct PDF if possible) and `source`.
If a listing URL in `sources.json` has moved, find the current one on the same official site, update `sources.json`, and
set `"verified": true` with the date.

A filing is new if its `doc_url` is not in `data/seen.json` and not already in `data/queue.json`. Append new filings to
`queue.json.pending`. Set `queue.json.last_scan` to the current UTC time (`YYYY-MM-DDTHH:MMZ`).

### 2. Pick what to analyse
Take at most `max_per_run` filings (currently **1**) from `pending`, in this priority:
1. An RHP / addendum for an issuer already in `companies/` (the decision stage; supersedes the DRHP note),
2. Mainboard DRHPs, oldest first,
3. SME DRHPs, oldest first.

### 3. Analyse each filing
- Download the PDF to `/tmp` (not the repo). Extract the text with `pdftotext -layout`, or `pypdf` if that is unavailable.
  Build a page map: prospectuses commonly carry three numbering blocks. If the restated-financials annexure is image-only,
  render it and read the images before citing any number from it.
- If the `drhp-due-diligence` skill is available in the session, **load it and follow it**. It is the full standing SOP.
  Otherwise, follow the condensed version below.
- Slug: company name in lower case with hyphens, legal suffix kept (`abc-industries-ltd`). An RHP for an existing slug
  updates that folder: the RHP note supersedes the DRHP note and opens with the DRHP-to-RHP delta register.
- Write into `ipo-analysis/companies/<slug>/`:
  - `facts.json`: figures exactly as restated, with page cites. Schema: `toolkit/FACTS_SCHEMA.md`.
  - `meta.json`: company, platform, stage, filed_on, doc_url, sector, brlm, issue_size_cr, price_band, `call`
    (`Subscribe` / `Avoid` / `Neutral`, or `Screen only` at DRHP stage when there is no price band),
    exit_route, `reference_note` (the price used for upside when no band exists, with its basis), a one-sentence neutral `headline`, and `red_flags`. Despite its name, `red_flags` is the list of **key
    observations**: at most six, balanced between strengths and concerns, each carrying its number.
  - `note.md`: the due-diligence note, in the report spine below.
  - **Merchant banker work:** before writing the merchant-banker section, open `data/merchant_bankers.json`.
    - If a lead manager is not there, add it: `owner` (promoters / key shareholders, with source), `listed` status,
      and the year-wise summary table from the offer document's "Price information of past issues handled by the BRLMs".
    - For every issue in that table, record in `issues[]` its name, sector, issue size and price, listing date,
      listing-day open and the 30/90/180-day changes. Take these **from the offer document**: it is exchange-sourced
      and outranks any website.
    - Then add for each issuer: **current share price with its date**, and **revenue and PAT for the last 3 financial
      years** (or since inception if listed less than 3 years ago), as amounts and % change. Prefer exchange filings;
      otherwise use secondary web sources, mark `"verified": false`, and name the source. Never fill a number you could not source.
    - Reuse existing entries; refresh current prices on each run that cites them.
- Build and verify:
  ```bash
  python3 ipo-analysis/toolkit/build_issuer.py <slug>
  python3 ipo-analysis/toolkit/verify.py
  ```
  `build_issuer.py` also writes the branded PDF report (`<SLUG>_Report.pdf`) from `note.md`. It needs Chromium,
  found at `/opt/pw-browsers/chromium` in the cloud container.
  `verify.py` must end with every check passed. If the issuer's own totals fail to reproduce (expenses do not sum,
  the balance sheet does not balance), say in the note whether the error is in the document or in your extraction.
- Move the filing from `queue.json.pending` to `seen.json.filings` (store its `doc_url`).

### 4. Publish
- Rebuild the index: `python3 ipo-analysis/toolkit/build_issuer.py --index`.
- Commit on a new branch, push, and open a pull request into `main` titled `IPO analysis: <company names>`.
  **Do not merge it.** The fund manager reviews the PR and clicks Merge; GitHub Pages then redeploys the site from `main`.
  The PR description lists each issuer with its call, headline and red flags, so it can be reviewed from a phone.
- If an earlier routine PR is still open and unmerged, push to that same branch instead of opening a second PR.
- If nothing new was analysed but the queue or `last_scan` changed, publish that the same way so the pipeline stays current.
- End the run with a short summary: filings found, analysed, still queued, and any source that failed.

## Condensed SOP (when the skill is not available)

**Stage**: a DRHP is a *screen*, an RHP is a *decision*. State the stage, the document date, the audited-to date and the
staleness in days in the opening banner. Where the audited record is more than a year old, say that no capital should be
committed until the RHP is read.

**Exit route**: default to a 2-3 year hold and say it is assumed. Anchor allotments are discretionary and locked in
(50% for 30 days, 50% for 90 days), so they cannot be sold on listing day.

**Ten forensic checks**: (1) bonus issue before filing and share-count consistency; (2) cash flow statement and cumulative
CFO/PAT; (3) current vs deferred tax; (4) related-party capex and funds into subsidiaries; (5) objects arithmetic as a price
floor; (6) revaluation reserve; (7) goodwill vs tangible equity; (8) customer, supplier and geographic concentration, with the
supply side tested separately; (9) contingent liabilities and the materiality threshold; (10) investor presentation vs the filed
document. Also: auditor qualifications, CARO audit trail, monitoring agency, eligibility re-computation, and the SME
conditions as currently in force.

**Twelve work blocks**: earnings quality; working capital (incremental NWC per rupee of incremental revenue);
receivables/payables/inventory ageing; revenue integrity; margin bridge; balance sheet and banking; objects tested;
post-issue dilution (ROE post-money, promoter WACA); related parties in full; management and governance (with auditor
forensics); corporate record; industry (who paid for the industry report).

**Valuation**: restated financials, never annualise a stub. Bear / Neutral / Bull drivers each with a rationale and page cite.
DCF and relative shown separately, then blended 60:40 (80:20 if there are no listed peers). Terminal growth 4.50%.
P/E, EV/EBITDA and P/B, no EV/Sales. Peers matched on business model, disclosed as ours if the document gives none.
Use of proceeds funds capex in Neutral and Bull only. Report the divergence between DCF and relative when above 25%.
Run the reverse DCF and say in plain words what the price asks for.

**Note spine** (`note.md`), in this order:
1. Basis and staleness banner.
2. Verdict, stated neutrally.
3. Snapshot table.
4. **Business model:** what is sold, to whom, how it is priced, how the company earns its margin, and what it owns vs outsources.
5. **Industry analysis:** market size and growth, structure and fragmentation, the competitors named and unnamed,
   regulation and cyclicality. State who commissioned the industry report.
6. **Moat:** what protects returns, such as scale, cost, switching costs, brands, licences or network. Say how durable each
   one is and what evidence supports it. Say plainly when there is none.
7. **Revenue and profit growth drivers:** volume vs price / mix for revenue; gross margin, operating leverage and
   one-offs for profit. Quantify each from the document.
8. **SWOT**, as a table of strengths, weaknesses, opportunities and threats, each item with a figure and page cite.
9. The offer and objects.
10. Financials and key findings: positives and concerns side by side.
11. Forensic scorecard.
12. **Merchant banker(s):**
    - name, owner, issues handled (year-wise summary);
    - for each recent issue: listing premium/discount, 30/90/180-day performance, current price, sector, and revenue and
      PAT growth (amount and %) over 3 years or since inception, with the source for each;
    - a neutral read of the track record.
13. Valuation and reverse DCF.
14. *What would change our view*: measurable conditions verifiable against the RHP.
15. Risks.
16. Data gaps.
17. Verification.
18. `## Disclaimer and disclosures`, followed by the `short` text from `data/disclaimer.json`.
