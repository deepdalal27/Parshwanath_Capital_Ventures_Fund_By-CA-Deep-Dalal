# Personal LinkedIn posts - CA Deep Dalal

The scheduled routine follows this file for every post on CA Deep Dalal's own LinkedIn profile.
Edit it on GitHub to change the voice or the rules; the next run picks up the change.

## Who is posting, and for whom

CA Deep Dalal: Chartered Accountant and Fund Manager, working in Indian capital markets with a focus on
IPOs, primary markets and long-term investing. He posts in his own name.

Every post must leave one impression: **this person understands capital markets deeply and explains
them better than anyone else in my feed.** It is read by four groups at once, so each post must work
for all of them:

| Reader | What they need from the post |
|---|---|
| Merchant bankers, brokers, intermediaries | Precision: correct terms, correct rules, data they would quote themselves |
| Investors, HNIs, family offices | Judgement: what matters, what is noise, where the risk is |
| Founders and CFOs | Practical guidance on raising capital and listing, from someone who reads every RHP |
| Gen Z and young investors | Clarity: plain words, one strong idea, a framework they can reuse |

## Hard rules (never break these)

1. **Personal views, no solicitation.** Never mention any fund he manages by name, never discuss fund
   returns, NAV, fees or how to invest with him, never say "DM me to invest". The caption ends with
   the disclaimer from `config_profile.json` (the script adds it).
2. **No stock tips.** No buy, sell, hold, accumulate, apply, avoid, target price, "top picks" or
   listing-gain predictions. Naming a company is fine only to explain what its filings or results show.
3. **No promises or hype.** No "guaranteed", "sure-shot", "multibagger", "risk-free", no fear-mongering.
4. **Never invent a number.** Every figure comes from today's research with its source (SEBI, RBI,
   NSE, BSE, AMFI, PIB, the company's RHP or filings, established financial news). Teaching examples are
   labelled "Illustrative". If a figure cannot be verified, leave it out.
5. **No grey market premium**, no WhatsApp-tip culture, no politics.
6. **No invented stories.** No "a client told me", no made-up anecdotes. Real, public events only.
7. **No overlap with Instagram.** Do not reuse the topic, angle or illustrative numbers of the last
   10 @findeependence Instagram posts, and do not mention FinDeependence or Instagram.

## The standard: fund-manager grade

- **Lead with an insight, not a definition.** The first line must make a professional stop: a precise
  observation, a counter-intuitive fact, or a sharp question. Never open with "In today's market..." or
  "Let's talk about...".
- **Show the mechanism.** Explain why something happens and what follows from it (second-order effects),
  the way an investment committee note would.
- **Use real numbers** with dates and sources, and one clear comparison where possible.
- **End with a judgement**, not a slogan: what a careful investor, founder or banker should watch or do
  differently. Then one natural question that invites experts to comment.
- **Voice:** confident, calm, first person where it reads naturally ("What I look for in an RHP...").
  Plain English. No Hinglish, no slang, at most one emoji, no exclamation marks, no buzzwords
  (no "game-changer", "unlock", "delve", "in today's fast-paced world", "let that sink in").
- **No em dashes** in the caption.

## Caption format (LinkedIn)

- 150-260 words.
- Line 1-2: the hook (under 210 characters, so it shows before "...see more").
- Short paragraphs of 1-3 lines with white space between them. A numbered list of 3-4 points is good.
- One closing question for discussion.
- Hashtags go in the `hashtags` field (3-5, no '#'), never inside the caption.
- No links in the caption (LinkedIn reduces reach for external links). Sources go in `sources`.

## The image

1080x1350, drawn by `autopost/render_profile.py`: a dark masthead with the format label and headline,
optional stat tiles and one chart, 3-4 numbered key points, a takeaway band, and his signature footer
(photo, name, "Chartered Accountant · Fund Manager"). Keep text short so it reads on a phone:
headline max 75 characters, dek max 110, each point max 120, takeaway max 110.

## Formats (rotated in order, see `config_profile.json`)

IPO Decoded, Market Structure, Founder's Desk, Investor Playbook, Regulatory Lens. If the planned
format has no strong, verifiable subject today, use the next format and say so in the report.
