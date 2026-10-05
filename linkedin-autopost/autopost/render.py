"""Draw the branded 1080x1350 post image: fund logo on top, content, address footer at the bottom.

Colours follow the website (assets/css/main.css): ink, paper and brass.
"""
import glob
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
INK, INK_SOFT = (11, 15, 22), (24, 32, 45)
PAPER = (251, 250, 247)
BRASS, BRASS_DARK = (201, 168, 106), (125, 99, 52)
MUTED, ON_INK, ON_INK_MUTED = (93, 102, 115), (238, 241, 245), (151, 161, 176)
GREEN = (76, 154, 118)

_FONTS = {
    "serif_bold": ["DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf"],
    "serif_italic": ["DejaVuSerif-Italic.ttf", "LiberationSerif-Italic.ttf", "DejaVuSerif.ttf"],
    "sans": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"],
    "sans_bold": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
}


def _font(style, size):
    for name in _FONTS[style]:
        hits = glob.glob(f"/usr/share/fonts/**/{name}", recursive=True)
        if hits:
            return ImageFont.truetype(hits[0], size)
    return ImageFont.load_default(size)


def _wrap(draw, text, font, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _fit(draw, text, style, width, max_lines, start, smallest):
    """Largest font size (down to `smallest`) at which text fits in max_lines."""
    size = start
    while True:
        font = _font(style, size)
        lines = _wrap(draw, text, font, width)
        if len(lines) <= max_lines or size <= smallest:
            return font, lines[:max_lines] if size > smallest else lines
        size -= 2


def _block(draw, lines, font, x, y, fill, gap=1.25):
    step = int(font.size * gap)
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=fill)
        y += step
    return y


def _logo(path, size):
    img = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    img.putalpha(mask)
    return img


def render(post, cfg, logo_path, date_label, out_path):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    pad = 84
    text_w = W - 2 * pad

    # Header: logo + fund name
    logo_size = 190
    img.paste(_logo(logo_path, logo_size), (pad - 10, 56), _logo(logo_path, logo_size))
    hx = pad - 10 + logo_size + 28
    d.text((hx, 98), "PARSHWANATH", font=_font("serif_bold", 44), fill=INK)
    d.text((hx, 152), "CAPITAL VENTURES FUND", font=_font("serif_bold", 30), fill=BRASS_DARK)
    d.text((hx, 196), "SEBI Registered Category III AIF", font=_font("sans", 20), fill=MUTED)
    y = 56 + logo_size + 34
    d.line((pad, y, W - pad, y), fill=BRASS, width=3)

    # Kicker
    y += 30
    kicker = f"{post['label'].upper()}  ·  {date_label}"
    d.text((pad, y), kicker, font=_font("sans_bold", 24), fill=BRASS_DARK)
    y += 54

    footer_top = H - 190
    if post["kind"] == "quote":
        y = _quote_body(d, post, pad, y, text_w, footer_top)
    else:
        y = _market_body(d, post, pad, y, text_w, footer_top)

    # Takeaway strip, anchored above the footer
    if post.get("takeaway"):
        font, lines = _fit(d, post["takeaway"], "sans_bold", text_w - 40, 2, 28, 22)
        box_h = 40 + int(font.size * 1.3) * len(lines)
        top = footer_top - 40 - box_h
        d.rectangle((pad, top, W - pad, top + box_h), fill=(244, 241, 236))
        d.rectangle((pad, top, pad + 8, top + box_h), fill=BRASS)
        _block(d, lines, font, pad + 32, top + 20, INK, 1.3)

    # Footer: registration + address (always present)
    d.rectangle((0, footer_top, W, H), fill=INK)
    d.rectangle((0, footer_top, W, footer_top + 6), fill=BRASS)
    d.text((pad, footer_top + 32), cfg["registration_line"], font=_font("sans_bold", 22), fill=BRASS)
    addr_font, addr_lines = _fit(d, cfg["address"], "sans", text_w, 2, 24, 18)
    yy = _block(d, addr_lines, addr_font, pad, footer_top + 74, ON_INK, 1.35)
    d.text((pad, yy + 6), f"{cfg['website']}  ·  For information only. Not investment advice.",
           font=_font("sans", 18), fill=ON_INK_MUTED)

    img.save(out_path, "PNG", optimize=True)
    return out_path


def _market_body(d, post, pad, y, text_w, footer_top):
    font, lines = _fit(d, post["headline"], "serif_bold", text_w, 3, 58, 40)
    y = _block(d, lines, font, pad, y, INK, 1.18) + 30
    for point in post["points"][:3]:
        pf, plines = _fit(d, point, "sans", text_w - 56, 3, 30, 24)
        d.ellipse((pad, y + 10, pad + 18, y + 28), fill=GREEN)
        y = _block(d, plines, pf, pad + 44, y, INK_SOFT, 1.32) + 26
    return y


def _quote_body(d, post, pad, y, text_w, footer_top):
    font, lines = _fit(d, post["quote"], "serif_italic", text_w, 6, 62, 32)
    block_h = 110 + int(font.size * 1.3) * len(lines) + 26 + 40
    space = footer_top - 200 - y            # leave room for the takeaway strip
    y += max(0, (space - block_h) // 2)
    d.text((pad - 6, y - 30), "“", font=_font("serif_bold", 170), fill=BRASS)
    y += 110
    y = _block(d, lines, font, pad, y, INK, 1.3) + 26
    d.text((pad, y), f"— {post['quote_author']}", font=_font("sans_bold", 30), fill=BRASS_DARK)
    return y + 60


if __name__ == "__main__":       # local preview: python -m autopost.render
    import json
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = json.load(open(os.path.join(here, "config.json")))
    logo = os.path.join(here, "..", cfg["logo"])
    samples = {
        "market": {"kind": "market", "label": "Market Lens", "headline": "Nifty holds 25,000 as FIIs turn net buyers",
                   "points": ["SAMPLE: Nifty 50 closed at 25,1xx (+0.8%) on the week; banks led, IT lagged.",
                              "SAMPLE: FIIs net bought Rs x,xxx cr over the week after two weeks of selling.",
                              "SAMPLE: 10-year G-sec yield eased to 6.xx% ahead of the RBI policy meeting."],
                   "quote": "", "quote_author": "",
                   "takeaway": "Flows turn quickly; earnings quality and valuation discipline compound."},
        "quote": {"kind": "quote", "label": "Investing Wisdom", "headline": "", "points": [],
                  "quote": "The stock market is a device for transferring money from the impatient to the patient.",
                  "quote_author": "Warren Buffett",
                  "takeaway": "Volatility is the fee for long-term returns, not a fine."},
    }
    for k, p in samples.items():
        print(render(p, cfg, logo, "05 OCT 2026", f"/tmp/sample_{k}.png"))
