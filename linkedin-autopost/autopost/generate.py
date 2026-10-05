"""Ask Claude for today's post.

Two calls:
  1. research - Claude uses web search to gather today's verified facts (or verify a quote).
  2. write    - Claude turns the notes into a structured post (JSON schema enforced).
They are separate because structured outputs cannot be combined with web-search citations.
"""
import json

import anthropic

FALLBACK_BETA = "server-side-fallback-2026-07-01"
WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 8}

POST_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["kind", "label", "headline", "stats", "chart", "points", "quote", "quote_author",
                 "takeaway", "caption", "hashtags", "alt_text", "sources"],
    "properties": {
        "kind": {"type": "string", "enum": ["market", "quote"]},
        "label": {"type": "string", "description": "Short kicker, e.g. 'MARKET LENS' or 'INVESTING WISDOM'"},
        "headline": {"type": "string", "description": "Max 70 characters"},
        "stats": {"type": "array", "description": "Market: 3 headline numbers for the stat tiles. Quote: empty.",
                  "items": {"type": "object", "additionalProperties": False,
                            "required": ["label", "value", "change"],
                            "properties": {
                                "label": {"type": "string", "description": "e.g. 'Nifty 50', max 20 chars"},
                                "value": {"type": "string", "description": "e.g. '25,114', max 12 chars"},
                                "change": {"type": "string",
                                           "description": "Signed change with period, e.g. '+0.8% w/w' or '-4 bps'; '' if none"}}}},
        "chart": {"type": "object", "additionalProperties": False,
                  "required": ["type", "title", "unit", "labels", "values", "source"],
                  "description": "Market: the chart for the image, built only from verified figures in the notes. "
                                 "Quote: type 'none'.",
                  "properties": {
                      "type": {"type": "string", "enum": ["bar", "line", "none"],
                               "description": "bar = 3-8 categories compared (sector % moves, FII vs DII flows, "
                                              "index returns); line = 4-12 points over time (daily closes)"},
                      "title": {"type": "string", "description": "Says what and the period, max 55 chars"},
                      "unit": {"type": "string", "description": "Suffix for values, e.g. '%' or '' "},
                      "labels": {"type": "array", "items": {"type": "string"}, "description": "Max 16 chars each"},
                      "values": {"type": "array", "items": {"type": "number"}},
                      "source": {"type": "string", "description": "Data source name, e.g. 'NSE'"}}},
        "points": {"type": "array", "items": {"type": "string"},
                   "description": "Market: exactly 3 observations, each max 100 characters, with its figure. Quote: empty."},
        "quote": {"type": "string", "description": "Quote post: the exact quote, max 220 characters. Market: empty."},
        "quote_author": {"type": "string", "description": "Quote post: who said it. Market: empty."},
        "takeaway": {"type": "string", "description": "One line for the image, max 120 characters"},
        "caption": {"type": "string", "description": "LinkedIn caption, 90-180 words, no hashtags, no disclaimer"},
        "hashtags": {"type": "array", "items": {"type": "string"}, "description": "3-5 words without '#'"},
        "alt_text": {"type": "string", "description": "Image description for accessibility, max 250 characters"},
        "sources": {"type": "array", "items": {"type": "string"}, "description": "Sources used (names or URLs)"},
    },
}


def _call(client, cfg, **kwargs):
    resp = client.beta.messages.create(
        model=cfg["model"],
        max_tokens=16000,
        thinking={"type": "adaptive"},
        betas=[FALLBACK_BETA],
        fallbacks="default",
        **kwargs,
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined the request: {resp.stop_details}")
    return resp


def _text(resp):
    return "\n".join(b.text for b in resp.content if b.type == "text").strip()


def research(client, cfg, rules, kind, today, recent):
    if kind == "market":
        task = (f"Today is {today} (India). Use web search to gather the latest verified data on Indian "
                "equity markets: the most recent completed session and the week so far - Nifty 50 / Sensex "
                "closes and % change, sector leaders and laggards, FII/DII flows, INR, crude, bond yields, and "
                "any major macro, RBI, results or global event driving them. Pick the 3 most useful "
                "observations for a long-term investor. Also gather ONE verified data set for a chart: either "
                "3-8 comparable figures for the same period (e.g. weekly % change of sector indices, FII vs DII "
                "net flows, returns of Nifty/Midcap/Smallcap) or 4-12 daily closes of an index. Write research "
                "notes: each fact with its figure, the date it refers to, and the source name and URL; list the "
                "chart data as a small table. Leave out anything you could not verify.")
    else:
        task = (f"Today is {today} (India). Choose one genuine investing quote that fits the current Indian "
                "market mood (search briefly for this week's context). Verify with web search that the "
                "attribution is genuine and the wording is exact. Do NOT use any of these recently used "
                f"quotes: {json.dumps(recent)}. Write research notes: the exact quote, the author, where it is "
                "documented (source name and URL), and one or two lines of current market context.")
    messages = [{"role": "user", "content": task}]
    for _ in range(5):       # web search turns can pause; resume up to 5 times
        resp = _call(client, cfg, system=rules, messages=messages, tools=[WEB_SEARCH],
                     output_config={"effort": cfg["effort"]})
        if resp.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": resp.content})
    notes = _text(resp)
    if not notes:
        raise RuntimeError("Research step returned no notes")
    return notes


def write_post(client, cfg, rules, kind, today, notes):
    prompt = (f"Today is {today}. Write today's '{kind}' LinkedIn post for the Fund's page using ONLY the "
              f"facts in these research notes. Every number in stats, chart and points must appear in the notes; if "
              "the notes do not hold a complete chart data set, set chart type to 'none'. Follow every hard rule.\n\n<research_notes>\n{notes}\n"
              "</research_notes>")
    resp = _call(client, cfg, system=rules, messages=[{"role": "user", "content": prompt}],
                 output_config={"effort": cfg["effort"],
                                "format": {"type": "json_schema", "schema": POST_SCHEMA}})
    post = json.loads(_text(resp))
    post["kind"] = kind
    return post


def generate(cfg, rules, kind, today, recent_quotes):
    client = anthropic.Anthropic()
    notes = research(client, cfg, rules, kind, today, recent_quotes)
    post = write_post(client, cfg, rules, kind, today, notes)
    post["research_notes"] = notes
    return post
