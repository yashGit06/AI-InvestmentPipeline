# AI-Augmented Investment Pipeline

A three-stage pipeline that automates startup triage for seed-stage VC firms. Given a topic query, the pipeline sources launches from Hacker News, scrapes their homepages (or GitHub repositories), analyzes them using LLMs against a specific investment thesis, and generates Pass / Watch / Take-a-Meeting memos.

---

## Prerequisites

Before running the pipeline, ensure your system meets the following requirements:

1. **Python:** Python 3.10 or higher installed on your system.
2. **API Keys (At least one is required):**
   - **OpenAI API Key (Recommended):** An active OpenAI API key with credits for `gpt-4o-mini` (costs less than $0.02 per run).
   - **Gemini API Key:** A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey). (Note: Free tier keys may face `RESOURCE_EXHAUSTED` rate limits if project billing/tier is set to 0 requests/min).
3. **Open Internet Connection:** For querying Hacker News APIs and scraping startup web pages.

---

## Installation & Setup

Follow these steps to set up the project locally:

### 1. Configure the Environment (`.env`)

Create a `.env` file in the root directory (you can copy `.env.example` as a template):

```bash
# Set your API keys (uncomment and fill the one you want to use)
# GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

*Note: If both keys are present, OpenAI will act as primary and Gemini as the fallback. If only `OPENAI_API_KEY` is set, the pipeline will immediately run on OpenAI.*

### 2. Install Dependencies

Install the required packages using `pip`. Note that we have pinned `httpx==0.27.2` in `requirements.txt` to prevent compatibility issues with the OpenAI client library:

```bash
python -m pip install -r requirements.txt
```

---

## How to Run the Pipeline

You can run the pipeline either via the **Desktop GUI** (recommended for interactive use) or the **CLI**.

### Option A: Desktop GUI (Recommended)

We provide a clean desktop interface to configure parameters, run tests, view real-time log outputs, and easily open results:

```bash
python gui.py
```

Inside the GUI:
- Enter your search query in **Topic Query**.
- Set **Startup Count** (limited to a maximum of 15 candidates for review safety).
- Click **Test Connection (Dry Run)** to verify sourcing connectivity and inspect candidates.
- Click **Run Full Pipeline** to process candidates, fetch homepage texts, call LLM analysis, and generate memos in real-time.
- Click **Open Outputs Folder** to open File Explorer showing your generated investment memos.
- Click **Clear Cache** to reset caches if you want to rerun from scratch.

---

### Option B: CLI (Command Line Interface)

#### 1. Run a Dry-Run (Sourcing only)

To query candidates and see search results in a table without making any LLM calls or charges:

```bash
python pipeline.py --topic "AI agents for SMBs" --dry-run
```

#### 2. Run the Full Pipeline (Analysis & Memo Generation)

To source candidates, scrape pages, run LLM analysis, and output markdown memos:

```bash
python pipeline.py --topic "AI agents for SMBs" --count 15
```

### 3. CLI Arguments Reference

- `--topic` (Required): The query or niche topic you are searching for (e.g. `"vertical AI"`, `"AI support"`, `"dev tools"`).
- `--count` (Optional, default: 15): Number of startups to process (ranges between 10 and 20).
- `--min-pts` (Optional, default: 10): Minimum Hacker News upvotes required to include a candidate (organic traction signal).
- `--output` (Optional, default: `./outputs`): The folder where markdown memos are saved.
- `--dry-run` (Optional): Run only the sourcing layer and print the matching startups.

---

## Understanding the Outputs

After running the pipeline, check the following files:

1. **`data/1_sourced.json`**: Contains the raw sourced startup profiles from Hacker News.
2. **`data/2_analyzed.json`**: Cache file holding the structured JSON analysis of each startup. This cache ensures that subsequent pipeline runs do not re-scrape or re-analyze already-processed startups, saving API costs and execution time.
3. **`outputs/`**: Contains the generated investment memos. Each memo follows a consistent format, listing:
   - Venture Score (0-100) and Recommendation (Pass / Watch / Take a Meeting)
   - Product, Team, and Market summaries
   - Technical depth, prior exits, and data confidence level
   - Risks & Open Questions
   - "What would change our mind" triggers
   - Exact source links and verification metadata
4. **`errors.log`**: Logs any errors (e.g., website connection failures or parsing issues) handled gracefully during the run.

---

## Verification & Testing

To verify the codebase is correct without calling external LLM APIs, run the automated test suite:

```bash
python -m pytest tests/ -v
```

This runs:
- Sourcing tests (`tests/test_sourcer.py`) evaluating name extraction and deduplication logic.
- Analyzer tests (`tests/test_analyzer.py`) testing structured response parsing and memo rendering with mocked LLM content.

---

## Troubleshooting

- **`Unexpected keyword argument 'proxies'` Error:**
  If you run the script and get a `TypeError` regarding `proxies` in `httpx` or `openai`, it means your Python environment has a newer version of `httpx` installed that conflicts with the OpenAI library. Correct this by running:
  ```bash
  python -m pip install httpx==0.27.2
  ```
