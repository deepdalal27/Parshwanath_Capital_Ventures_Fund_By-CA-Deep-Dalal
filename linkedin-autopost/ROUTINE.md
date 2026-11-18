# Daily LinkedIn post - routine instructions (free mode)

A scheduled Claude Code routine reads this file every day at about 11:20 IST and follows it.
Claude writes the post itself, so no Anthropic API key is needed. Edit this file on GitHub to change what
the routine does. The tone and compliance rules are in `POSTING_RULES.md`. Both files bind every run.

## Steps

### 0. Setup
```bash
cd linkedin-autopost
pip install -q pillow requests
(apt-get install -y -q fonts-dejavu-core fonts-liberation >/dev/null 2>&1 || true)
./history.sh pull
python run.py --plan
```
`--plan` prints today's post type (`market` or `quote`), whether today is already posted, and the quotes
used recently. If `already_posted_today` is true, stop and report that.

### 1. Research (web search)
Read `POSTING_RULES.md` first.

- **market**: search for the latest completed session or week of Indian markets: Nifty 50 and Sensex
  close and % change, sector indices, FII/DII flows, INR, crude, 10-year G-sec yield, and the main driver.
  Also collect **one complete chart data set** for the same period: 3-8 comparable figures (for example
  weekly % change of sector indices, or FII vs DII net flows) or 4-12 daily closes of an index.
  Use NSE, BSE, RBI, NSDL or established financial news. Note each figure with its date and source.
- **quote**: choose a genuine investing quote that is not in `recent_quotes_do_not_reuse`. Verify the
  exact wording and the attribution with a search. Pick something that fits this week's market mood.

Never write a number you did not find in today's search. If you cannot verify a chart data set, use
`"chart": {"type": "none", ...}` and the post goes out without a chart.

### 2. Write `out/post.json`
```json
{
  "kind": "market",
  "label": "Market Lens",
  "headline": "max 70 chars",
  "stats": [{"label": "Nifty 50", "value": "25,114", "change": "+0.8% w/w"}, {"...": "3 tiles"}],
  "chart": {"type": "bar", "title": "Sector indices, weekly change (%)", "unit": "%",
            "labels": ["Nifty Bank", "Nifty IT"], "values": [2.4, -2.3], "source": "NSE"},
  "points": ["3 observations, each max 100 chars, each with its figure"],
  "quote": "",
  "quote_author": "",
  "takeaway": "one line, max 120 chars",
  "caption": "90-180 words for LinkedIn, no hashtags, no disclaimer",
  "hashtags": ["3-5 words without #"],
  "alt_text": "max 250 chars describing the image",
  "sources": ["source names or URLs"]
}
```
- For a **quote** post: `"kind": "quote"`, `"label": "Investing Wisdom"`, `"headline": ""`, `"stats": []`,
  `"points": []`, `"chart": {"type": "none", "title": "", "unit": "", "labels": [], "values": [], "source": ""}`,
  and fill `quote` (max 220 chars) and `quote_author`. The script adds CA Deep Dalal's photo and the
  "CA Deep Dalal, Fund Manager" card. The quote stays credited to the person who said it.
- Bar charts: `values` are plain numbers (no % sign) and in the same order as `labels`. Labels max 16 chars.

### 3. Preview and check
```bash
python run.py --post-file out/post.json --dry-run
```
Open the image `out/<date>.png` and look at it. Check that no text is cut off or overlapping, every number
matches your research notes, and no hard rule in `POSTING_RULES.md` is broken. Fix `post.json` and preview
again if anything is wrong.

### 4. Post
```bash
python run.py --post-file out/post.json
```
It uploads the image, waits until 12:00 IST, posts to the Company Page and records it in
`data/history.json`. Then save the history:
```bash
./history.sh push
```
Do not open a pull request. The history lives on the `linkedin-history` branch.

If `LINKEDIN_ORG_ID` or a LinkedIn token is missing, or LinkedIn refuses the request (for example a 403
from the network proxy, or 401 for an expired token), do not retry repeatedly. Finish with the preview
image and caption so the fund manager can post by hand, and state exactly what is missing.

### 5. Report
End with: the post type, the headline or quote, the LinkedIn link printed by the script (or why it was
not posted), and the sources used.
