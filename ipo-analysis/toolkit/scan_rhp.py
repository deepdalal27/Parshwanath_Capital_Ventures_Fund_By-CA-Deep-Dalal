"""RHP scanner: builds data/calendar.json, the worklist for the IPO desk.

An issue enters the calendar when it has a price band (NSE current / upcoming issues feed). The SEBI
"Red herring documents filed with RoC" listing is matched in to give the RHP link. Each issue is marked
with the report status:

    published   companies/<slug>/meta.json exists with stage RHP (or Prospectus), built from the RHP
    provisional RHP-stage report built without the RHP (meta.rhp_read false) -> refresh once the RHP is reachable
    to_do       no RHP-stage report yet  -> the routine must produce one

Closed issues stay in the calendar for 30 days after closing so the site can show recent outcomes.

    python3 ipo-analysis/toolkit/scan_rhp.py            # scan and write data/calendar.json
    python3 ipo-analysis/toolkit/scan_rhp.py --todo     # also print the to-do list (one line per issue)

Network: www.nseindia.com and www.sebi.gov.in must be reachable. nsearchives.nseindia.com (RHP and anchor
zips), api.bseindia.com and www.bsesme.com (BSE SME) are optional; when blocked the routine records it.
"""
import datetime as dt
import glob
import json
import os
import re
import sys
import urllib.parse
import subprocess
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CAL = os.path.join(ROOT, "data", "calendar.json")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
KEEP_CLOSED_DAYS = 30


class Session:
    """curl-backed session (NSE rejects Python's TLS client; curl with a cookie jar works)."""

    def __init__(self, ua=UA):
        self.ua = ua
        fd, self.jar = tempfile.mkstemp(suffix=".cookies")
        os.close(fd)


def opener(ua=UA):
    return Session(ua)


def get(op, url, data=None, headers=None, timeout=40):
    cmd = ["curl", "-s", "-S", "--compressed", "-m", str(timeout), "-A", op.ua, "-b", op.jar, "-c", op.jar,
           "-H", "Accept-Language: en-IN,en;q=0.9", "-w", "\n%{http_code}"]
    for k, v in (headers or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    if data is not None:
        cmd += ["--data", data.decode() if isinstance(data, bytes) else data]
    for attempt in range(3):   # SEBI drops TLS handshakes now and then
        r = subprocess.run(cmd + [url], capture_output=True, text=True)
        body, _, code = r.stdout.rpartition("\n")
        if r.returncode == 0 and code.startswith("2"):
            break
        time.sleep(3 * (attempt + 1))
    if r.returncode != 0 or not code.startswith("2"):
        raise RuntimeError(f"HTTP {code or r.returncode} {r.stderr.strip()[:120]}")
    return body


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    s = re.sub(r"-limited$", "-ltd", s)
    return s


def nse_issues(errors):
    op = opener("Mozilla/5.0")
    try:
        get(op, "https://www.nseindia.com/")   # sets the cookies; the page itself answers 403
    except Exception:  # noqa: BLE001
        pass
    hdr = {"Referer": "https://www.nseindia.com/", "Accept": "application/json"}
    out = {}
    for path in ("api/ipo-current-issue", "api/all-upcoming-issues?category=ipo", "api/all-upcoming-issues?category=sme"):
        try:
            d = json.loads(get(op, "https://www.nseindia.com/" + path, headers=hdr) or "{}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"NSE {path}: {e}")
            continue
        rows = d if isinstance(d, list) else d.get("data", []) if isinstance(d, dict) else []
        for x in rows:
            sym = x.get("symbol") or x.get("companyName")
            if not sym:
                continue
            series = (x.get("series") or "").upper()
            out[sym] = {
                "company": (x.get("companyName") or "").strip(),
                "symbol": x.get("symbol"),
                "platform": "SME" if series in ("SM", "SME", "ST") else "Mainboard",
                "series": series,
                "open_date": parse_date(x.get("issueStartDate")),
                "close_date": parse_date(x.get("issueEndDate")),
                "price_band": clean_band(x.get("issuePrice")),
                "issue_size_shares": to_int(x.get("issueSize")),
                "source": "NSE",
            }
            # details (lot, size, listing) from the issue page
            try:
                det = json.loads(get(op, "https://www.nseindia.com/api/ipo-detail?symbol=" +
                                     urllib.parse.quote(x.get("symbol") or "") + "&series=" + (series or "EQ"), headers=hdr))
                info = {i.get("title"): i.get("value") for i in (det.get("issueInfo", {}) or {}).get("dataList", []) if i.get("title")}
                lot = re.search(r"(\d[\d,]*)\s+Equity Shares", str(info.get("Bid Lot", "")))
                out[sym]["lot_size"] = to_int(lot.group(1)) if lot else None
                out[sym]["issue_size_text"] = re.sub(r"\s+", " ", str(info.get("Issue Size", "")).strip('" ')) or None
                out[sym]["brlm"] = str(info.get("Book Running Lead Managers", "")).strip('" ') or None
                out[sym]["rhp_zip"] = info.get("Red Herring Prospectus")
                out[sym]["anchor_zip"] = info.get("Anchor Allocation Report")
            except Exception as e:  # noqa: BLE001
                errors.append(f"NSE ipo-detail {sym}: {e}")
    return list(out.values())


def sebi_rhps(errors, pages=2):
    op = opener()
    base = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=15&smid=11"
    rows = []
    try:
        html = get(op, base)
        rows += parse_sebi(html)
        for p in range(1, pages):
            data = urllib.parse.urlencode({"nextValue": p, "next": "n", "search": "", "fromDate": "", "toDate": "",
                                           "fromYear": "", "toYear": "", "deptId": "-1", "sid": "3", "ssid": "15",
                                           "smid": "11", "ssidhidden": "15", "intmid": "-1", "sText": "Public Issues",
                                           "ssText": "Public Issues", "smText": "Red Herring Documents filed with ROC",
                                           "doDirect": str(p - 1)}).encode()
            rows += parse_sebi(get(op, "https://www.sebi.gov.in/sebiweb/ajax/home/getnewslistinfo.jsp", data=data,
                                   headers={"X-Requested-With": "XMLHttpRequest", "Referer": base}))
    except Exception as e:  # noqa: BLE001
        errors.append(f"SEBI RHP listing: {e}")
    return rows


def parse_sebi(html):
    out = []
    for d, cell in re.findall(r"<td>([A-Z][a-z]{2} \d\d, \d{4})</td>\s*<td>(.*?)</td>", html, re.S):
        u = re.search(r"href=['\"]([^'\"]+)", cell)
        title = re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", cell)).strip()
        t = re.search(r'title="([^"]+)"', cell)
        title = (t.group(1) if t else title).split(" - ")[0].strip()
        out.append({"date": dt.datetime.strptime(d, "%b %d, %Y").date().isoformat(), "title": title,
                    "url": u.group(1) if u else None})
    return out


def parse_date(s):
    if not s:
        return None
    for f in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s.strip(), f).date().isoformat()
        except ValueError:
            pass
    return None


def clean_band(s):
    if not s:
        return None
    n = re.findall(r"\d[\d,]*(?:\.\d+)?", s)
    return ("Rs " + "-".join(x.replace(",", "") for x in n[:2])) if n else None


def to_int(s):
    try:
        return int(str(s).replace(",", "").split(".")[0])
    except (TypeError, ValueError):
        return None


def norm(name):
    return re.sub(r"\b(limited|ltd|private|pvt)\b|[^a-z0-9]", "", (name or "").lower())


def reports():
    out = {}
    for mp in glob.glob(os.path.join(ROOT, "companies", "*", "meta.json")):
        m = json.load(open(mp))
        out[norm(m.get("company"))] = m
    return out


def status_of(issue, today):
    o, c = issue.get("open_date"), issue.get("close_date")
    if o and today < o:
        return "Upcoming"
    if c and today > c:
        return "Closed"
    if o:
        return "Open"
    return "Upcoming"


def main():
    errors = []
    today = dt.datetime.now(IST).date().isoformat()
    prev = json.load(open(CAL)) if os.path.exists(CAL) else {"issues": []}
    issues = {norm(i["company"]): i for i in prev.get("issues", [])}
    for i in nse_issues(errors):
        k = norm(i["company"])
        issues[k] = {**issues.get(k, {}), **{a: b for a, b in i.items() if b is not None}}
    sebi = sebi_rhps(errors)
    sop = opener()
    for k, i in issues.items():
        hits = [s for s in sebi if norm(s["title"]) == k or k in norm(s["title"])]
        rhp = next((h for h in hits if "rhp" in (h["url"] or "").lower() and "addendum" not in h["url"].lower()
                    and "corrigendum" not in h["url"].lower()), None) or (hits[0] if hits else None)
        if rhp:
            i["rhp_filing"] = rhp["url"]
            i["rhp_filed_on"] = rhp["date"]
            if not i.get("rhp_pdf"):
                try:
                    get(sop, "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=15&smid=11")
                    m = re.search(r"file=(https://www\.sebi\.gov\.in/sebi_data/attachdocs/[^'\"&]+?\.pdf)", get(sop, rhp["url"]), re.I)
                    if m:
                        i["rhp_pdf"] = m.group(1)
                except Exception as e:  # noqa: BLE001
                    errors.append(f"SEBI filing page {rhp['url']}: {e}")
        if len(hits) > 1:
            i["sebi_filings"] = [{"date": h["date"], "url": h["url"]} for h in hits]
    reps = reports()
    keep = []
    for k, i in issues.items():
        i["status"] = status_of(i, today)
        m = reps.get(k)
        i["slug"] = (m or {}).get("slug") or i.get("slug") or slugify(i["company"])
        if m and str(m.get("stage", "")).upper() in ("RHP", "PROSPECTUS"):
            i["report"] = "provisional" if m.get("rhp_read") is False else "published"
        else:
            i["report"] = "to_do"
        if i["status"] == "Closed" and i.get("close_date"):
            if (dt.date.fromisoformat(today) - dt.date.fromisoformat(i["close_date"])).days > KEEP_CLOSED_DAYS:
                continue
        keep.append(i)
    keep.sort(key=lambda i: (i.get("open_date") or "9999"))
    out = {"last_scan": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "today_ist": today,
           "coverage": "Every IPO with a filed RHP and an announced price band. DRHPs are not covered.",
           "errors": errors, "issues": keep}
    json.dump(out, open(CAL, "w"), indent=2, ensure_ascii=False)
    print(f"calendar: {len(keep)} issues ({sum(1 for i in keep if i['report'] == 'to_do')} to do); errors: {len(errors)}")
    if "--todo" in sys.argv:
        for i in keep:
            if i["report"] == "provisional" and i["status"] != "Closed":
                print(f"REFRESH {i['slug']} | {i['company']} | built without the RHP | RHP now: {i.get('rhp_pdf') or 'not yet'}")
            if i["report"] == "to_do" and i["status"] != "Closed":
                print(f"TODO {i['slug']} | {i['company']} | {i['platform']} | {i.get('price_band')} | "
                      f"{i.get('open_date')} to {i.get('close_date')} | RHP: {i.get('rhp_pdf') or i.get('rhp_filing') or i.get('rhp_zip')}")
    for e in errors:
        print("ERROR", e)


if __name__ == "__main__":
    main()
