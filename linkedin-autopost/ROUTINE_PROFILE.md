# Personal LinkedIn post - routine instructions

A scheduled Claude routine reads this file on odd dates at about 08:20 IST and follows it, together with
`PROFILE_RULES.md`. Instagram @findeependence posts on even dates, so the two never share a day.

## 0. Setup and plan
```bash
cd linkedin-autopost
pip install -q pillow requests
(apt-get install -y -q fonts-dejavu-core fonts-liberation >/dev/null 2>&1 || true)
./history.sh pull
python run_profile.py --plan
```
If `post_today` is false or `already_posted_today` is true, stop and report that in one line.
The plan gives today's `format` (id, label, brief) and recent headlines that must not be repeated.

## 1. Research
Read `PROFILE_RULES.md` first. Pick ONE strong subject for the format's brief from the last 1-2 weeks
of Indian capital markets news, and research it with web search from primary or established sources.
Note every figure with its date and source. For a chart, collect one complete set of 3-8 comparable
figures or 4-12 points over time; otherwise use no chart.

Check overlap with Instagram: fetch the last 10 @findeependence captions with
`curl -sS "https://graph.facebook.com/v23.0/17841472800395651/media?fields=caption,timestamp&limit=10"`
(the token is added by the network proxy; skip this check if it fails) and choose a different subject or angle.

## 2. Write `out/profile.json`
Visual first (see `PROFILE_RULES.md`): a 4-7 slide carousel, or 1 slide when one number or chart says it all.
```json
{
  "format": "<format id from the plan>",
  "label": "<format label from the plan>",
  "headline": "max 70 chars, the post's title (used as the carousel title on LinkedIn)",
  "slides": [
    {"type": "cover", "big": "₹1.2L cr", "big_label": "max 8 words", "title": "max 8 words", "sub": "max 10 words"},
    {"type": "stat", "value": "56%", "label": "max 8 words", "note": "max 10 words"},
    {"type": "chart", "title": "max 8 words", "note": "max 10 words",
     "chart": {"type": "bar", "labels": ["max 12 chars"], "values": [1.2], "unit": "%", "source": "named source"}},
    {"type": "compare", "title": "max 8 words", "a": {"value": "₹500 cr", "label": "max 6 words"},
     "b": {"value": "₹1,800 cr", "label": "max 6 words"}, "note": "max 10 words"},
    {"type": "points", "title": "max 8 words", "items": ["max 6 words", "max 6 words", "max 6 words"]},
    {"type": "end", "title": "the takeaway in one sentence", "sub": "max 10 words"}
  ],
  "caption": "60-120 words, per PROFILE_RULES.md, no hashtags, no disclaimer",
  "hashtags": ["3-5 words without #"],
  "alt_text": "max 250 chars describing the visuals",
  "sources": ["source names or URLs"]
}
```
Rules for slides: start with `cover`, end with `end` (carousel); use only verified figures; `big`, `value`
and chart values come from your notes. Charts: bar for 3-6 comparable figures, line for 5-12 points over
time, values as plain numbers in label order. Mix slide types so the carousel has rhythm (number, chart,
comparison, points). A single-slide post uses one `cover` (with `big`) or one `chart` slide.

## 3. Preview and check
```bash
python run_profile.py --post-file out/profile.json --dry-run
```
Open every `out/profile-<date>-NN.png` and look at it: nothing cut off or overlapping, every number matches
your notes, each slide is understood in 3 seconds on a phone. Too much text on a slide means split or cut it. Re-read the caption against every hard rule and the "fund-manager grade"
standard in `PROFILE_RULES.md`. Fix and preview again if anything is off.

## 4. Post
```bash
LINKEDIN_ACCESS_TOKEN=${LINKEDIN_ACCESS_TOKEN:-proxy-injected} python run_profile.py --post-file out/profile.json
./history.sh push-profile
```
It uploads the carousel (PDF document) or the single image, waits until 09:10 IST, publishes on the profile
and records the post. If LinkedIn refuses the carousel, it posts the cover slide as an image instead. The token is
added by the environment's network proxy for api.linkedin.com and www.linkedin.com; never add or print it.
Do not open a pull request.

If `LINKEDIN_PERSON_ID` is missing, or LinkedIn refuses (401/403, "no rule allows host", expired token),
do not retry repeatedly: send the image (SendUserFile) and the full caption so it can be posted by hand,
and say exactly what is missing.

## 5. Report
End with the format, headline, sources, and a last line that is either
"Posted on LinkedIn (profile): <headline> <link>" or "LinkedIn profile post ready but NOT posted: <reason>".
