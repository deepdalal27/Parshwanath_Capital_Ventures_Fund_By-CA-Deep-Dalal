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
```json
{
  "format": "<format id from the plan>",
  "label": "<format label from the plan>",
  "headline": "max 75 chars, the insight itself",
  "dek": "max 110 chars, one line that frames it, or empty",
  "stats": [{"label": "max 20 chars", "value": "max 12 chars", "change": "signed change with period, or empty"}],
  "chart": {"type": "bar | line | none", "title": "what and period, max 55 chars", "unit": "%",
            "labels": ["max 16 chars"], "values": [1.2], "source": "named source"},
  "points": ["3-4 points, max 120 chars each, each with a fact or a mechanism"],
  "takeaway": "max 110 chars, the judgement",
  "caption": "150-260 words, per PROFILE_RULES.md, no hashtags, no disclaimer",
  "hashtags": ["3-5 words without #"],
  "alt_text": "max 250 chars describing the image",
  "sources": ["source names or URLs"]
}
```
Use `"stats": []` and `"chart": {"type": "none", "title": "", "unit": "", "labels": [], "values": [], "source": ""}`
when there is no verified data set. Bar values are plain numbers in the same order as labels.
Space on the card: with stat tiles AND a chart, write only 2 points of max 90 chars (the card drops points
that do not fit); with only one of them, 3 points; with neither, 3-4 points. Use a chart only when it
shows something the words cannot.

## 3. Preview and check
```bash
python run_profile.py --post-file out/profile.json --dry-run
```
Open `out/profile-<date>.png` and look at it: nothing cut off or overlapping, every number matches your
notes, it reads well on a phone. Re-read the caption against every hard rule and the "fund-manager grade"
standard in `PROFILE_RULES.md`. Fix and preview again if anything is off.

## 4. Post
```bash
LINKEDIN_ACCESS_TOKEN=${LINKEDIN_ACCESS_TOKEN:-proxy-injected} python run_profile.py --post-file out/profile.json
./history.sh push-profile
```
It uploads the image, waits until 09:10 IST, publishes on the profile and records the post. The token is
added by the environment's network proxy for api.linkedin.com and www.linkedin.com; never add or print it.
Do not open a pull request.

If `LINKEDIN_PERSON_ID` is missing, or LinkedIn refuses (401/403, "no rule allows host", expired token),
do not retry repeatedly: send the image (SendUserFile) and the full caption so it can be posted by hand,
and say exactly what is missing.

## 5. Report
End with the format, headline, sources, and a last line that is either
"Posted on LinkedIn (profile): <headline> <link>" or "LinkedIn profile post ready but NOT posted: <reason>".
