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
6. **Investor's lens, not a forensic auditor's lens** (fund manager's instruction, 19-Oct-2026). This rule overrides the
   `drhp-due-diligence` skill wherever the two differ.
   - The report answers one question: *is this a sound investment at this price over the holding period?* It does not
     set out to find fault with the accounts. Lead with the business, its growth, its position and its valuation.
   - **Normal features are context, not deductions.** Customer or sector concentration typical of the industry, working
     capital built up during growth or in lumpy order cycles, disclosed related-party dealings, an offer for sale,
     promoter pay within norms, small tax disputes, bank guarantees, an issuer-paid industry report, routine litigation:
     report each once, in proportion, with its number, under **Points to monitor**. They never cut fair value on their
     own and never appear in the headline or verdict unless they are material.
   - **Material** means it would change the investment case: going-concern doubt, an auditor qualification or a
     resignation for cause, fraud or regulatory action against the company or promoters, undisclosed related-party
     dealings, misstated figures, profits that have not converted to cash over a full cycle with no business reason,
     or proceeds that benefit promoters. Only a material issue can make a check `FAIL`; anything else is `WATCH` at most.
   - **Valuation without a strict stance.** House defaults: company-specific premium 0%, no discount to the peer median,
     DCF:relative blend 50:50 (70:30 when no listed peer exists). In the Neutral case use through-cycle (three-year
     average) margins and working-capital intensity, not the worst year; the Bear case carries the stress. Terminal ROIC in
     the Neutral case is not set below WACC unless the business has never earned its cost of capital. When DCF and relative
     diverge, explain why in plain words and give the market's pricing of peers its due weight; a trough-year DCF does
     not decide the call by itself.
   - **The call follows a fixed rule** on the Neutral blended value against the upper band (or reference price):
     `Subscribe` at -10% or better; `Neutral` between -10% and -30%, or whenever the Bull value is at or above the price;
     `Avoid` only when the Neutral value is more than 30% below the price **and** the Bull value is also below it, or when
     there is a material issue. State which limb applied.
   - Words: "points to monitor", not "red flags" or "concerns"; "the price assumes", not "the price rests on".
7. Grey market premium is never used and never moves fair value.
8. **Branding:** every output carries the fund logo, the fund name and registration, "Fund Manager: CA Deep Dalal" and
   "Sponsor: Jignesh Shah". The toolkit adds these to Excel and PDF automatically; never strip them.
9. **One offer document per day.** `max_per_run` in `data/sources.json` is 1. Do not raise it without the fund manager's instruction.

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
   **unless its issue opens within the next 5 working days**: those are covered by the opening-day routine
   (`OPENING_DAY.md`, see `data/opening_calendar.json`), so leave them in the queue for it,
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
  - `note.md`: the report, in the nine-part **Report structure** below. It applies whether or not the skill is loaded and overrides the skill's own spine.
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
  `build_issuer.py` also writes `charts.json` (the data behind every chart on the website dashboard and in the PDF) and the
  branded PDF report (`<SLUG>_Report.pdf`), printed from `report.html` with Chromium (`/opt/pw-browsers/chromium` in the
  cloud container). Charts are generated automatically for every issue; **the inputs below must be present for them to fill:**
  - `facts.json` → `kpi.ebitda` (3 years, Rs crore, as the issuer's KPI table) and, where disclosed, `kpi.volume` with
    `kpi.volume_unit` (production or sales volume). Cite the page in `kpi._cite`.
  - `meta.json` → `swot` with four lists (`strengths`, `weaknesses`, `opportunities`, `threats`); each item carries a figure
    and a page reference. `reference_note` when there is no price band.
  - `facts.screening.checks` filled for every check worked (PASS / WATCH / FAIL / N.A., with page and finding). The
    "Where to focus" panel ranks FAIL, then WATCH, then model guards, then High/Medium data gaps.
  - `data/merchant_bankers.json` updated for this offer's lead managers (see above).
- Before publishing, open `ipo-analysis/view.html?c=<slug>` through a local server
  (`python3 -m http.server` from the repo root) and check that every chart has data and nothing overlaps. Then open the PDF.
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
DCF and relative shown separately, then blended 50:50 (70:30 if there are no listed peers). Terminal growth 4.50%.
Apply the investor's lens in hard rule 6 (through-cycle Neutral case, no company-specific premium or peer discount by default).
P/E, EV/EBITDA and P/B, no EV/Sales. Peers matched on business model, disclosed as ours if the document gives none.
Use of proceeds funds capex in Neutral and Bull only. Report the divergence between DCF and relative when above 25%.
Run the reverse DCF and say in plain words what the price asks for.

**Report structure (`note.md`)** - the fund manager's nine-part order (19-Oct-2026). The website and the PDF place each
part next to its charts by reading these exact `##` headings, so use them word for word:

- `# <Company>: <stage> note`, then a `>` basis banner: document and date, audited-to date and staleness, price band, dates,
  sources outside the offer document, holding period assumed, grey market premium not used.
- `## 1. Business of the company` - what is sold, to whom, how it is priced, how it earns its margin, what it owns vs
  outsources, revenue mix; and the **stage of the business** (start-up / early growth / scaling / mature / turnaround /
  declining) with the evidence and what it means for valuation.
- `## 2. Industry outlook` - market size and growth, structure, named and unnamed competitors, regulation, cyclicality,
  peers' recent growth. Say who commissioned the industry report.
- `## 3. Moat and SWOT analysis` - the moat (scale, cost, switching costs, brand, licences, technology, network), how
  durable and on what evidence; then `### SWOT` as a table, each item with a figure and page cite.
- `## 4. Management analysis and governance` - promoters and their record, board and independence, KMP, pay against
  profit, shareholding before and after, who sells and at what cost, related parties, litigation, auditor, banking;
  end with a short governance read.
- `## 5. Historical financials and ratios` - three years and the stub: revenue, growth, margins, PAT, cash flow,
  working capital, debt, net worth, ROE, ROCE; the ratios at the issue price (market cap, P/E, P/B, EV/EBITDA).
  Inside part 5 add `### Is the reported P/E right?` (the earnings-quality test below).
- `## 6. Future outlook and projections` - order book or pipeline, capacity, new products, what management says,
  and Bear / Neutral / Bull projections with their drivers; what is contracted and what has to go right.
- `## 7. Valuation: DCF and peer comparison (P2P)` - the peer table (issuer at the upper band against listed peers and
  the median), the DCF inputs, WACC build and five-year projection, the scenario table (DCF, relative, fair value,
  upside), sensitivity, why the methods differ, and the reverse DCF in plain words.
- `## 8. Areas to watch and growth drivers` - the growth drivers to track and the **points to monitor** (normal-course
  items, each with its number), plus *what would change our view* as measurable conditions.
- `## 9. Conclusion` - the call under the rule in hard rule 6 (say which limb applied), the price it was judged at,
  the fair value range, and the one or two things that decide it.
- `## Appendix A: Offer, anchor book and lock-ins`, `## Appendix B: Merchant bankers` (track record as below),
  `## Appendix C: Diligence checks` (the scorecard; `FAIL` only for material issues), `## Appendix D: Data gaps and
  verification`.
- `## Disclaimer and disclosures`, followed by the `short` text from `data/disclaimer.json`.

**Earnings quality: is the reported P/E right?** Run on every report and record it in `facts.earnings_quality`
(schema in `toolkit/FACTS_SCHEMA.md`); the site and the PDF show reported and adjusted P/E side by side with the reasons.
Look for, in the accounting policies, the PPE / intangibles / CWIP schedules, the expense notes and MD&A:
1. Costs capitalised instead of expensed: development and R&D staff cost in intangibles or CWIP, software, pre-operative
   or trial-run expenses, borrowing costs, overheads in inventory. Compare additions with the R&D expense and with prior years.
2. Provisions released or under-booked: warranty, bad debts / expected credit loss, inventory obsolescence, gratuity and leave,
   "liabilities no longer required written back".
3. Expenses deferred or not yet charged: contracted but undrawn promoter pay, ESOP cost not expensed, related-party rent or
   services below market, royalties stopped by an asset purchase.
4. Policy changes: depreciation or amortisation lives, revenue recognition, consolidation perimeter.
5. One-off or non-operating income inside PAT: exceptional gains, asset sales, insurance claims, exchange gains, interest on
   IPO-bound or temporary cash.
6. Items that **raise** earnings too (non-cash amortisation of acquired intangibles, one-off charges): record them, so the test
   stays two-sided.
Rules: adjust only with a figure and a page cite; pre-tax by year, negative reduces profit; `include: true` only where the
item changes recurring earnings (confidence High or Medium), otherwise show it as information. State the verdict in plain
words: reported P/E fair (adjustments within 10% of PAT) or flattered / understated, with the adjusted P/E and the
three-year average P/E reported and adjusted. Items that pass go in `checked`. An earnings adjustment is not by itself a
material issue under hard rule 6; it changes the call only through the valuation. In part 7, state the relative value on
the latest adjusted EPS and on the three-year average adjusted EPS; the Neutral case uses the through-cycle figure.

Merchant banker appendix: name, owner, issues handled (year-wise summary); for each recent issue the listing premium or
discount, 30/90/180-day performance, current price, sector, and revenue and PAT growth over three years with sources;
a neutral read of the track record.
