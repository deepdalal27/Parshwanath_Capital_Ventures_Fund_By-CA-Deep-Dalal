"""Visual-first slides for CA Deep Dalal's personal LinkedIn posts.

People scan, they do not read: every slide carries one idea, shown big (a number, a chart, a comparison),
with at most one short line of text. Full-colour gradient backgrounds per format, bold numbers, simple
graphics. 1080x1350 (4:5). One slide = image post; 3+ slides = carousel (posted as a PDF document).

Slide types (post JSON "slides"):
  cover    {"title", "sub"?, "big"?, "big_label"?}          hook slide, optional hero number
  stat     {"value", "label", "note"?}                       one giant number
  chart    {"title", "chart": {type bar|line, labels, values, unit, source}, "note"?}
  compare  {"title", "a": {"value","label"}, "b": {"value","label"}, "note"?}
  points   {"title", "items": [max 3 short lines, <= 8 words each]}
  end      {"title", "sub"?}                                 takeaway + signature
No fund logo or fund name: personal views.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

from .render import _fit, _font, _fmt, _nice, _wrap

W, H = 1080, 1350
PAD = 84
WHITE = (255, 255, 255)
SOFT = (255, 255, 255, 190)

PALETTES = {   # top colour, bottom colour, accent
    "ipo":        ((27, 20, 100), (110, 44, 170), (255, 209, 102)),
    "markets":    ((4, 54, 74), (11, 132, 87), (255, 210, 63)),
    "founders":   ((122, 28, 59), (232, 85, 58), (255, 230, 109)),
    "playbook":   ((11, 61, 145), (0, 166, 251), (255, 210, 63)),
    "regulation": ((24, 32, 48), (185, 28, 28), (253, 230, 138)),
}


def _palette(fmt):
    return PALETTES.get(fmt, PALETTES["markets"])


def _background(fmt, seed):
    top, bottom, accent = _palette(fmt)
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line((0, y, W, y), fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    # soft decorative shapes, placed differently per slide
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    r = 420 + (seed * 37) % 160
    cx, cy = (W - 80, 120) if seed % 2 == 0 else (60, H - 330)
    ld.ellipse((cx - r, cy - r, cx + r, cy + r), fill=accent + (34,))
    r2 = 220 + (seed * 53) % 120
    cx2, cy2 = (120, 420) if seed % 2 == 0 else (W - 60, 520)
    ld.ellipse((cx2 - r2, cy2 - r2, cx2 + r2, cy2 + r2), outline=WHITE + (40,), width=6)
    for gx in range(PAD, W - PAD + 1, 48):            # faint dot grid
        for gy in range(1040, 1180, 48):
            ld.ellipse((gx - 2, gy - 2, gx + 2, gy + 2), fill=WHITE + (26,))
    layer = layer.filter(ImageFilter.GaussianBlur(1))
    img.paste(layer, (0, 0), layer)
    return img, accent


def _avatar(path, size):
    src = Image.open(path).convert("RGB")
    sw, sh = src.size
    side = int(min(sw, sh * 0.40))
    left = max(0, min(sw - side, int(sw * 0.56) - side // 2))
    top = int(sh * 0.07)
    face = src.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    return face, mask


def _chrome(img, d, post, cfg, i, n, accent, photo):
    """Top label + slide counter, bottom signature strip + progress dots."""
    d.text((PAD, 70), post["label"].upper(), font=_font("sans_bold", 26), fill=accent)
    if n > 1:
        d.text((W - PAD, 70), f"{i + 1:02d}/{n:02d}", font=_font("sans_bold", 26), fill=WHITE, anchor="ra")
    y = H - 132
    size = 76
    if photo and os.path.exists(photo):
        face, mask = _avatar(photo, size)
        d.ellipse((PAD - 4, y - 4, PAD + size + 4, y + size + 4), fill=accent)
        img.paste(face, (PAD, y), mask)
    p = cfg["presenter"]
    d.text((PAD + size + 22, y + 6), p["name"], font=_font("sans_bold", 28), fill=WHITE)
    d.text((PAD + size + 22, y + 44), p["title"], font=_font("sans", 21), fill=(230, 230, 240))
    if n > 1:
        dots_x = W - PAD - (n * 26)
        for k in range(n):
            fill = accent if k == i else (255, 255, 255)
            r = 8 if k == i else 6
            cx = dots_x + k * 26 + 10
            d.ellipse((cx - r, y + 38 - r, cx + r, y + 38 + r), fill=fill if k == i else None,
                      outline=fill, width=2)


def _text(d, text, style, width, max_lines, start, smallest, x, y, fill, gap=1.12, anchor_center=False):
    f, lines = _fit(d, text, style, width, max_lines, start, smallest)
    step = int(f.size * gap)
    for ln in lines:
        if anchor_center:
            d.text((W // 2, y), ln, font=f, fill=fill, anchor="ma")
        else:
            d.text((x, y), ln, font=f, fill=fill)
        y += step
    return y


def _pill(d, text, x, y, accent):
    f = _font("sans_bold", 24)
    w = d.textlength(text, font=f)
    d.rounded_rectangle((x, y, x + w + 40, y + 50), radius=25, fill=accent)
    d.text((x + 20, y + 25), text, font=f, fill=(20, 20, 30), anchor="lm")
    return y + 50


# ------------------------------------------------------------------ slide bodies

def _cover(d, s, accent, n):
    y = 270 if s.get("big") else 330
    if s.get("big"):
        y = _text(d, s["big"], "sans_bold", W - 2 * PAD, 1, 230, 120, PAD, y, accent, 1.0)
        if s.get("big_label"):
            y = _text(d, s["big_label"], "sans_bold", W - 2 * PAD, 1, 34, 24, PAD, y + 4, WHITE) + 30
        else:
            y += 30
    y = _text(d, s["title"], "serif_bold", W - 2 * PAD, 4, 92, 56, PAD, y, WHITE, 1.08)
    if s.get("sub"):
        y = _text(d, s["sub"], "sans", W - 2 * PAD, 2, 34, 26, PAD, y + 22, (235, 235, 245), 1.3)
    if n > 1:
        _pill(d, "Swipe  →", PAD, min(y + 50, H - 260), accent)


def _stat(d, s, accent):
    f, _ = _fit(d, s["value"], "sans_bold", W - 2 * PAD, 1, 300, 120)
    d.text((W // 2, 430), s["value"], font=f, fill=accent, anchor="mm")
    y = _text(d, s["label"], "sans_bold", W - 2 * PAD, 2, 52, 34, PAD, 640, WHITE, 1.15, anchor_center=True)
    if s.get("note"):
        _text(d, s["note"], "sans", W - 2 * PAD, 2, 30, 22, PAD, y + 26, (235, 235, 245), 1.3, anchor_center=True)


def _bars(d, chart, box, accent):
    x0, y0, x1, y1 = box
    labels, values = chart["labels"][:7], chart["values"][:7]
    n = len(values)
    unit = chart.get("unit", "")
    lo, hi = min(0, min(values)), max(0, max(values))
    span = (hi - lo) or 1
    slot = (x1 - x0) / n
    bw = min(120, slot * 0.62)
    zero = y1 - (0 - lo) / span * (y1 - y0)
    vf = _font("sans_bold", 30 if n <= 5 else 24)
    lf = _font("sans_bold", 24 if n <= 5 else 19)
    top_i = max(range(n), key=lambda k: abs(values[k]))
    for k, (lab, v) in enumerate(zip(labels, values)):
        cx = x0 + slot * k + slot / 2
        yv = zero - v / span * (y1 - y0)
        a, b = sorted((zero, yv))
        fill = accent if k == top_i else (255, 255, 255)
        d.rounded_rectangle((cx - bw / 2, a, cx + bw / 2, max(b, a + 3)), radius=12, fill=fill)
        txt = _fmt(v) + unit
        if v >= 0:
            d.text((cx, a - 14), txt, font=vf, fill=WHITE, anchor="mb")
        else:
            d.text((cx, b + 14), txt, font=vf, fill=WHITE, anchor="mt")
        for j, ln in enumerate(_wrap(d, lab, lf, slot - 8)[:2]):
            d.text((cx, y1 + 22 + j * (lf.size + 4) + (50 if lo < 0 else 0)), ln, font=lf, fill=WHITE, anchor="ma")
    d.line((x0, zero, x1, zero), fill=(255, 255, 255), width=3)


def _line(d, chart, box, accent):
    x0, y0, x1, y1 = box
    labels, values = chart["labels"][:12], chart["values"][:12]
    lo, hi = min(values), max(values)
    pad = (hi - lo) * 0.15 or abs(hi) * 0.05 or 1
    lo, hi = lo - pad, hi + pad
    n = len(values)
    pts = [(x0 + (x1 - x0) * k / max(n - 1, 1), y1 - (v - lo) / (hi - lo) * (y1 - y0)) for k, v in enumerate(values)]
    d.polygon(pts + [(pts[-1][0], y1), (pts[0][0], y1)], fill=(255, 255, 255, 40))
    d.line(pts, fill=accent, width=9, joint="curve")
    for k, (px, py) in enumerate(pts):
        if k in (0, n - 1):
            d.ellipse((px - 12, py - 12, px + 12, py + 12), fill=accent, outline=WHITE, width=4)
            d.text((px, py - 26), _fmt(values[k]) + chart.get("unit", ""), font=_font("sans_bold", 32), fill=WHITE,
                   anchor="mb")
    lf = _font("sans_bold", 22)
    step = max(1, (n - 1) // 4)
    for k in list(range(0, n, step)) + ([n - 1] if (n - 1) % step else []):
        d.text((pts[k][0], y1 + 20), labels[k][:10], font=lf, fill=WHITE, anchor="ma")


def _chart(img, s, accent):
    d = ImageDraw.Draw(img, "RGBA")
    y = _text(d, s["title"], "serif_bold", W - 2 * PAD, 2, 64, 44, PAD, 150, WHITE, 1.08)
    ch = s["chart"]
    box = (PAD + 10, max(y + 110, 400), W - PAD - 10, 960)
    (_line if ch.get("type") == "line" else _bars)(d, ch, box, accent)
    if ch.get("source"):
        d.text((PAD, 1080), f"Source: {ch['source']}"[:90], font=_font("sans", 20), fill=(225, 225, 235))
    if s.get("note"):
        _text(d, s["note"], "sans_bold", W - 2 * PAD, 1, 30, 22, PAD, 1026, accent)


def _compare(d, s, accent):
    _text(d, s["title"], "serif_bold", W - 2 * PAD, 2, 64, 44, PAD, 150, WHITE, 1.08)
    cw = (W - 2 * PAD - 40) // 2
    for k, side in enumerate((s["a"], s["b"])):
        x = PAD + k * (cw + 40)
        fill = (255, 255, 255) if k == 0 else accent
        d.rounded_rectangle((x, 420, x + cw, 900), radius=36, fill=fill)
        f, _ = _fit(d, side["value"], "sans_bold", cw - 50, 1, 150, 60)
        d.text((x + cw // 2, 600), side["value"], font=f, fill=(20, 20, 30), anchor="mm")
        lf, ll = _fit(d, side["label"], "sans_bold", cw - 60, 3, 34, 24)
        yy = 720
        for ln in ll:
            d.text((x + cw // 2, yy), ln, font=lf, fill=(40, 40, 55), anchor="ma")
            yy += int(lf.size * 1.2)
    d.ellipse((W // 2 - 44, 616, W // 2 + 44, 704), fill=(20, 20, 30))
    d.text((W // 2, 660), "vs", font=_font("sans_bold", 34), fill=WHITE, anchor="mm")
    if s.get("note"):
        _text(d, s["note"], "sans_bold", W - 2 * PAD, 2, 34, 24, PAD, 960, WHITE, 1.25, anchor_center=True)


def _points(d, s, accent):
    y = _text(d, s["title"], "serif_bold", W - 2 * PAD, 2, 70, 48, PAD, 150, WHITE, 1.08) + 70
    items = s["items"][:3]
    for k, it in enumerate(items, 1):
        d.rounded_rectangle((PAD, y, W - PAD, y + 190), radius=30, fill=(255, 255, 255))
        d.ellipse((PAD + 34, y + 51, PAD + 122, y + 139), fill=accent)
        d.text((PAD + 78, y + 95), str(k), font=_font("sans_bold", 46), fill=(20, 20, 30), anchor="mm")
        f, lines = _fit(d, it, "sans_bold", W - 2 * PAD - 200, 2, 44, 28)
        ty = y + 95 - (len(lines) * int(f.size * 1.18)) // 2
        for ln in lines:
            d.text((PAD + 160, ty), ln, font=f, fill=(20, 20, 30))
            ty += int(f.size * 1.18)
        y += 220


def _end(d, s, accent):
    d.text((PAD, 240), "THE TAKEAWAY", font=_font("sans_bold", 30), fill=accent)
    y = _text(d, s["title"], "serif_bold", W - 2 * PAD, 4, 86, 54, PAD, 300, WHITE, 1.1)
    if s.get("sub"):
        y = _text(d, s["sub"], "sans", W - 2 * PAD, 2, 34, 26, PAD, y + 26, (235, 235, 245), 1.3)
    _pill(d, "Follow for capital markets, simplified", PAD, min(y + 60, H - 260), accent)
    d.text((PAD, H - 168), "Views personal · Education only · Not investment advice", font=_font("sans", 19),
           fill=(225, 225, 235))


def render_slide(post, cfg, i, photo):
    slides = post["slides"]
    s, n = slides[i], len(slides)
    img, accent = _background(post["format"], i + len(post.get("headline", "")))
    d = ImageDraw.Draw(img, "RGBA")
    kind = s.get("type", "points")
    if kind == "chart":
        _chart(img, s, accent)
        d = ImageDraw.Draw(img, "RGBA")
    else:
        {"cover": lambda: _cover(d, s, accent, n), "stat": lambda: _stat(d, s, accent),
         "compare": lambda: _compare(d, s, accent), "points": lambda: _points(d, s, accent),
         "end": lambda: _end(d, s, accent)}.get(kind, lambda: _points(d, s, accent))()
    _chrome(img, d, post, cfg, i, n, accent, photo)
    return img


def render_post(post, cfg, out_base, photo_path=None):
    """Returns (cover_png, pdf_or_None, [slide pngs])."""
    imgs = [render_slide(post, cfg, i, photo_path) for i in range(len(post["slides"]))]
    pngs = []
    for k, im in enumerate(imgs, 1):
        p = f"{out_base}-{k:02d}.png"
        im.save(p, "PNG", optimize=True)
        pngs.append(p)
    pdf = None
    if len(imgs) >= 2:
        pdf = f"{out_base}.pdf"
        imgs[0].save(pdf, "PDF", save_all=True, append_images=imgs[1:], resolution=150)
    return pngs[0], pdf, pngs


SAMPLE = {
    "format": "ipo", "label": "IPO Decoded", "headline": "SAMPLE: Who actually gets the IPO money?",
    "slides": [
        {"type": "cover", "big": "xx%", "big_label": "SAMPLE: of this IPO is offer for sale",
         "title": "SAMPLE: Who actually gets the IPO money?", "sub": "SAMPLE: The offer structure in 60 seconds"},
        {"type": "compare", "title": "SAMPLE: Two ways money flows in an IPO",
         "a": {"value": "₹xxx cr", "label": "Fresh issue: goes to the company"},
         "b": {"value": "₹x,xxx cr", "label": "OFS: goes to selling shareholders"}},
        {"type": "chart", "title": "SAMPLE: OFS share in recent IPOs",
         "chart": {"type": "bar", "labels": ["Issue A", "Issue B", "Issue C", "Issue D"], "values": [82, 45, 100, 20],
                   "unit": "%", "source": "SAMPLE placeholder data"}, "note": "SAMPLE: Higher is not automatically worse"},
        {"type": "stat", "value": "3", "label": "SAMPLE: questions to ask about any OFS",
         "note": "SAMPLE: who sells, how much, at what entry price"},
        {"type": "points", "title": "SAMPLE: Read these in the RHP",
         "items": ["SAMPLE: Objects of the issue", "SAMPLE: Selling shareholders' cost", "SAMPLE: Promoter holding after"]},
        {"type": "end", "title": "SAMPLE: Subscription shows demand. Structure shows who gets paid.",
         "sub": "SAMPLE: Save this for the next IPO you study."},
    ],
}

if __name__ == "__main__":      # local preview: python -m autopost.render_profile [outdir]
    import json
    import sys
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = json.load(open(os.path.join(here, "config_profile.json"), encoding="utf-8"))
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
    print(render_post(SAMPLE, cfg, os.path.join(out, "sample"), os.path.join(here, cfg["presenter"]["photo"])))
