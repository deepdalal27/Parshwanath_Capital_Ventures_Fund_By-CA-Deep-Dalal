# IPO Desk - standing instructions (RHP-stage research, fully automatic)

This file is the single SOP for the IPO Desk. A scheduled run reads it twice a day and follows it without being asked.
Edit it on GitHub to change what the desk does; the next run picks up the change.

**What the desk delivers.** For every Indian IPO (Mainboard and SME) whose **Red Herring Prospectus is filed and whose
price band is announced**, a full report goes live on the website - before the issue opens - with no request from the
fund manager. DRHPs are not covered.

| | |
|---|---|
| Trigger | Price band announced for an issue with a filed RHP (NSE issue calendar), or a new RHP on SEBI |
| Schedule | Every day at 07:43 and 18:43 IST (scheduled task "IPO Desk - RHP reports (auto)"; two runs, so a band announced in the evening is covered by next morning) |
| Worklist | `data/calendar.json`, written by `toolkit/scan_rhp.py` |
| Depth | Mainboard: full nine-part report. SME: the same nine parts, shorter (`meta.depth` = `"Snapshot"`) |
| Publish | Automatic: the run merges its own pull request into `main`; GitHub Pages redeploys |
| Deadline | Live before the issue opens; if the band is announced the evening before, by 09:30 IST on opening day |

## Hard rules (override everything below)

1. **Never invent a figure.** If the document is silent, leave the key out of `facts.json` (the workbook cell stays blank),
   and add the item to `facts.screening.gaps` and to the note's data-gaps table with a severity.
2. **Disclaimer: use the firm-approved text, never write your own.** It lives in `data/disclaimer.json`. The website,
   every Excel workbook and every PDF read it automatically. End each `note.md` with the heading
   `## Disclaimer and disclosures` followed by the `short` text from that file. To change the wording, edit `disclaimer.json` only.
3. **Never commit offer-document PDFs** (size and copyright). Link to the source URL in `meta.json.doc_url`.
4. **Offer document only.** The issuer analysis comes only from the RHP (or, while the RHP cannot be fetched, the latest
   SEBI-filed offer document plus the exchange's issue page, marked provisional - see step 3); never from memory, news
   articles or aggregator summaries. The single exception is the
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
9. **Coverage: RHP with a price band, nothing else** (fund manager's instruction, 26-Oct-2026). Every Mainboard and SME IPO
   whose RHP is filed and whose price band is announced gets a report. DRHPs are never analysed or listed on the site.
   Old DRHP screens live in `archive/drhp/` and are not linked.

## Each run

### 0. Setup
```bash
pip install -q -r ipo-analysis/toolkit/requirements.txt pypdf
(apt-get install -y -q poppler-utils || true)
git fetch origin main
```
Work on the session's designated development branch if it has one (the scheduled run lives in a session whose branch is
`claude/hopeful-knuth-8hoypv`), otherwise on `ipo-desk/<YYYYMMDD-HHMM>`. Restart that branch from `origin/main` each run
(`git checkout -B <branch> origin/main`); if the remote branch still carries already-merged history, keep the push a
fast-forward with `git merge -s ours origin/<branch>` before pushing (never force-push).

### 1. Scan
```bash
python3 ipo-analysis/toolkit/scan_rhp.py --todo
```
It reads the NSE current and upcoming issue feeds (Mainboard and SME), the issue detail pages (lot size, issue size,
BRLMs, RHP and anchor links) and SEBI's register of red herring prospectuses (with the RHP PDF link), and writes
`data/calendar.json`. Each issue is `Open`, `Upcoming` or `Closed` (kept 30 days) and its report is `published`,
`provisional` (built without the RHP) or `to_do`. The `TODO` lines are this run's work; also refresh every
`provisional` report whose `rhp_pdf` has now appeared. Errors (a blocked host) are listed at the end; record them in
the run summary, never work around a block.

### 2. Get the RHP
In order: `rhp_pdf` from the calendar (SEBI attachdocs PDF; extension may be `.PDF`); the SEBI filing page
`rhp_filing`; the NSE `rhp_zip` (nsearchives.nseindia.com - may be blocked); the company's investor page; the BRLMs'
sites. Download to `/tmp/ipo/<slug>/` (never into the repo), resuming with `curl -C -` until the size matches
Content-Length. The NSE issue page is the source for price band, lot, dates, issue size and BRLMs.
If no RHP can be fetched, build from the latest SEBI-filed offer document plus the NSE issue page, set
`meta.rhp_read` to `false`, say so in the basis banner and data gaps, and refresh the report on a later run once the RHP
is reachable. With the RHP, set `meta.rhp_read` to `true`.

### 3. Analyse - every issue, in parallel
- Spawn one subagent per issue (Mainboard first). Each writes only its own `companies/<slug>/` folder, never
  `data/*.json`, and never commits; if `build_issuer.py` rewrites `data/index.json` it reverts that file. The main
  session collects the results and publishes once.
- Load the `drhp-due-diligence` skill if available; hard rule 6 and the **Report structure** below override it.
- Extract with `pdftotext -layout`; build the page map (printed page vs PDF page).
- Write `facts.json` (Rs crore, page cites; schema `toolkit/FACTS_SCHEMA.md`), `meta.json` and `note.md`.
  `meta.json` carries: company, platform, `stage` = `"RHP"`, filed_on, doc_date, doc_url (SEBI filing page), sector, brlm,
  issue_size_cr, price_band (e.g. `"Rs 313-330"`), open_date, close_date, allotment_date, listing_date, lot_size,
  exchange, depth, `rhp_read`, business_stage, call (judged at the upper band; `Screen only` is never used), call_basis,
  headline (one neutral sentence), red_flags (at most six balanced key observations with numbers), swot, anchor
  (`{amount_cr, investors, mf_share, source}`; "not readable" if the anchor report is blocked), reference_note.
- Valuation inputs: floor and cap = the band; fresh issue amount (or fixed shares) and OFS shares from the RHP.
- Merchant bankers: update `data/merchant_bankers.json` from the RHP's past-issue table (main session only).
- Build and check each issue:
  ```bash
  python3 ipo-analysis/toolkit/build_issuer.py <slug>
  python3 ipo-analysis/toolkit/verify.py          # must end with every check passed
  ```
  Open `view.html?c=<slug>` through `python3 -m http.server` (repo root) with Playwright
  (`executable_path="/opt/pw-browsers/chromium"`): all nine part headings present, charts filled, no console errors;
  open the PDF.

### 4. Publish (automatic)
```bash
python3 ipo-analysis/toolkit/scan_rhp.py          # refresh report statuses after the builds
python3 ipo-analysis/toolkit/build_issuer.py --index
```
Commit on the run's branch, push, open a pull request into `main` titled `IPO Desk: <date> - <company names>` (call and
upper-band upside for each in the description) and **merge it yourself (squash)**: the fund manager has authorised
auto-publishing for the IPO Desk. Never change files outside `ipo-analysis/`, never force-push, never push to `main`
directly. If the merge is refused, leave the PR open and say why. If only `data/calendar.json` changed, publish that the
same way so the site's calendar stays current.

### 5. Report
End with a short summary (it becomes a phone notification): issues open today and opening next, each with its call
and upper-band upside; reports published or refreshed this run, with the merged PR link; provisional reports still
waiting for an RHP; and any blocked host.

## Condensed SOP (when the skill is not available)

**Stage**: every report is an RHP-stage decision, judged at the upper band. State the document and its date, the
audited-to date and the staleness in days in the opening banner.

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
