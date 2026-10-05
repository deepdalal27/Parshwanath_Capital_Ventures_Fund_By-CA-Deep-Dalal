# LinkedIn daily post - Parshwanath Capital Ventures Fund

Every day at **12:00 PM IST** a scheduled Claude routine posts to the Fund's LinkedIn Company Page:

| Day | Post |
|---|---|
| Mon, Wed, Fri | **Market analysis**: Claude searches the web for the latest Indian market data (Nifty/Sensex, sectors, FII/DII flows, INR, crude, yields, RBI). The image carries 3 stat tiles, a chart (bar chart of sector/flow figures or line chart of daily closes, source named underneath) and 3 sourced observations |
| Tue, Thu, Sat, Sun | **Investing quote**: a verified quote (never repeated within 120 days), credited to its real author, on a dark card with **CA Deep Dalal's photo and the name card "CA Deep Dalal, Fund Manager"** |

Each post is a 1080x1350 image with the **Fund logo at the top** and the **address at the bottom**
(*D-3/A, 2nd Floor, Nikumbh Complex, Bh. National Handloom, CG Road, Ellisbridge, Ahmedabad*), plus a
caption that ends with the address, SEBI registration and the disclaimer.

## How it works (free mode)

There is **no paid API key**. A scheduled **Claude Code routine** on your Claude plan does the work, the
same way the IPO-analysis routine runs:

1. About **11:20 IST** every day the routine starts a Claude session on this repository and follows
   `ROUTINE.md`.
2. Claude researches with web search and writes the post as `out/post.json`, following `POSTING_RULES.md`.
3. `autopost/render.py` draws the branded image using `../Logo.jpeg` (and, for quotes, the Fund Manager's
   photo). Claude looks at the image before posting. If a market post has no complete verified data set, the
   chart is left out rather than guessed.
4. `run.py` uploads the image to LinkedIn, waits until **12:00 IST**, then publishes.
5. The post is recorded in `data/history.json` on the `linkedin-history` branch, so the routine never
   posts twice in a day and avoids repeating quotes.

The GitHub Actions workflow (`.github/workflows/linkedin-daily-post.yml`) is the paid alternative. It
calls the Claude API itself and needs an `ANTHROPIC_API_KEY` secret, so its schedule is switched off.

## One-time setup

### 1. LinkedIn app (to post as the Company Page) - free

1. Go to <https://www.linkedin.com/developers/apps> and create an app. Link it to the
   Parshwanath Capital Ventures Fund page and verify it from the page's admin account.
2. Under **Products**, request **Community Management API**. LinkedIn reviews this; it is what allows
   posting as a page (scope `w_organization_social`). Posting does not work until it is approved.
3. Get a token while signed in as a **page admin**: open
   <https://www.linkedin.com/developers/tools/oauth/token-generator>, pick your app, tick
   `w_organization_social`, click **Request access token** and approve. Copy the token it shows
   (valid for 60 days; repeat this step every ~2 months).
4. **Organization ID**: open the page's admin view. The URL is `linkedin.com/company/<NUMBER>/admin/`.
   That number is the ID.

### 2. Claude cloud environment settings

In Claude Code on the web, open the **cloud environment menu in the session's title bar → Edit**:

- **Network access**: choose **Custom**, keep the default package-manager list, and add these allowed
  domains: `api.linkedin.com`, `www.linkedin.com`. (LinkedIn is blocked by default.)
- **Environment variables**: add
  `LINKEDIN_ORG_ID=<the number from step 1.4>` and
  `LINKEDIN_ACCESS_TOKEN=<the token from step 1.3>`.

Never paste the token into a chat; put it only in the environment settings.

### 3. Merge the pull request

Merge the PR into `main` so the routine finds this folder. Until LinkedIn is set up, each run still
makes the day's image and caption and reports what is missing, so you can post by hand.

## Changing things

| To change | Edit |
|---|---|
| Tone, topics, compliance rules | `POSTING_RULES.md` |
| Which day gets which type, hashtags, address, disclaimer, model | `config.json` |
| Post time | `post_time` in `config.json` **and** the routine's schedule (start it about 40 min earlier) |
| Image design | `autopost/render.py`, then preview with `python -m autopost.render` |
| Photo or name on quote posts | Replace `assets/deep-dalal-fund-manager.jpg`, or edit `presenter` in `config.json` |
| Pause posting | Turn off the "LinkedIn daily post" routine in Claude Code's Routines list |

## Notes

- **Compliance:** the rules forbid stock tips, return promises, fund solicitation and invented figures.
  Market figures must come from the day's web search, and the sources are saved in `data/history.json`.
  Have your compliance officer review `POSTING_RULES.md` and the disclaimer in `config.json` once.
- **Timing:** the routine starts about 40 minutes early so research is done by noon. If it is ever late,
  the post goes out as soon as it is ready.
- **LinkedIn API version:** `linkedin_api_version` in `config.json` (format `YYYYMM`). LinkedIn retires
  versions after about a year. If posting starts failing with a version error, set it to a recent month.
- **Cost:** free mode uses your Claude plan's usage (one session a day); LinkedIn and GitHub are free.
