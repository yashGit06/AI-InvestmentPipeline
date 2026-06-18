# Process Log

## Before Writing Code

### Why HN as the sole source

We chose Hacker News (via the Algolia Search API) as the sole sourcing channel because:
- **Zero Friction:** It does not require API authentication or OAuth.
- **Built-in Quality Proxy:** Upvotes and comment activity on "Show HN" posts act as immediate organic validation.
- **Freshness:** Launches are posted in real-time, providing fresh data out-of-the-box.
- **Comparison to Alternatives:** Product Hunt requires OAuth and has aggressive bot detection; Crunchbase is behind a restrictive paywall; Scraping YC Batch directories is fragile and breaks easily when the page structure changes.

### LLM Choice - OpenAI Primary & Gemini Fallback

- **OpenAI Primary:** We transitioned OpenAI (`gpt-4o-mini`) to be the primary model because Google's Gemini free tier API keys often encounter restrictive project quotas (e.g. `RESOURCE_EXHAUSTED` limit: 0) depending on geographic or developer profile restrictions.
- **Low-Cost Execution:** OpenAI's `gpt-4o-mini` is highly cost-efficient (approx. $0.02 for a full 15-startup run) and offers extremely high uptime.
- **Gemini Fallback:** We kept Gemini 2.0 Flash in the codebase as a robust secondary fallback model if the primary OpenAI client encounters rate limits or errors.

### Thesis Scoping Decision

- **First Draft:** "AI companies for SMBs" — way too broad.
- **Revised Thesis:** "B2B software that uses LLMs to fully automate a single, previously human-executed operational workflow for businesses with 10–200 employees, in markets where the incumbent is either spreadsheets or legacy SaaS priced above $100/seat/month."
- **Rationale:** Startups targeting concrete, highly-specific workflows (like invoicing, payroll, or customer support triage) are easier to sell to SMBs than broad "AI copilots" or complex builders that require manual configuration and high change-management friction.

## Prompt Iterations

### v1 Problem
The initial prompt in `prompts/analysis_v1.txt` had several flaws:
1. The model hallucinated founder names (e.g. inventing realistic-sounding names like "John Smith") when none were present in the source text.
2. It hallucinated massive TAM estimates without any evidence in the page content.
3. Scoring math was sometimes inconsistent (the total score did not match the sum of the category scores).
4. The output often wrapped the JSON inside markdown code blocks, which required extra regex parsing to clean up.

### v1 -> v2 Changes
In `prompts/analysis_v2.txt`, we implemented the following changes:
1. **Strict Hallucination Control:** Added explicit rules like: *"Never hallucinate. If a fact is not in the provided data, write 'Not publicly available'."*
2. **Data Confidence Rating:** Added a `data_quality` field under the team block to measure sourcing confidence:
   - `high`: found actual founder backgrounds.
   - `medium`: company name known, founders unnamed.
   - `low`: home page failed, only HN post title available.
3. **Structured Scoring Constraint:** Added a rule that the total score *must* equal the sum of the breakdown scores. Added code in `analyze.py` to auto-enforce this consistency by summing up category scores at parse time if they differ.
4. **Output Schema Reinforcement:** Provided a complete schema with explicit key types and instructed the model to return raw JSON only.

## Data Issues Found During Testing

- **GitHub Links as Homepages:** Discovered some Show HN submissions link directly to GitHub instead of a dedicated SaaS homepage.
  - *Fix:* Added detection for `github.com` in `sourcer/hn.py` and routed these to `scrape_github_repo` in `scraper/homepage.py` which retrieves the raw `README.md` from `raw.githubusercontent.com`.
- **403 Forbidden / Anti-Bot blocks:** Many startups protect their homepages with Cloudflare or other bot mitigations.
  - *Fix:* Added standard Chrome browser User-Agent headers to request headers. If anti-bot blocks still fail the homepage fetch, the pipeline catches the error, flags it in `data_gaps`, and proceeds using the HN launch post context alone rather than crashing.
- **Ambiguous Titles:** Some HN post titles lack clear company names (e.g. *"Show HN: I built an AI bookkeeping tool"*).
  - *Fix:* Built a robust parser `extract_name()` that extracts names before dashes/colons, and falls back to a clean slice of the title if no separators are found.

## Decisions I'd Revisit with More Time

- **Multi-Source Sourcing:** Integrating Crunchbase or LinkedIn API to enrich the co-founder profiling since founders' backgrounds are rarely fully listed on their homepage or HN launches.
- **Scraper Caching:** Cache scraped homepage HTML pages so if you re-run the pipeline on the same topic, you do not hit the remote homepages again. (We cached analyzed LLM JSON results, but not raw pages).
- **Comparative Dashboard:** A command line flag (`--compare`) that prints a comparative grid comparing all sourced startups across their workflows and score differences side-by-side.
