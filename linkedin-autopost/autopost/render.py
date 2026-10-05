"""Draw the branded 1080x1350 post image.

Market post: logo header, headline, stat tiles, a data chart (bar or line), key observations.
Quote post:  dark card with the Fund Manager's photo, the quote, and "CA Deep Dalal, Fund Manager".
Both end with the registration + address footer.

Colours follow the website (assets/css/main.css). Gain/loss colours were checked for
colour-blind separation; bars also carry polarity by position and +/- signs.
"""
import glob
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1350
PAD = 72
FOOTER_H = 170
INK, INK_SOFT, INK_DEEP = (11, 15, 22), (24, 32, 45), (7, 9, 13)
PAPER, PAPER_2, PAPER_3 = (251, 250, 247), (244, 241, 236), (233, 228, 219)
BRASS, BRASS_DARK = (201, 168, 106), (125, 99, 52)
MUTED, FAINT = (93, 102, 115), (139, 147, 159)
ON_INK, ON_INK_MUTED = (238, 241, 245), (151, 161, 176)
GAIN, LOSS = (26, 138, 106), (196, 70, 47)
QUOTE_BG = (17, 18, 20)

_FONTS = {
    "serif_bold": ["DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf"],
    "serif_italic": ["LiberationSerif-Italic.ttf", "DejaVuSerif-Italic.ttf", "DejaVuSerif.ttf"],
    "sans": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf"],
    "sans_bold": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
}
_cache = {}


def _font(style, size):
    key = (style, size)
    if key not in _cache:
        _cache[key] = ImageFont.load_default(size)
        for name in _FONTS[style]:
            hits = glob.glob(f"/usr/share/fonts/**/{name}", recursive=True)
            if hits:
                _cache[key] = ImageFont.truetype(hits[0], size)
                break
    return _cache[key]


def _wrap(draw, text, font, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _fit(draw, text, style, width, max_lines, start, smallest):
    """Largest font size (down to `smallest`) at which text fits in max_lines."""
    for size in range(start, smallest - 1, -2):
        font = _font(style, size)
        lines = _wrap(draw, text, font, width)
        if len(lines) <= max_lines:
            return font, lines
    return font, lines


def _block(draw, lines, font, x, y, fill, gap=1.25):
    step = int(font.size * gap)
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=fill)
        y += step
    return y


def _round_logo(path, size):
    img = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    img.putalpha(mask)
    return img


def _fmt(v):
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    if abs(v) >= 100:
        return f"{v:,.1f}".rstrip("0").rstrip(".")
    return f"{v:,.2f}".rstrip("0").rstrip(".")


def _nice(raw):
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


# ---------------------------------------------------------------- shared pieces

def _header(img, d, logo_path, dark):
    size = 150
    logo = _round_logo(logo_path, size)
    img.paste(logo, (PAD - 6, 44), logo)
    x = PAD - 6 + size + 26
    d.text((x, 66), "PARSHWANATH", font=_font("serif_bold", 42), fill=ON_INK if dark else INK)
    d.text((x, 117), "CAPITAL VENTURES FUND", font=_font("serif_bold", 28), fill=BRASS if dark else BRASS_DARK)
    d.text((x, 158), "SEBI Registered Category III AIF", font=_font("sans", 19),
           fill=ON_INK_MUTED if dark else MUTED)
    y = 44 + size + 22
    d.line((PAD, y, W - PAD, y), fill=BRASS, width=3)
    return y


def _footer(d, cfg):
    top = H - FOOTER_H
    d.rectangle((0, top, W, H), fill=INK_DEEP if cfg.get("_dark") else INK)
    d.rectangle((0, top, W, top + 6), fill=BRASS)
    d.text((PAD, top + 26), cfg["registration_line"], font=_font("sans_bold", 21), fill=BRASS)
    font, lines = _fit(d, cfg["address"], "sans", W - 2 * PAD, 2, 23, 18)
    y = _block(d, lines, font, PAD, top + 64, ON_INK, 1.35)
    d.text((PAD, y + 4), f"{cfg['website']}  ·  For information only. Not investment advice.",
           font=_font("sans", 17), fill=ON_INK_MUTED)
    return top


# ---------------------------------------------------------------- market post

def _stat_tiles(d, stats, y):
    stats = stats[:3]
    gap = 18
    tw = (W - 2 * PAD - gap * (len(stats) - 1)) // len(stats)
    th = 128
    for i, s in enumerate(stats):
        x = PAD + i * (tw + gap)
        d.rounded_rectangle((x, y, x + tw, y + th), radius=10, fill=PAPER_2)
        d.text((x + 20, y + 16), s["label"].upper()[:24], font=_font("sans_bold", 17), fill=MUTED)
        vf, _ = _fit(d, s["value"], "serif_bold", tw - 40, 1, 38, 24)
        d.text((x + 20, y + 42), s["value"], font=vf, fill=INK)
        ch = s.get("change", "").strip()
        if ch:
            up = not ch.startswith(("-", "−", "–"))
            glyph = "▲" if up else "▼"
            d.text((x + 20, y + 92), f"{glyph} {ch}", font=_font("sans_bold", 20), fill=GAIN if up else LOSS)
    return y + th


def _bar_chart(d, chart, box):
    x0, y0, x1, y1 = box
    labels, values = chart["labels"][:8], chart["values"][:8]
    n = len(values)
    unit = chart.get("unit", "")
    label_w = 230
    lo, hi = min(0, min(values)), max(0, max(values))
    span = (hi - lo) or 1
    value_room = 120
    px0, px1 = x0 + label_w, x1 - value_room // 2
    has_neg = lo < 0
    if has_neg:                                    # leave room for labels on both sides
        px0 += value_room // 2
    scale = (px1 - px0) / span
    zero_x = px0 + (0 - lo) * scale
    row = (y1 - y0) / n
    bar_h = min(34, row - 10)
    lf = _font("sans", 21)
    vf = _font("sans_bold", 19)
    for i, (lab, v) in enumerate(zip(labels, values)):
        cy = y0 + row * i + row / 2
        lab_lines = _wrap(d, lab, lf, label_w - 16)[:1]
        d.text((x0, cy), lab_lines[0], font=lf, fill=INK_SOFT, anchor="lm")
        end_x = zero_x + v * scale
        a, b = sorted((zero_x, end_x))
        if b - a < 2:
            b = a + 2
        color = GAIN if v >= 0 else LOSS
        d.rounded_rectangle((a, cy - bar_h / 2, b, cy + bar_h / 2), radius=4, fill=color)
        if v >= 0:   # square off the end that touches the baseline
            d.rectangle((a, cy - bar_h / 2, min(a + 4, b), cy + bar_h / 2), fill=color)
        else:
            d.rectangle((max(b - 4, a), cy - bar_h / 2, b, cy + bar_h / 2), fill=color)
        txt = ("+" if v > 0 else "") + _fmt(v) + unit
        if v >= 0:
            d.text((b + 10, cy), txt, font=vf, fill=INK, anchor="lm")
        else:
            d.text((a - 10, cy), txt, font=vf, fill=INK, anchor="rm")
    d.line((zero_x, y0 - 4, zero_x, y1 + 4), fill=FAINT, width=2)


def _line_chart(d, chart, box):
    x0, y0, x1, y1 = box
    labels, values = chart["labels"], chart["values"]
    unit = chart.get("unit", "")
    lo, hi = min(values), max(values)
    step = _nice((hi - lo) / 2 or abs(hi) * 0.01 or 1)
    lo, hi = math.floor(lo / step) * step, math.ceil(hi / step) * step
    if hi - lo < 2 * step:
        hi = lo + 2 * step
    axis_w = 96
    px0, px1, py0, py1 = x0 + axis_w, x1 - 70, y0 + 10, y1 - 34
    gf = _font("sans", 17)
    for k in range(int(round((hi - lo) / step)) + 1):     # recessive grid at round values
        gv = lo + step * k
        gy = py1 - (gv - lo) / (hi - lo) * (py1 - py0)
        d.line((px0, gy, px1, gy), fill=PAPER_3, width=1)
        d.text((px0 - 12, gy), _fmt(gv), font=gf, fill=FAINT, anchor="rm")
    n = len(values)
    pts = [(px0 + (px1 - px0) * i / max(n - 1, 1), py1 - (v - lo) / (hi - lo) * (py1 - py0))
           for i, v in enumerate(values)]
    up = values[-1] >= values[0]
    color = GAIN if up else LOSS
    area = pts + [(pts[-1][0], py1), (pts[0][0], py1)]
    tint = tuple(int(c + (p - c) * 0.88) for c, p in zip(color, PAPER))
    d.polygon(area, fill=tint)
    d.line(pts, fill=color, width=4, joint="curve")
    ex, ey = pts[-1]
    d.ellipse((ex - 7, ey - 7, ex + 7, ey + 7), fill=color, outline=PAPER, width=2)
    d.text((ex + 12, ey), _fmt(values[-1]) + unit, font=_font("sans_bold", 19), fill=INK, anchor="lm")
    step = max(1, (n - 1) // 4)
    for i in list(range(0, n, step)) + ([n - 1] if (n - 1) % step else []):
        d.text((pts[i][0], py1 + 12), labels[i][:10], font=gf, fill=MUTED, anchor="mt")


def _chart_panel(d, chart, top, bottom):
    d.rounded_rectangle((PAD, top, W - PAD, bottom), radius=12, fill=(255, 255, 255), outline=PAPER_3, width=2)
    ix0, ix1 = PAD + 28, W - PAD - 28
    tf, tl = _fit(d, chart["title"], "sans_bold", ix1 - ix0, 1, 24, 18)
    d.text((ix0, top + 22), tl[0], font=tf, fill=INK)
    src = f"Source: {chart.get('source', '')}".strip()
    sf, sl = _fit(d, src, "sans", ix1 - ix0, 1, 16, 13)
    d.text((ix0, bottom - 34), sl[0], font=sf, fill=FAINT)
    box = (ix0, top + 70, ix1, bottom - 52)
    (_line_chart if chart["type"] == "line" else _bar_chart)(d, chart, box)


def _valid_chart(chart):
    if not chart or chart.get("type") not in ("bar", "line"):
        return False
    lab, val = chart.get("labels") or [], chart.get("values") or []
    return len(lab) == len(val) and len(val) >= (4 if chart["type"] == "line" else 3)


def _market(img, d, post, cfg, y, footer_top):
    text_w = W - 2 * PAD
    kicker = f"{post['label'].upper()}  ·  {post['_date']}"
    d.text((PAD, y + 20), kicker, font=_font("sans_bold", 22), fill=BRASS_DARK)
    font, lines = _fit(d, post["headline"], "serif_bold", text_w, 2, 50, 36)
    y = _block(d, lines, font, PAD, y + 60, INK, 1.16) + 14

    if post.get("stats"):
        y = _stat_tiles(d, post["stats"], y) + 22
    chart_ok = _valid_chart(post.get("chart"))
    if chart_ok:
        bottom = y + 360
        _chart_panel(d, post["chart"], y, bottom)
        y = bottom + 24

    # Observations fill what is left above the footer
    points = post["points"][:3]
    room = footer_top - 18 - y
    for size in range(26, 18, -1):
        f = _font("sans", size)
        wrapped = [_wrap(d, p, f, text_w - 40) for p in points]
        need = sum(len(w) * int(size * 1.3) + 14 for w in wrapped)
        if need <= room:
            break
    for w in wrapped:
        d.rounded_rectangle((PAD, y + 8, PAD + 14, y + 22), radius=3, fill=BRASS)
        y = _block(d, w, f, PAD + 36, y, INK_SOFT, 1.3) + 14
    if not chart_ok and post.get("takeaway") and footer_top - y > 150:
        tf, tl = _fit(d, post["takeaway"], "sans_bold", text_w - 60, 2, 28, 22)
        h = 40 + int(tf.size * 1.3) * len(tl)
        top = footer_top - 30 - h
        d.rectangle((PAD, top, W - PAD, top + h), fill=PAPER_2)
        d.rectangle((PAD, top, PAD + 8, top + h), fill=BRASS)
        _block(d, tl, tf, PAD + 32, top + 20, INK, 1.3)


# ---------------------------------------------------------------- quote post

def _portrait(path, w, h):
    """Crop the Fund Manager photo to w x h and feather its left and top edges into the card."""
    src = Image.open(path).convert("RGB")
    sw, sh = src.size
    ratio = w / h
    ch = int(sh * 0.90)                       # keep head to waist
    cw = int(ch * ratio)
    if cw > sw:
        cw, ch = sw, int(sw / ratio)
    cx = int(sw * 0.56)                       # subject sits slightly right of centre
    left = max(0, min(sw - cw, cx - cw // 2))
    top = int(sh * 0.12)
    top = min(top, sh - ch)
    photo = src.crop((left, top, left + cw, top + ch)).resize((w, h), Image.LANCZOS)
    mask = Image.new("L", (w, h), 255)
    md = ImageDraw.Draw(mask)
    fx, fy = int(w * 0.30), int(h * 0.10)
    for i in range(fx):
        md.line((i, 0, i, h), fill=int(255 * (i / fx) ** 1.6))
    top_mask = Image.new("L", (w, h), 255)
    td = ImageDraw.Draw(top_mask)
    for j in range(fy):
        td.line((0, j, w, j), fill=int(255 * j / fy))
    mask = ImageChops.multiply(mask, top_mask).filter(ImageFilter.GaussianBlur(2))
    return photo, mask


def _quote(img, d, post, cfg, y, footer_top):
    photo_w, photo_top = 560, y + 70
    photo_h = footer_top - photo_top
    photo, mask = _portrait(cfg["_photo"], photo_w, photo_h)
    img.paste(photo, (W - photo_w, photo_top), mask)

    kicker = f"{post['label'].upper()}  ·  {post['_date']}"
    d.text((PAD, y + 20), kicker, font=_font("sans_bold", 22), fill=BRASS)

    col_w = W - photo_w - PAD + 40              # text may run slightly into the feathered edge
    d.text((PAD - 6, y + 46), "“", font=_font("serif_bold", 150), fill=BRASS)
    qy = y + 170
    name_top = footer_top - 210
    room = name_top - 90 - qy
    for size in range(54, 28, -2):
        f = _font("serif_italic", size)
        lines = _wrap(d, post["quote"], f, col_w)
        if len(lines) * int(size * 1.28) <= room:
            break
    qy = _block(d, lines, f, PAD, qy, ON_INK, 1.28) + 18
    af, al = _fit(d, f"— {post['quote_author']}", "sans_bold", col_w, 2, 28, 20)
    _block(d, al, af, PAD, qy, BRASS, 1.25)

    # Name card: who is sharing the thought
    nm = cfg["presenter"]
    d.rectangle((PAD, name_top, PAD + 6, name_top + 150), fill=BRASS)
    d.text((PAD + 28, name_top + 4), "SHARED BY", font=_font("sans_bold", 16), fill=ON_INK_MUTED)
    d.text((PAD + 28, name_top + 30), nm["name"], font=_font("serif_bold", 42), fill=ON_INK)
    d.text((PAD + 28, name_top + 86), nm["title"], font=_font("sans_bold", 26), fill=BRASS)
    d.text((PAD + 28, name_top + 122), cfg["fund_name"], font=_font("sans", 18), fill=ON_INK_MUTED)


# ---------------------------------------------------------------- entry point

def render(post, cfg, logo_path, date_label, out_path, photo_path=None):
    dark = post["kind"] == "quote"
    cfg = {**cfg, "_dark": dark, "_photo": photo_path}
    post = {**post, "_date": date_label}
    img = Image.new("RGB", (W, H), QUOTE_BG if dark else PAPER)
    d = ImageDraw.Draw(img)
    y = _header(img, d, logo_path, dark)
    footer_top = H - FOOTER_H
    if dark:
        _quote(img, d, post, cfg, y, footer_top)
        d = ImageDraw.Draw(img)
    else:
        _market(img, d, post, cfg, y, footer_top)
    _footer(d, cfg)
    img.save(out_path, "PNG", optimize=True)
    return out_path


SAMPLES = {
    "market_bar": {
        "kind": "market", "label": "Market Lens", "headline": "SAMPLE: Banks lead as Nifty ends the week higher",
        "stats": [{"label": "Nifty 50", "value": "25,1xx", "change": "+0.8% w/w"},
                  {"label": "FII net flow", "value": "₹x,xxx cr", "change": "+ net buy"},
                  {"label": "10Y G-sec", "value": "6.xx%", "change": "-4 bps"}],
        "chart": {"type": "bar", "title": "SAMPLE: Sector indices, weekly change (%)", "unit": "%",
                  "labels": ["Nifty Bank", "Nifty Auto", "Nifty FMCG", "Nifty Pharma", "Nifty Metal", "Nifty IT"],
                  "values": [2.4, 1.6, 0.7, -0.4, -1.1, -2.3], "source": "NSE (placeholder data)"},
        "points": ["SAMPLE: Private banks led the move on improving credit growth and steady margins.",
                   "SAMPLE: IT lagged after cautious US commentary on discretionary tech spending.",
                   "SAMPLE: FIIs turned net buyers after two weeks of selling; DIIs stayed steady buyers."],
        "quote": "", "quote_author": "", "takeaway": "Flows turn quickly; earnings quality compounds."},
    "market_line": {
        "kind": "market", "label": "Market Lens", "headline": "SAMPLE: Nifty recovers through the week",
        "stats": [{"label": "Nifty 50", "value": "25,1xx", "change": "+0.8% w/w"},
                  {"label": "India VIX", "value": "12.x", "change": "-6%"}],
        "chart": {"type": "line", "title": "SAMPLE: Nifty 50 daily close", "unit": "",
                  "labels": ["29 Sep", "30 Sep", "1 Oct", "3 Oct", "4 Oct"],
                  "values": [24880, 24760, 24950, 25040, 25110], "source": "NSE (placeholder data)"},
        "points": ["SAMPLE: Index recovered from Tuesday's dip as banks and autos gained.",
                   "SAMPLE: Breadth improved; advances outnumbered declines on four of five days."],
        "quote": "", "quote_author": "", "takeaway": ""},
    "quote": {
        "kind": "quote", "label": "Investing Wisdom", "headline": "", "points": [], "stats": [], "chart": None,
        "quote": "The stock market is a device for transferring money from the impatient to the patient.",
        "quote_author": "Warren Buffett", "takeaway": ""},
}


if __name__ == "__main__":       # local preview: python -m autopost.render [outdir]
    import json
    import sys
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = json.load(open(os.path.join(here, "config.json")))
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
    for k, p in SAMPLES.items():
        print(render(p, cfg, os.path.join(here, "..", cfg["logo"]), "05 OCT 2026",
                     os.path.join(out, f"sample_{k}.png"), os.path.join(here, cfg["presenter"]["photo"])))
