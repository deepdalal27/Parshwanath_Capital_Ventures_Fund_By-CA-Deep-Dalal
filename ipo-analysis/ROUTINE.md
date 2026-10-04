# Scheduled IPO analysis routine - standing instructions

The scheduled Claude routine reads this file on every run. Edit it on GitHub to change what the routine does;
the next run picks up the change. Settings that change often live in `data/sources.json`.

## Hard rules (override everything below)

1. **Never invent a figure.** If the document is silent, leave the key out of `facts.json` (the workbook cell stays blank),
   and add the item to `facts.screening.gaps` and to the note's data-gaps table with a severity.
2. **Never draft regulatory disclaimer text.** Every note carries the literal line
   `[FIRM-APPROVED SEBI DISCLAIMER AND DISCLOSURE BLOCK TO BE INSERTED]`.
3. **Never commit offer-document PDFs** (size and copyright). Link to the source URL in `meta.json.doc_url`.
4. If a source cannot be reached or a PDF cannot be read, **leave the filing in the queue with a note**. Never analyse from memory,
   news articles or aggregator summaries.
5. Everything published here is public. Write in a neutral, factual register. No position sizing. Upside as a percentage only.
6. Grey market premium is never used and never moves fair value.

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
Take at most `max_per_run` filings from `pending`, in this priority:
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
    exit_route, a one-sentence `headline`, and `red_flags` (at most six, each with the number in it).
  - `note.md`: the due-diligence note, in the report spine below.
- Build and verify:
  ```bash
  python3 ipo-analysis/toolkit/build_issuer.py <slug>
  python3 ipo-analysis/toolkit/verify.py
  ```
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

**Note spine** (`note.md`): basis and staleness banner, then verdict, snapshot, investment summary, company and offer, objects,
financials, key findings, forensic scorecard, valuation, reverse DCF, verdict, *what would change our view* (measurable
conditions verifiable against the RHP), risks, data gaps, verification, disclaimer placeholder.
