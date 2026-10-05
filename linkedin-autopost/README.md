# LinkedIn daily post - Parshwanath Capital Ventures Fund

Every day at **12:00 PM IST** a GitHub Actions job posts to the Fund's LinkedIn Company Page:

| Day | Post |
|---|---|
| Mon, Wed, Fri | **Market analysis**: Claude searches the web for the latest Indian market data (Nifty/Sensex, sectors, FII/DII flows, INR, crude, yields, RBI) and writes 3 sourced observations plus a long-term takeaway |
| Tue, Thu, Sat, Sun | **Investing quote**: a verified quote (never repeated within 120 days) with a short explanation for Indian investors |

Each post is a 1080x1350 image with the **Fund logo at the top** and the **address at the bottom**
(*D-3/A, 2nd Floor, Nikumbh Complex, Bh. National Handloom, CG Road, Ellisbridge, Ahmedabad*), plus a
caption that ends with the address, SEBI registration and the disclaimer.

## How it works

1. `06:05 UTC` (11:35 IST): the workflow `.github/workflows/linkedin-daily-post.yml` starts.
2. Claude does the research with web search, then writes the post following `POSTING_RULES.md`.
3. `autopost/render.py` draws the branded image using `../Logo.jpeg`.
4. The image is uploaded to LinkedIn. The job waits until 12:00 IST, then publishes.
5. The post is added to `data/history.json`, so the job never posts twice in a day and avoids repeating quotes.
   The image and text are saved as a workflow artifact for your records.

## One-time setup

### 1. LinkedIn app (to post as the Company Page)

1. Go to <https://www.linkedin.com/developers/apps> and create an app. Link it to the
   Parshwanath Capital Ventures Fund page and verify it from the page's admin account.
2. Under **Products**, request **Community Management API**. LinkedIn reviews this; it is what allows
   posting as a page (scope `w_organization_social`). Posting does not work until it is approved.
3. Under **Auth**, add a redirect URL (for example `https://parshwanath.in/`), and note the
   **Client ID** and **Client Secret**.
4. Get a token while signed in as a **page admin**. Open this in a browser (put in your Client ID):

   ```
   https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=CLIENT_ID&redirect_uri=https%3A%2F%2Fparshwanath.in%2F&scope=w_organization_social%20r_organization_social
   ```

   Approve. You are redirected to `https://parshwanath.in/?code=...`. Copy the `code` value and exchange it
   within a few minutes:

   ```bash
   curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
     -d grant_type=authorization_code -d code=CODE \
     -d redirect_uri=https://parshwanath.in/ \
     -d client_id=CLIENT_ID -d client_secret=CLIENT_SECRET
   ```

   The reply contains `access_token` (valid for 60 days) and, once your app has refresh tokens enabled,
   `refresh_token` (valid for 1 year).
5. **Organization ID**: open the page's admin view. The URL is `linkedin.com/company/<NUMBER>/admin/`.
   That number is the ID.

### 2. GitHub secrets

In the repository, open **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key from <https://console.anthropic.com> |
| `LINKEDIN_ORG_ID` | The page's numeric ID |
| `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_REFRESH_TOKEN` | Recommended. A fresh access token is fetched on every run, so it keeps working for a year |
| `LINKEDIN_ACCESS_TOKEN` | Alternative to the three above. Expires after 60 days, so replace it before then |

### 3. Test it

**Actions → LinkedIn daily post → Run workflow**, keeping *Preview only* ticked. When it finishes, download
the artifact to see the image and caption. Nothing is posted. To post now, untick *Preview only*.

After that, it runs every day by itself.

## Changing things

| To change | Edit |
|---|---|
| Tone, topics, compliance rules | `POSTING_RULES.md` |
| Which day gets which type, hashtags, address, disclaimer, model | `config.json` |
| Post time | `post_time` in `config.json` **and** the cron line in the workflow (start it about 25 min earlier, in UTC) |
| Image design | `autopost/render.py`, then preview with `python -m autopost.render` |
| Pause posting | Actions → LinkedIn daily post → ⋯ → Disable workflow |

## Notes

- **Compliance:** the rules forbid stock tips, return promises, fund solicitation and invented figures.
  Market figures must come from the day's web search, and the sources are saved in `data/history.json`.
  Have your compliance officer review `POSTING_RULES.md` and the disclaimer in `config.json` once.
- **Timing:** GitHub sometimes starts scheduled jobs late. The job starts 25 minutes early to absorb this.
  If GitHub starts it after 12:00, the post goes out as soon as it is ready.
- **LinkedIn API version:** `linkedin_api_version` in `config.json` (format `YYYYMM`). LinkedIn retires
  versions after about a year. If posting starts failing with a version error, set it to a recent month.
- **Cost:** about two Claude API calls a day, plus a few web searches.
