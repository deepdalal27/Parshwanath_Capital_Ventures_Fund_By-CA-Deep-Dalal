"""Render an issuer's note.md into a branded A4 PDF report.

Usage:  python3 ipo-analysis/toolkit/build_pdf.py <slug>
Writes: ipo-analysis/companies/<slug>/<SLUG>_Report.pdf

The page carries the fund logo, the fund / Fund Manager / Sponsor names, the valuation
summary from meta.json, the full note and the disclaimer from data/disclaimer.json.
Printed with headless Chromium through Playwright (uses /opt/pw-browsers/chromium when present).
"""
import base64
import html
import json
import os
import sys

import re

import markdown


def normalise_md(text):
    """Python-Markdown needs a blank line before a list and 4-space nesting; notes are written GitHub-style."""
    out, prev = [], ""
    item = re.compile(r"^(\s*)([-*+]|\d+\.)\s")
    for line in text.splitlines():
        m = item.match(line)
        if m:
            line = " " * (len(m.group(1)) * 2) + line.lstrip()          # 2-space nesting -> 4-space
            if prev.strip() and not item.match(prev) and not prev.startswith((" ", "\t")):
                out.append("")
        elif line.startswith("  ") and out and item.match(out[-1] if out[-1] else " "):
            line = "  " + line                                              # keep continuation lines inside the item
        out.append(line)
        prev = line
    return "\n".join(out)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHROMIUM = "/opt/pw-browsers/chromium"

CSS = """
@page { size: A4; margin: 18mm 18mm 20mm 18mm; }
* { box-sizing: border-box; }
body { font: 10pt/1.5 "Inter", "Segoe UI", Arial, sans-serif; color: #0b0f16; margin: 0; }
.brand { display: flex; align-items: center; gap: 14px; border-bottom: 2px solid #c9a86a; padding-bottom: 10px; }
.brand img { width: 64px; height: 64px; }
.brand .n { font: 600 15pt Georgia, serif; color: #1F3864; }
.brand .s { font-size: 8.5pt; color: #5d6673; }
.people { font-size: 8.5pt; color: #0b0f16; margin-top: 2px; }
h1 { font: 400 22pt Georgia, serif; margin: 18px 0 4px; }
.meta { color: #5d6673; font-size: 9pt; margin-bottom: 10px; }
.call { display: inline-block; font: 600 9pt monospace; padding: 3px 8px; border-radius: 3px; background: #f4f1ec; }
.headline { font-size: 11pt; margin: 8px 0 12px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 8.8pt; page-break-inside: avoid; }
th, td { border: 1px solid #d8d1c5; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #1F3864; color: #fff; font-weight: 600; }
td.n, th.n { text-align: right; }
h2 { font: 400 14pt Georgia, serif; color: #1F3864; border-top: 1px solid #e9e4db; padding-top: 8px; margin-top: 18px;
     page-break-after: avoid; }
h3 { font-size: 10.5pt; margin: 12px 0 4px; page-break-after: avoid; }
blockquote { margin: 8px 0; padding: 6px 10px; border-left: 3px solid #c9a86a; background: #fbfaf7; }
code { font-size: 8.5pt; background: #f4f1ec; padding: 0 3px; }
ul { padding-left: 18px; }
.flags li { margin: 2px 0; }
.disc { page-break-before: always; font-size: 8.5pt; color: #333; }
.disc h2 { margin-top: 0; }
"""


def fmt(v, pct=False):
    if not isinstance(v, (int, float)):
        return "-"
    return f"{v * 100:.1f}%" if pct else f"{v:,.2f}"


def build(slug):
    d = os.path.join(ROOT, "companies", slug)
    meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
    note_p = os.path.join(d, "note.md")
    if not os.path.exists(note_p):
        print(f"{slug}: no note.md, PDF skipped")
        return None
    disc = json.load(open(os.path.join(ROOT, "data", "disclaimer.json"), encoding="utf-8"))
    logo = base64.b64encode(open(os.path.join(ROOT, "assets", "logo-128.png"), "rb").read()).decode()
    body = markdown.markdown(normalise_md(open(note_p, encoding="utf-8").read()), extensions=["tables", "sane_lists"])
    e = html.escape
    model = meta.get("model") or {}
    rows = "".join(
        f"<tr><td>{k.title()}</td><td class=n>{fmt((model.get(k) or {}).get('dcf'))}</td>"
        f"<td class=n>{fmt((model.get(k) or {}).get('relative'))}</td><td class=n>{fmt((model.get(k) or {}).get('blended'))}</td>"
        f"<td class=n>{fmt((model.get(k) or {}).get('upside_cap'), True)}</td></tr>" for k in ("bear", "neutral", "bull"))
    flags = "".join(f"<li>{e(f)}</li>" for f in (meta.get("red_flags") or []))
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="brand"><img src="data:image/png;base64,{logo}" alt="">
  <div><div class="n">{e(disc['entity'])}</div><div class="s">{e(disc['registration'])}</div>
  <div class="people"><b>Fund Manager:</b> CA Deep Dalal &nbsp;|&nbsp; <b>Sponsor:</b> Jignesh Shah</div></div></div>
<h1>{e(meta.get('company') or slug)}</h1>
<div class="meta">{e(meta.get('platform') or '')} &middot; {e(meta.get('stage') or '')} &middot; filed {e(meta.get('filed_on') or '-')}
  &middot; lead manager(s): {e(meta.get('brlm') or '-')} &middot; issue size Rs {fmt(meta.get('issue_size_cr'))} cr
  &middot; price band: {e(meta.get('price_band') or 'not announced')}</div>
<span class="call">Call: {e(meta.get('call') or 'Pending')}</span>
<p class="headline">{e(meta.get('headline') or '')}</p>
<table><tr><th>Scenario (Rs/share)</th><th class=n>DCF</th><th class=n>Relative</th><th class=n>Blended</th><th class=n>Upside vs reference</th></tr>{rows}</table>
{f'<h3>Key observations</h3><ul class="flags">{flags}</ul>' if flags else ''}
{body}
<div class="disc"><h2>{e(disc['title'])}</h2>{''.join(f'<p>{e(p)}</p>' for p in disc['paragraphs'])}</div>
</body></html>"""
    tag = slug.upper().replace("-", "_")[:24]
    out = os.path.join(d, f"{tag}_Report.pdf")
    footer = (f'<div style="font-size:7px;width:100%;padding:0 18mm;color:#666;display:flex;justify-content:space-between">'
              f'<span>{e(disc["entity"])} | SEBI Reg. CAT III AIF IN/AIF3/25-26/2108 | Fund Manager: CA Deep Dalal | '
              f'Sponsor: Jignesh Shah</span><span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        kw = {"executable_path": CHROMIUM} if os.path.exists(CHROMIUM) else {}
        browser = pw.chromium.launch(**kw)
        pg = browser.new_page()
        pg.set_content(page, wait_until="load")
        pg.pdf(path=out, format="A4", print_background=True, display_header_footer=True,
               header_template="<div></div>", footer_template=footer,
               margin={"top": "18mm", "bottom": "20mm", "left": "18mm", "right": "18mm"})
        browser.close()
    print(f"pdf: {out}")
    return os.path.basename(out)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        build(s)
