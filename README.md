# Parshwanath Capital Ventures Fund — Website

Website for **Parshwanath Capital Ventures Fund**, a SEBI-registered Category III Alternative
Investment Fund (Reg. No. `IN/AIF3/25-26/2108`), managed by Parshwanath Fund Managers LLP.

Static HTML, CSS and vanilla JavaScript. **No build step, no dependencies, no framework.**
Open `index.html` in a browser and it works.

---

## ⚠️ Before you publish

### 1. Add the three image files (required)

The site is wired for real imagery but the files are not in the repo yet. Drop them in at
these exact paths and they appear automatically — no code change needed:

| Path | What | Notes |
|---|---|---|
| `assets/img/mark.png` | Logo emblem for the navbar | **Square, emblem only** — no ring text. Renders at 34×34, so the circular badge with "PARSHWANATH CAPITAL VENTURES FUND" around it will be illegible. Crop to just the central figure. Transparent PNG or SVG. |
| `assets/img/deep-dalal.jpg` | Portrait of CA Deep Dalal | Portrait crop, ideally 4:5. Displayed at ~800×1000. |
| `assets/img/jignesh-shah.jpg` | Portrait of Jignesh Shah | Same treatment. |

Until a file exists, the slot **degrades gracefully rather than breaking**: the navbar keeps
its built-in SVG mark and the portraits show a monogram plate. The images are transparent
until they fire `load`, so a missing file never shows a broken-image icon. Verified both ways.

Your full circular badge logo is still worth keeping for social/OG images and print — it is
just the wrong shape for a 34px navbar slot.

### 2. Replace remaining placeholders

| Placeholder | Where | Replace with |
|---|---|---|
| Jignesh Shah biography | `about.html` — marked with a visible "Biography to be added" notice | The Sponsor's real professional profile |
| `fundmanager@parshwanath.in` used as the **compliance/grievance** address | `governance.html`, `legal.html`, `contact.html` | A dedicated compliance officer mailbox, if you have one. SEBI expects a named grievance contact — right now everything routes to the Fund Manager. |
| Custodian, fund accountant/registrar, statutory auditor rows | `about.html`, `fund.html` | Named service providers. Only the trustee (Axis Trustee Services Limited) is named, because only that was supplied. |
| Management fee, performance fee, hurdle, lock-in, notice periods | `fund.html` | Actual figures from your PPM. Currently written as "as set out in the PPM". |
| Insight article links (`href="#"`) | `insights.html` | Real article pages or PDFs. Titles and summaries are drafted; the articles themselves are not written. |
| `https://parshwanath.in/` | canonical + `og:` tags, `robots.txt`, `sitemap.xml` | Confirm this is the live domain. |

Find them:

```bash
grep -rn 'href="#"\|Biography to be added\|set out in the PPM' *.html
```

### 3. Get it reviewed

Have your compliance officer and legal counsel review every page before launch. The
disclaimers in `legal.html`, the site footer, and the risk language on `fund.html` and
`philosophy.html` are a thorough starting point drafted against the AIF Regulations, 2012 —
they are not a substitute for sign-off.

---

## Facts the site is built on

Taken from the fund profile and fund manager profile PDFs supplied. If any of these are
wrong, they are wrong in several places — search before editing.

| | |
|---|---|
| Fund | Parshwanath Capital Ventures Fund |
| Category | SEBI Category III AIF |
| SEBI Reg. No. | `IN/AIF3/25-26/2108` |
| Inception | October 2025 |
| Structure | Open-ended |
| Investment Manager | Parshwanath Fund Managers LLP |
| Sponsor | Jignesh Shah |
| Fund Manager | CA Deep Dalal |
| Trustee | Axis Trustee Services Limited |
| Registered office | SF/3D-3 Nikumbh Complex, Near Mudra House, Law Garden, C.G. Road, Ellisbridge, Ahmedabad, Gujarat – 380 006 |
| Contact | fundmanager@parshwanath.in · +91 70690 06298 |

**Strategy** — primary markets (anchor participation in mainboard and SME IPOs, pre-IPO
placements, QIPs), listed equities (high-conviction, long/short permitted), special situations
(rights issues, buybacks, open offers), sector-agnostic with a preference for scalable
businesses, clean governance and credible promoters.

### Deliberate content decisions

- **No performance figures anywhere.** No returns, AUM, CAGR or track record — none was
  supplied, and inventing them would be a serious regulatory breach.
- **No invented allocation percentages.** The profile gives four strategy pillars but no
  weights, so the strategies are presented as cards rather than as a percentage breakdown.
  (An `.alloc` bar component exists in the CSS if you later want to publish real ranges.)
- **Experience is stated as given** — "3+ years", CA qualified November 2024. The copy
  deliberately does not imply decades of track record.
- **Primary-market risks are disclosed specifically**: anchor lock-ins, partial or nil
  allotment, SME liquidity, short public track records. These are material to this mandate
  and generic AIF risk language does not cover them.
- **"Open-ended" is explained, not oversold.** The FAQ states plainly that open-ended
  describes the constitution, not on-demand liquidity.

---

## Pages

| File | Purpose |
|---|---|
| `index.html` | Home — position, strategy, process, fund snapshot, issuers, leadership, insights |
| `fund.html` | Snapshot, commercial terms, onboarding, 8-question FAQ |
| `philosophy.html` | Strategy & philosophy — beliefs, four-part mandate, six-stage process, risk controls |
| `issuers.html` | For issuers & lead managers — proposition, scope, engagement path |
| `about.html` | The firm, leadership (Sponsor + Fund Manager), service providers, timeline |
| `governance.html` | Regulatory framework, independent oversight, policies, grievance redressal |
| `insights.html` | Notes and letters |
| `contact.html` | Enquiry form and direct contacts |
| `legal.html` | Disclaimer, privacy policy, terms of use |
| `404.html` | Not-found page |

`issuers.html` exists because the fund profile addresses issuers and lead managers as a
distinct audience from investors — they need different information and a different call to
action.

## Structure

```
├── index.html … 404.html      # every page is standalone, fully-formed HTML
├── assets/
│   ├── css/main.css           # the entire design system, one file
│   ├── js/main.js             # nav, scroll reveal, accordions, counters, form
│   └── img/                   # favicon + built-in SVG mark (add your logo here)
├── robots.txt
├── sitemap.xml
└── .nojekyll                  # tells GitHub Pages to serve files as-is
```

## Design system

Defined as CSS custom properties at the top of `assets/css/main.css`.

- **Ink** (`--ink-900` … `--ink-500`) — the dark institutional ground.
- **Paper** (`--paper-100` … `--paper-400`) — warm off-white, deliberately not clinical.
- **Brass** (`--brass-100` … `--brass-500`) — the single accent, picked up from your logo's
  gold. Used sparingly; restraint is what separates an asset-management site from a fintech
  landing page.
- **Type** — Fraunces (display serif), Inter (body), IBM Plex Mono (labels, data, section
  indices). Google Fonts, with system fallbacks.

Sections alternate between paper and ink as "chapters", each opened by a numbered `sec-head` —
the running index is the site's signature editorial device. The hero motif is an animated
compounding curve, masked so it sits behind the type rather than crossing it.

To rebrand, change the token values. Nothing else hard-codes a colour.

## Behaviour

`assets/js/main.js` is progressive enhancement only — **every page is fully readable with
JavaScript disabled.** It handles sticky nav state, mobile drawer, scroll progress, reveals,
accordions, counters, allocation bars, copyright year, and form validation.

`prefers-reduced-motion: reduce` is honoured throughout.

## The enquiry form

No backend. The form on `contact.html` works two ways:

1. **Default.** Composes a pre-filled email via `mailto:` so an enquiry never disappears.
2. **With a form service.** Add `data-endpoint` and submissions POST as JSON:

```html
<form data-enquiry-form data-endpoint="https://formspree.io/f/YOUR_ID" novalidate>
```

Formspree, Basin, Netlify Forms, a Lambda, or your own endpoint — anything accepting JSON.

## Deploying

Any static host. No build, no CI.

- **GitHub Pages** — Settings → Pages → deploy from this branch, root folder.
- **Netlify / Vercel / Cloudflare Pages** — connect the repo, empty build command, publish
  directory `/`.
- **Traditional hosting** — upload the contents of this directory to your web root.

## Local preview

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Verified

Checked in Chromium at 1440px and 390px across all ten pages: no horizontal overflow, no
JavaScript errors, accordions and form validation working, image fallbacks confirmed in both
the present and absent states.

## Accessibility

Semantic landmarks, skip link, visible focus rings, labelled form fields with inline errors,
`aria-expanded`/`aria-controls` on the nav toggle and accordions, `aria-current` on the active
nav item, `aria-live` form status, and decorative SVG hidden from assistive technology.
