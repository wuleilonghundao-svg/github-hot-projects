GitHub Hot Projects

Overview
- Daily-updated ranking of hot GitHub projects by recent stars.
- Supports All + specific languages, configurable time window.
- Runs locally or via GitHub Actions to auto-update README and JSON data.

How It Works
- Searches repositories via GitHub REST API.
- Ranks by stars gained within the configured window (fallback: stars for newly created repos).
- Outputs a Markdown ranking and machine-readable JSON.

Quick Start
- Python 3.10+
- Create a GitHub token with public_repo access; set `GITHUB_TOKEN`.
- Install deps: `pip install -r requirements.txt`
- Run: `python -m gh_hot.generate`

Config
- See `gh_hot/config.yml` for languages and window days.
- Override via env vars:
  - `GITHUB_TOKEN`: GitHub API token
  - `GH_HOT_LANGS`: comma-separated languages (e.g., `All,Python,JavaScript,Go,TypeScript,Rust`)
  - `GH_HOT_DAYS`: integer days window (e.g., `7`)
  - `GH_HOT_TOP_N`: top N to keep (e.g., `50`)
  - `GH_HOT_USE_GROWTH`: `1` to compute recent star growth (slower, more accurate)

Automation
- See `.github/workflows/daily.yml` for a daily schedule that runs the generator and commits updates.

Outputs
- `README.md`: Top rankings per language
- `data/latest.json`: Raw ranking data to integrate elsewhere

Notes
- The GitHub search API does not provide star growth directly; this project optionally computes it by reading stargazer timestamps for candidate repos.
- Rate limits: authenticated tokens are recommended for reliability.

