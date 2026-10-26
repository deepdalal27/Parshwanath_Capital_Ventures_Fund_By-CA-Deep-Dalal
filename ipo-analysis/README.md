# IPO Desk

A section of the fund website at `/ipo-analysis/`. It covers **every Indian IPO whose Red Herring Prospectus is filed and
whose price band is announced**, and publishes a full report before the issue opens. Draft prospectuses (DRHPs) are not
covered. Everything is produced and published automatically by a scheduled run twice a day.

| Path | What it is |
|---|---|
| `ROUTINE.md` | The standing SOP the scheduled run follows: scan, fetch the RHP, analyse, verify, publish |
| `toolkit/scan_rhp.py` | Scans the NSE issue calendar and SEBI's RHP register; writes `data/calendar.json` (the worklist) |
| `data/calendar.json` | Issues with a price band: open / upcoming / closed (30 days), RHP links and report status |
| `data/index.json` | One summary row per published RHP-stage report (built by `toolkit/build_issuer.py --index`) |
| `companies/<slug>/` | Per issue: `facts.json`, `meta.json`, `note.md`, three Excel models, `charts.json`, the PDF report |
| `data/disclaimer.json` | The firm-approved disclaimer, read by the website, every workbook and every PDF |
| `data/merchant_bankers.json` | Lead managers and the track record of their past issues |
| `toolkit/` | Builders for the workbooks, charts and PDF, and `verify.py`, the gate every build must pass |
| `archive/drhp/` | Earlier DRHP screens, kept for the record and not linked from the site |

Website: `index.html` (open now, opening soon, recently closed, method), `view.html?c=<slug>` (the report with charts),
`report.html?c=<slug>` (print layout used for the PDF).
