"""Posts on CA Deep Dalal's personal LinkedIn profile (odd dates; Instagram posts on even dates).

    python run_profile.py --plan                      # is today a posting day, which format, what to avoid
    python run_profile.py --post-file F --dry-run     # render the image and caption only (out/)
    python run_profile.py --post-file F               # upload, wait until post_time, publish, record history
    python run_profile.py --whoami                    # print the member id for LINKEDIN_PERSON_ID (setup)

Environment:
    LINKEDIN_PERSON_ID       member id from --whoami (the "sub" value)
    LINKEDIN_ACCESS_TOKEN    token with w_member_social (or "proxy-injected" when a network secret adds it)

The post JSON is written by the scheduled Claude routine (ROUTINE_PROFILE.md), following PROFILE_RULES.md.
"""
import argparse
import datetime as dt
import json
import os
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "config_profile.json")
HISTORY = os.path.join(HERE, "data", "history_profile.json")
OUT = os.path.join(HERE, "out")
KEYS = ["format", "label", "headline", "dek", "stats", "chart", "points", "takeaway", "caption",
        "hashtags", "alt_text", "sources"]


def load(path, default=None):
    if default is not None and not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_post_day(cfg, day):
    rule = cfg.get("post_on", "odd_dates")
    return {"odd_dates": day.day % 2 == 1, "even_dates": day.day % 2 == 0, "daily": True}.get(rule, False)


def next_format(cfg, history):
    ids = [f["id"] for f in cfg["formats"]]
    used = [p["format"] for p in history["posts"] if p.get("format") in ids]
    if not used:
        return cfg["formats"][0]
    i = (ids.index(used[-1]) + 1) % len(ids)
    return cfg["formats"][i]


def caption_and_tags(post, cfg):
    tags, seen = [], set()
    for t in post.get("hashtags", []) + cfg["hashtags"].get(post["format"], []):
        k = t.lstrip("#").lower()
        if k and k not in seen:
            seen.add(k)
            tags.append(t.lstrip("#"))
    return f"{post['caption'].strip()}\n\n{cfg['disclaimer']}", tags[:5]


def token():
    t = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    if not t:
        sys.exit("Set LINKEDIN_ACCESS_TOKEN (use 'proxy-injected' when the network proxy adds the token)")
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--post-file")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-wait", action="store_true")
    ap.add_argument("--force", action="store_true", help="post even on a non-posting day or twice in a day")
    ap.add_argument("--whoami", action="store_true")
    args = ap.parse_args()

    cfg = load(CONFIG)
    history = load(HISTORY, {"posts": []})
    tz = ZoneInfo(cfg["timezone"])
    now = dt.datetime.now(tz)
    today = now.date().isoformat()
    posted_today = any(p["date"] == today for p in history["posts"])

    if args.whoami:
        import requests
        r = requests.get("https://api.linkedin.com/v2/userinfo", timeout=30,
                         headers={"Authorization": f"Bearer {token()}"})
        print(r.status_code, r.text[:400])
        return

    if args.plan:
        fmt = next_format(cfg, history)
        cutoff = (now.date() - dt.timedelta(days=cfg["history_days_to_avoid_repeats"])).isoformat()
        print(json.dumps({
            "date": today, "weekday": now.strftime("%A"),
            "post_today": is_post_day(cfg, now.date()), "already_posted_today": posted_today,
            "format": fmt, "post_time": cfg["post_time"],
            "recent_headlines_do_not_repeat": [p["headline"] for p in history["posts"] if p["date"] >= cutoff][-20:],
        }, indent=2, ensure_ascii=False))
        return

    if not args.post_file:
        sys.exit("Give --post-file (the routine writes it), or use --plan / --whoami")
    if not args.dry_run and not args.force:
        if posted_today:
            sys.exit(f"Already posted on {today}.")
        if not is_post_day(cfg, now.date()):
            sys.exit(f"{today} is not a posting day ({cfg.get('post_on')}).")

    post = load(args.post_file)
    missing = [k for k in KEYS if k not in post]
    if missing:
        sys.exit(f"{args.post_file} is missing keys: {missing}")
    if post["format"] not in [f["id"] for f in cfg["formats"]]:
        sys.exit(f"Unknown format {post['format']!r}")

    from autopost.render_profile import render_profile
    os.makedirs(OUT, exist_ok=True)
    png = render_profile(post, cfg, now.strftime("%d %b %Y").upper(), os.path.join(OUT, f"profile-{today}.png"),
                         os.path.join(HERE, cfg["presenter"]["photo"]))
    caption, tags = caption_and_tags(post, cfg)
    with open(os.path.join(OUT, f"profile-{today}.json"), "w", encoding="utf-8") as f:
        json.dump({**post, "final_caption": caption, "final_hashtags": tags}, f, indent=2, ensure_ascii=False)
    print(f"Image: {png}\n\n{caption}\n\n" + " ".join("#" + t for t in tags))
    if args.dry_run:
        print("\nDry run: not posted.")
        return

    person = os.environ.get("LINKEDIN_PERSON_ID", "").strip()
    if not person:
        sys.exit("Set LINKEDIN_PERSON_ID (run --whoami once to find it)")
    from autopost.linkedin import LinkedIn, to_commentary
    from run import wait_until
    li = LinkedIn(token(), person if person.startswith("urn:li:") else f"urn:li:person:{person}",
                  cfg["linkedin_api_version"])
    image = li.upload_image(png)
    if not args.no_wait:
        wait_until(cfg["post_time"], tz)
    urn = li.post(to_commentary(caption, tags), image, post["headline"], post["alt_text"])
    print(f"Posted: {urn}  https://www.linkedin.com/feed/update/{urn}/")

    history["posts"].append({"date": today, "format": post["format"], "urn": urn, "headline": post["headline"],
                             "sources": post.get("sources", [])})
    os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
    with open(HISTORY, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
