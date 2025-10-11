GitHub Trending/Hot Projects Landscape Research

Summary
- Goal: Build a daily-updated ranking of hot GitHub projects emphasizing recent star growth and activity, per language.
- Approaches in the ecosystem: scrape GitHub Trending pages, use GitHub Search API, analyze star events (stargazers), or leverage public datasets (GH Archive / BigQuery) for more comprehensive analytics.

Known Project Types (from general knowledge; verify links live when network available)
- GitHub Trending scrapers/APIs: Community tools that fetch https://github.com/trending (no official API). Pros: mirrors GitHub UI. Cons: fragile (HTML changes), no star growth metric, limited filters.
- Search-API based trenders: Query `search/repositories` with `created:` or `pushed:` windows and sort by stars/activity. Pros: stable API. Cons: does not provide star growth directly; needs heuristics.
- Star growth analyzers: Use stargazer timestamps (`Accept: application/vnd.github.star+json`) to count recent stars for candidates. Pros: accurate growth metric. Cons: API-call heavy; rate-limit sensitive.
- Event/dataset analytics: Use GH Archive or OSS Insight-like pipelines. Pros: rich analytics (PRs, issues, stars over time). Cons: infra heavy; not ideal for a simple repo-based project.

Representative Projects/Services (to validate)
- githubtrending APIs (e.g., community repos providing REST endpoints)
- vitalets/github-trending-repos (scraper-based)
- huchenme/github-trending-api (popular historical project)
- OSS Insight (PingCAP) — dashboards and trend analytics over GH events
- gharchive.org / bigquery-public-data.github_repos (datasets for deeper analysis)

Feature Comparison (typical)
- Update cadence: daily vs. hourly. Daily is sufficient and cost-effective for Actions.
- Ranking metric: star growth in N days > total stars; fallback to new repos (created within window).
- Filters: language, time window (7/14/30 days), minimum stars.
- Output: Markdown + JSON; programmatic consumption is valuable.
- Automation: GitHub Actions with GITHUB_TOKEN, commit back to repo.

Our Approach
- Candidate selection: `pushed:>=since AND stars:>50` (+ optional language). Pull top 2×N by total stars to limit the star-growth scan scope.
- Growth metric: count stargazers with `starred_at >= since` for each candidate; fallback to total stars for newly created repos within the window.
- Ranking: sort by `(recent_stars, total_stars)` descending; top N per language.
- Delivery: README section per language; JSON for integrations.

Gaps & Future Enhancements
- Star-growth sampling: consider early cutoffs once older stargazers encountered to reduce API calls.
- Broaden candidates: include `archived:false`, `is:public`, negative filters for forks.
- Additional signals: forks growth, issues/PR activity, release cadence.
- Visualization: small sparkline of stars (requires extra data persistence).
- Caching: persist last run’s repos to update incrementally.

Operational Considerations
- Rate limits: authenticated token mandatory; exponential backoff.
- Action runtime: for 6 languages × ~100 repos, should fit comfortably in schedule; adjust `top_n` and candidate multiplier as needed.
- Error handling: proceed-best-effort per repo; keep ranking deterministic.

