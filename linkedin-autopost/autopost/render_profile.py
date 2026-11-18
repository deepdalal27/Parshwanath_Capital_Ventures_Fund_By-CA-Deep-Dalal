"""Draw the 1080x1350 image for CA Deep Dalal's personal LinkedIn posts.

Layout: dark masthead (format kicker, date, headline), light body (optional stat tiles and a data chart,
numbered key points, takeaway band), dark signature footer with his photo, name and credentials.
No fund logo or fund name: these are personal views, not Fund communication.
Reuses the drawing helpers of render.py so charts look the same as on the Fund page.
"""
import os

from PIL import Image, ImageDraw

from .render import (BRASS, BRASS_DARK, INK, INK_DEEP, INK_SOFT, MUTED, ON_INK, ON_INK_MUTED, PAD, PAPER,
                     PAPER_2, W, H, _block, _chart_panel, _fit, _font, _stat_tiles, _valid_chart, _wrap)

FOOT_H = 200


def _avatar(path, size):
    src = Image.open(path).convert("RGB")
    sw, sh = src.size
    side = int(min(sw, sh * 0.40))                 # head and shoulders
    left = max(0, min(sw - side, int(sw * 0.56) - side // 2))
    top = int(sh * 0.07)
    face = src.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    return face, mask


def _masthead(d, post, date_label):
    d.rectangle((0, 0, W, 10), fill=BRASS)
    kicker = f"{post['label'].upper()}  ·  {date_label}"
    d.text((PAD, 58), kicker, font=_font("sans_bold", 24), fill=BRASS)
    font, lines = _fit(d, post["headline"], "serif_bold", W - 2 * PAD, 3, 66, 44)
    y = _block(d, lines, font, PAD, 104, ON_INK, 1.12)
    if post.get("dek"):
        df, dl = _fit(d, post["dek"], "sans", W - 2 * PAD, 2, 28, 22)
        y = _block(d, dl, df, PAD, y + 10, ON_INK_MUTED, 1.3)
    return y + 40


def _signature(img, d, cfg, photo_path):
    top = H - FOOT_H
    d.rectangle((0, top, W, H), fill=INK_DEEP)
    d.rectangle((0, top, W, top + 5), fill=BRASS)
    size = 128
    if photo_path and os.path.exists(photo_path):
        face, mask = _avatar(photo_path, size)
        cx, cy = PAD, top + (FOOT_H - size) // 2 + 2
        d.ellipse((cx - 5, cy - 5, cx + size + 5, cy + size + 5), fill=BRASS)
        img.paste(face, (cx, cy), mask)
        x = cx + size + 30
    else:
        x = PAD
    p = cfg["presenter"]
    d.text((x, top + 42), p["name"], font=_font("serif_bold", 44), fill=ON_INK)
    d.text((x, top + 98), p["title"], font=_font("sans_bold", 23), fill=BRASS)
    d.text((x, top + 134), p["focus"], font=_font("sans", 20), fill=ON_INK_MUTED)
    note = "Views personal · Education only · Not investment advice"
    d.text((W - PAD, H - 26), note, font=_font("sans", 15), fill=ON_INK_MUTED, anchor="rs")
    return top


def _body(d, post, y, bottom):
    text_w = W - 2 * PAD
    if post.get("stats"):
        y = _stat_tiles(d, post["stats"], y) + 24
    chart_ok = _valid_chart(post.get("chart"))
    if chart_ok:
        ch_bottom = y + (280 if post.get("stats") else 340)
        _chart_panel(d, post["chart"], y, ch_bottom)
        y = ch_bottom + 26

    take_h = 0
    if post.get("takeaway"):
        tf, tl = _fit(d, post["takeaway"], "sans_bold", text_w - 64, 2, 28, 21)
        take_h = 44 + int(tf.size * 1.3) * len(tl)
    room = bottom - 30 - take_h - 24 - y

    points = post["points"][:4]
    big = not post.get("stats") and not chart_ok
    while True:                                    # largest size that fits; drop the last point if none does
        for size in range(38 if big else 27, 18, -1):
            f = _font("sans", size)
            wrapped = [_wrap(d, p, f, text_w - 64) for p in points]
            need = sum(len(w) * int(size * 1.3) + 22 for w in wrapped)
            if need <= room:
                break
        if need <= room or len(points) <= 1:
            break
        points = points[:-1]
    gap = max(22, (room - need) // max(len(points), 1) // 2 + 22) if big else 22
    nf = _font("sans_bold", 20)
    for i, w in enumerate(wrapped, 1):
        d.ellipse((PAD, y + 2, PAD + 38, y + 40), fill=INK)
        d.text((PAD + 19, y + 21), str(i), font=nf, fill=BRASS, anchor="mm")
        y = _block(d, w, f, PAD + 60, y, INK_SOFT, 1.3) + gap

    if take_h:
        top = bottom - 30 - take_h
        d.rectangle((PAD, top, W - PAD, top + take_h), fill=PAPER_2)
        d.rectangle((PAD, top, PAD + 8, top + take_h), fill=BRASS_DARK)
        _block(d, tl, tf, PAD + 36, top + 22, INK, 1.3)


def render_profile(post, cfg, date_label, out_path, photo_path=None):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, H), fill=INK)            # masthead background; the body is painted over it below
    y = _masthead(d, post, date_label)
    d.rectangle((0, y, W, H), fill=PAPER)
    d.line((0, y, W, y), fill=BRASS, width=3)
    footer_top = _signature(img, d, cfg, photo_path)
    d = ImageDraw.Draw(img)
    _body(d, post, y + 36, footer_top)
    img.save(out_path, "PNG", optimize=True)
    return out_path


SAMPLES = {
    "ipo": {
        "kind": "profile", "label": "IPO Decoded", "headline": "SAMPLE: Read the OFS share before you read the subscription number",
        "dek": "SAMPLE: What the offer structure tells founders, bankers and investors.",
        "stats": [{"label": "Fresh issue", "value": "₹xxx cr", "change": ""},
                  {"label": "Offer for sale", "value": "₹x,xxx cr", "change": ""},
                  {"label": "OFS share", "value": "xx%", "change": ""}],
        "chart": {"type": "none", "title": "", "unit": "", "labels": [], "values": [], "source": ""},
        "points": ["SAMPLE: An OFS pays selling shareholders; only the fresh issue reaches the company.",
                   "SAMPLE: A high OFS share is not a red flag by itself; who sells and why matters.",
                   "SAMPLE: The objects of the issue show whether new money builds capacity or repays debt."],
        "takeaway": "SAMPLE: Subscription shows demand. Offer structure shows who gets the money.",
    },
    "framework": {
        "kind": "profile", "label": "Investor Playbook", "headline": "SAMPLE: Three questions before any investment, at any age",
        "dek": "", "stats": [], "chart": {"type": "none", "title": "", "unit": "", "labels": [], "values": [], "source": ""},
        "points": ["SAMPLE: What has to go right for this to work, and how would I know if it did not?",
                   "SAMPLE: What price am I paying for that outcome compared with the alternatives?",
                   "SAMPLE: How much can I lose without changing my life, and is my position sized for that?"],
        "takeaway": "SAMPLE: Process first. Returns follow process more often than the other way round.",
    },
}

if __name__ == "__main__":      # local preview: python -m autopost.render_profile [outdir]
    import json
    import sys
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = json.load(open(os.path.join(here, "config_profile.json"), encoding="utf-8"))
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
    for k, p in SAMPLES.items():
        print(render_profile(p, cfg, "19 NOV 2026", os.path.join(out, f"profile_{k}.png"),
                             os.path.join(here, cfg["presenter"]["photo"])))
