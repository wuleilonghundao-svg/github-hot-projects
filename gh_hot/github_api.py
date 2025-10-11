from __future__ import annotations

import time
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


GITHUB_API = "https://api.github.com"


class RateLimitError(Exception):
    pass


def _auth_headers(token: Optional[str]) -> Dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "gh-hot-projects"
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _stars_headers(token: Optional[str]) -> Dict[str, str]:
    h = _auth_headers(token)
    # Stargazers with timestamps require this custom media type
    h["Accept"] = "application/vnd.github.star+json"
    return h


def _check_rate_limit(resp: requests.Response):
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        raise RateLimitError("GitHub API rate limit exceeded")


@retry(reraise=True, stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=20),
       retry=retry_if_exception_type((requests.RequestException, RateLimitError)))
def gh_get(url: str, token: Optional[str], params: Optional[Dict[str, str]] = None, headers: Optional[Dict[str, str]] = None) -> requests.Response:
    h = _auth_headers(token)
    if headers:
        h.update(headers)
    resp = requests.get(url, headers=h, params=params, timeout=30)
    _check_rate_limit(resp)
    resp.raise_for_status()
    return resp


def github_search_repos(query: str, token: Optional[str], sort: str = "stars", order: str = "desc", per_page: int = 50) -> List[Dict]:
    url = f"{GITHUB_API}/search/repositories"
    params = {"q": query, "sort": sort, "order": order, "per_page": per_page}
    resp = gh_get(url, token, params=params)
    data = resp.json()
    return data.get("items", [])


def list_stargazers_within(owner: str, repo: str, token: Optional[str], since: datetime) -> int:
    # Count stargazers starred_at >= since. Iterate pages until older stars encountered.
    url = f"{GITHUB_API}/repos/{owner}/{repo}/stargazers"
    per_page = 100
    page = 1
    total = 0
    while True:
        params = {"per_page": per_page, "page": page}
        resp = gh_get(url, token, params=params, headers={"Accept": "application/vnd.github.star+json"})
        batch = resp.json()
        if not batch:
            break
        newer = 0
        older_found = False
        for item in batch:
            starred_at = item.get("starred_at")
            if not starred_at:
                continue
            try:
                ts = datetime.fromisoformat(starred_at.replace("Z", "+00:00"))
            except ValueError:
                continue
            if ts >= since:
                newer += 1
            else:
                older_found = True
        total += newer
        if older_found:
            break
        page += 1
        # Cap pages for safety
        if page > 10:
            break
    return total


def iso_days_ago(days: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.strftime("%Y-%m-%d")

