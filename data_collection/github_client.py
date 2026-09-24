"""Shared GitHub API client for data collection.

Loads the token from <project_root>/.env and provides a get() helper
that:
  - waits automatically when the rate limit is hit (403/429),
  - retries transient/network errors a couple of times,
  - finally raises a clear SystemExit if GitHub keeps failing.

Not meant to be run directly; imported by the other scripts in this folder.
"""

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
REPO_LIST = ROOT / "data" / "repo_list.csv"
RAW = ROOT / "data" / "raw"

load_dotenv(ROOT / ".env")

TOKEN = os.getenv("GITHUB_TOKEN")
BASE = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

MAX_RETRIES = 5

if not TOKEN:
    raise SystemExit(
        "No GITHUB_TOKEN found. Put it in <project_root>/.env as "
        "GITHUB_TOKEN=ghp_your_token_here"
    )


def _wait_for_rate_limit(resp):
    """Sleep until the rate limit resets, then let the caller retry."""
    reset = resp.headers.get("X-RateLimit-Reset")
    reset_ts = int(reset) if reset and reset.isdigit() else int(time.time()) + 3600
    wait = max(reset_ts - int(time.time()) + 5, 5)
    print(f"Rate limit reached (HTTP {resp.status_code}). Waiting {wait} seconds...")
    time.sleep(wait)


def get(path, params=None, headers=None):
    """Call the GitHub API and return the parsed JSON."""
    headers = {**HEADERS, **(headers or {})}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(f"{BASE}{path}", headers=headers, params=params, timeout=30)

            if resp.status_code in (403, 429):
                _wait_for_rate_limit(resp)
                continue

            if resp.status_code == 401:
                raise SystemExit(
                    "GitHub rejected the token (401 Unauthorized). "
                    "Check GITHUB_TOKEN in .env."
                )

            if resp.status_code >= 500:
                print(f"GitHub server error (HTTP {resp.status_code}), retry {attempt}/{MAX_RETRIES}...")
                time.sleep(10 * attempt)
                continue

            resp.raise_for_status()
            return resp.json()

        except requests.RequestException as exc:
            if attempt == MAX_RETRIES:
                raise SystemExit(f"GitHub API request failed: {exc}")
            print(f"Request error ({exc}), retry {attempt}/{MAX_RETRIES}...")
            time.sleep(10 * attempt)

    raise SystemExit("GitHub API request failed after all retries.")