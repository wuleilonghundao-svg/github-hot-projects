from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from .config import load_settings
from .github_api import github_search_repos, list_stargazers_within, iso_days_ago


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CONFIG_PATH = ROOT / "gh_hot" / "config.yml"
README_PATH = ROOT / "README.md"


RANK_TEMPLATE = Template(
    """
GitHub Hot Projects

Overview
- Daily-updated ranking of hot GitHub projects by recent stars.
- Supports All + specific languages, configurable time window.
- Runs locally or via GitHub Actions to auto-update README and JSON data.

Latest Update: {{ generated_at }} UTC
Window: last {{ days }} days | Top {{ top_n }} | Languages: {{ languages|join(', ') }}

{% for lang, items in rankings.items() %}
### {{ lang }}
| # | Repo | Stars ↑ ({{ days }}d) | Total Stars | Description |
|---:|:-----|----------------------:|------------:|:------------|
{% for r in items %}| {{ loop.index }} | [{{ r.full_name }}]({{ r.html_url }}) | {{ r.recent_stars }} | {{ r.stargazers_count }} | {{ r.description or '' }} |
{% endfor %}

{% endfor %}

How It Works
- Searches repositories via GitHub REST API.
- Ranks by stars gained within the configured window (fallback: stars for newly created repos).
- Outputs a Markdown ranking and machine-readable JSON.

Config
- See `gh_hot/config.yml` for languages and window days.
- Override via env vars: `GITHUB_TOKEN`, `GH_HOT_LANGS`, `GH_HOT_DAYS`, `GH_HOT_TOP_N`, `GH_HOT_USE_GROWTH`.

Automation
- See `.github/workflows/daily.yml` for a daily schedule that runs the generator and commits updates.

""".strip()
)


def compute_rankings(settings) -> Dict[str, List[Dict]]:
    days = settings.days
    since_date = iso_days_ago(days)
    since_dt = datetime.now(timezone.utc) - timedelta(days=days)
    rankings: Dict[str, List[Dict]] = {}

    for lang in settings.languages:
        query_parts = []
        if lang and lang.lower() != "all":
            query_parts.append(f"language:{lang}")
        # Prefer active repos with stars; scope candidates to reduce expensive star scans
        query_parts.append(f"pushed:>={since_date}")
        query_parts.append("stars:>50")
        # GitHub search limits query length; join safely
        q = " ".join(query_parts)

        candidates = github_search_repos(q, settings.token, sort="stars", order="desc", per_page=settings.top_n * 2)

        ranked: List[Dict] = []
        for item in candidates:
            full_name = item.get("full_name", "")
            owner, repo = full_name.split("/") if "/" in full_name else (None, None)
            recent = 0
            if settings.use_growth and owner and repo:
                try:
                    recent = list_stargazers_within(owner, repo, settings.token, since_dt)
                except Exception:
                    recent = 0
            # Fallback: if no growth computed and repo is new, use total stars as proxy
            created_at = item.get("created_at")
            if recent == 0 and created_at:
                try:
                    created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    if created_dt >= since_dt:
                        recent = item.get("stargazers_count", 0)
                except Exception:
                    pass

            rec = {
                "full_name": full_name,
                "html_url": item.get("html_url"),
                "description": item.get("description"),
                "stargazers_count": item.get("stargazers_count", 0),
                "recent_stars": int(recent),
                "language": item.get("language"),
            }
            ranked.append(rec)

        ranked.sort(key=lambda x: (x["recent_stars"], x["stargazers_count"]), reverse=True)
        rankings[lang] = ranked[: settings.top_n]

    return rankings


def write_outputs(rankings: Dict[str, List[Dict]], days: int, top_n: int, languages: List[str]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "days": days,
        "top_n": top_n,
        "languages": languages,
        "rankings": rankings,
    }
    (DATA_DIR / "latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    md = RANK_TEMPLATE.render(
        generated_at=out["generated_at"], days=days, top_n=top_n, languages=languages, rankings=rankings
    )
    README_PATH.write_text(md, encoding="utf-8")


def main():
    settings = load_settings(str(CONFIG_PATH))
    rankings = compute_rankings(settings)
    write_outputs(rankings, settings.days, settings.top_n, settings.languages)


if __name__ == "__main__":
    main()

