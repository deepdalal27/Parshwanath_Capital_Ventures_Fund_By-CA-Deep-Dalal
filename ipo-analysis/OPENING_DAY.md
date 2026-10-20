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
Write `note.md` in the nine-part structure in `ROUTINE.md` ("Report structure"), with its exact headings. On opening day
also cover, inside those parts:
- Basis banner: RHP date, audited-to date and staleness; open / close / allotment / listing dates; price band, lot size
  and minimum application; issue size split fresh vs OFS; exchanges.
- Part 5: the ratios at the upper band, post-issue, and the earnings-quality test (`### Is the reported P/E right?`) with the
  adjusted P/E and reason flags (`ROUTINE.md`, "Earnings quality").
- Part 7: peers from the RHP's "Basis for Offer Price" plus our own if the list is thin (marked "added by us"); peer
  data goes into `facts.valuation.peers`; upside against the upper band as a percentage only.
- Part 9: the call judged at the upper band.
- Appendix A: the anchor book (investors, amount, MF share, lock-in, source) and subscription at the time of writing.
Every number carries an RHP page cite.

### SME: snapshot report
The same nine parts and headings, each kept short (about two pages in all), with the same rules on sourcing and
neutrality. Set `meta.depth` to `"Snapshot"`. `facts.json` still needs the valuation inputs, drivers and peers so the
model and charts build.

### meta.json additions
On top of the fields in `toolkit/FACTS_SCHEMA.md`: `stage` = `"RHP"`, `price_band` (e.g. `"Rs 285-300"`),
`open_date`, `close_date`, `allotment_date`, `listing_date`, `lot_size`, `exchange`, `depth` (`"Full"` or `"Snapshot"`),
`business_stage` (the classification in part 1), `anchor` (`{ "amount_cr": , "investors": , "mf_share": , "source": }`),
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
