"""Daily LinkedIn post for Parshwanath Capital Ventures Fund.

    python run.py                 # generate, wait until 12:00 IST, post, record in history
    python run.py --dry-run       # generate + render only (image and text saved in out/)
    python run.py --kind quote    # override the weekday schedule
    python run.py --force         # post even if today's post is already recorded
    python run.py --plan          # print today's post type and recently used quotes (for the routine)
    python run.py --post-file F   # use a post Claude already wrote (JSON) instead of calling the API

Free mode (ROUTINE.md): a scheduled Claude Code routine writes the post JSON itself and calls
--post-file, so no ANTHROPIC_API_KEY is needed.

Environment:
    ANTHROPIC_API_KEY             only when the script writes the post itself (no --post-file)
    LINKEDIN_ORG_ID               numeric id of the Company Page
    LINKEDIN_ACCESS_TOKEN         or, to refresh automatically each run:
    LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_REFRESH_TOKEN
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
from zoneinfo import ZoneInfo

from autopost.render import render

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY = os.path.join(HERE, "data", "history.json")
OUT = os.path.join(HERE, "out")
MAX_WAIT_MIN = 60
POST_KEYS = ["kind", "label", "headline", "stats", "chart", "points", "quote", "quote_author",
             "takeaway", "caption", "hashtags", "alt_text", "sources"]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f) if path.endswith(".json") else f.read()


def build_caption(post, cfg):
    tags, seen = [], set()
    for t in post.get("hashtags", []) + cfg["hashtags"][post["kind"]]:
        key = t.lstrip("#").lower()
        if key and key not in seen:
            seen.add(key)
            tags.append(t.lstrip("#"))
    body = (f"{post['caption'].strip()}\n\n"
            f"{cfg['fund_name']} | {cfg['registration_line']}\n"
            f"Address: {cfg['address']}\n\n"
            f"Disclaimer: {cfg['disclaimer']}")
    return body, tags[:6]


def wait_until(post_time, tz):
    hh, mm = map(int, post_time.split(":"))
    now = dt.datetime.now(tz)
    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    secs = (target - now).total_seconds()
    if 0 < secs <= MAX_WAIT_MIN * 60:
        print(f"Waiting {secs / 60:.1f} min until {post_time} {tz.key}")
        time.sleep(secs)


def linkedin_token():
    if os.environ.get("LINKEDIN_REFRESH_TOKEN"):
        from autopost.linkedin import refresh_access_token
        return refresh_access_token(os.environ["LINKEDIN_CLIENT_ID"], os.environ["LINKEDIN_CLIENT_SECRET"],
                                    os.environ["LINKEDIN_REFRESH_TOKEN"])
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    if not token:
        sys.exit("Set LINKEDIN_ACCESS_TOKEN (or the LINKEDIN_REFRESH_TOKEN trio)")
    return token


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-wait", action="store_true")
    ap.add_argument("--kind", choices=["market", "quote"])
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--post-file")
    args = ap.parse_args()

    cfg = load(os.path.join(HERE, "config.json"))
    rules = load(os.path.join(HERE, "POSTING_RULES.md"))
    history = load(HISTORY)
    tz = ZoneInfo(cfg["timezone"])
    now = dt.datetime.now(tz)
    today = now.date().isoformat()

    if not args.dry_run and not args.force and any(p["date"] == today for p in history["posts"]):
        print(f"Already posted for {today}; nothing to do (use --force to post again).")
        return

    kind = args.kind or cfg["schedule"][now.strftime("%A")]
    cutoff = (now.date() - dt.timedelta(days=cfg["history_days_to_avoid_repeats"])).isoformat()
    recent_quotes = [f"{p['quote']} - {p['quote_author']}" for p in history["posts"]
                     if p.get("quote") and p["date"] >= cutoff]

    if args.plan:
        print(json.dumps({"date": today, "weekday": now.strftime("%A"), "kind": kind,
                          "already_posted_today": any(p["date"] == today for p in history["posts"]),
                          "recent_quotes_do_not_reuse": recent_quotes}, indent=2, ensure_ascii=False))
        return

    if args.post_file:
        post = load(args.post_file)
        missing = [k for k in POST_KEYS if k not in post]
        if missing:
            sys.exit(f"{args.post_file} is missing keys: {missing}")
        kind = post["kind"]
        print(f"{today}: using '{kind}' post from {args.post_file}")
    else:
        from autopost.generate import generate
        print(f"{today}: generating '{kind}' post with {cfg['model']}")
        post = generate(cfg, rules, kind, now.strftime("%A, %d %B %Y"), recent_quotes)

    os.makedirs(OUT, exist_ok=True)
    png = render(post, cfg, os.path.join(HERE, "..", cfg["logo"]), now.strftime("%d %b %Y").upper(),
                 os.path.join(OUT, f"{today}.png"), os.path.join(HERE, cfg["presenter"]["photo"]))
    caption, tags = build_caption(post, cfg)
    with open(os.path.join(OUT, f"{today}.json"), "w", encoding="utf-8") as f:
        json.dump({**post, "final_caption": caption, "final_hashtags": tags}, f, indent=2, ensure_ascii=False)
    print(f"Image: {png}\n\n{caption}\n\n" + " ".join("#" + t for t in tags))

    if args.dry_run:
        print("\nDry run: not posted.")
        return

    from autopost.linkedin import LinkedIn, to_commentary
    li = LinkedIn(linkedin_token(), os.environ["LINKEDIN_ORG_ID"], cfg["linkedin_api_version"])
    image = li.upload_image(png)
    if not args.no_wait:
        wait_until(cfg["post_time"], tz)
    title = post["headline"] or f"{post['quote_author']} on investing"
    urn = li.post(to_commentary(caption, tags), image, title, post["alt_text"])
    print(f"Posted: {urn}  https://www.linkedin.com/feed/update/{urn}/")

    history["posts"].append({
        "date": today, "kind": kind, "urn": urn, "headline": post["headline"],
        "quote": post.get("quote", ""), "quote_author": post.get("quote_author", ""),
        "sources": post.get("sources", []),
    })
    with open(HISTORY, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
