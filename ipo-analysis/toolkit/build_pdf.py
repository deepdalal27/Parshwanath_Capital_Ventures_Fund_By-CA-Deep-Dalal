"""Print an issuer's branded PDF report from report.html.

Usage:  python3 ipo-analysis/toolkit/build_pdf.py <slug>
Writes: ipo-analysis/companies/<slug>/<SLUG>_Report.pdf

report.html renders the same dashboard as the website (charts.js + dashboard.js) from
companies/<slug>/charts.json, plus a cover page, the full note and the disclaimer. This script
serves ipo-analysis/ on a local port, opens the page in headless Chromium (Playwright; uses
/opt/pw-browsers/chromium when present), waits for window.REPORT_READY and prints A4.
"""
import functools
import html
import json
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHROMIUM = "/opt/pw-browsers/chromium"


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def build(slug):
    d = os.path.join(ROOT, "companies", slug)
    if not os.path.exists(os.path.join(d, "charts.json")):
        print(f"{slug}: no charts.json, PDF skipped (run build_charts.py first)")
        return None
    disc = json.load(open(os.path.join(ROOT, "data", "disclaimer.json"), encoding="utf-8"))
    tag = slug.upper().replace("-", "_")[:24]
    out = os.path.join(d, f"{tag}_Report.pdf")
    e = html.escape
    footer = (f'<div style="font-size:7px;width:100%;padding:0 13mm;color:#666;display:flex;justify-content:space-between;'
              f'font-family:Arial,sans-serif"><span>{e(disc["entity"])} | SEBI Reg. CAT III AIF IN/AIF3/25-26/2108 | '
              f'Fund Manager: CA Deep Dalal | Sponsor: Jignesh Shah</span>'
              f'<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')

    srv = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            kw = {"executable_path": CHROMIUM} if os.path.exists(CHROMIUM) else {}
            browser = pw.chromium.launch(**kw)
            page = browser.new_page(viewport={"width": 794, "height": 1123})       # A4 at 96 dpi
            page.route("**/fonts.googleapis.com/**", lambda r: r.abort())           # offline-safe: system fonts
            page.goto(f"http://127.0.0.1:{srv.server_address[1]}/report.html?c={slug}", wait_until="load")
            page.wait_for_function("window.REPORT_READY === true", timeout=60000)
            page.emulate_media(media="print")
            page.pdf(path=out, format="A4", print_background=True, display_header_footer=True,
                     header_template="<div></div>", footer_template=footer,
                     margin={"top": "14mm", "bottom": "16mm", "left": "13mm", "right": "13mm"})
            browser.close()
    finally:
        srv.shutdown()
    print(f"pdf: {out}")
    return os.path.basename(out)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        build(s)
