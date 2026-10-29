"""Shared GitHub API client for data collection.

Loads the token from <project_root>/.env and provides get() (JSON) and
get_text() (raw text, None on 404) helpers that:
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
    "Accept": "application/vnd.github+json",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

MAX_RETRIES = 5

def _is_rate_limited(resp):
    """True for primary (quota used up) or secondary (too fast) rate limits.

    A plain 403 (e.g. access denied) is NOT a rate limit and must not make
    us sleep for an hour.
    """
    if resp.status_code == 429:
        return True
    if resp.status_code != 403:
        return False
    return (
        resp.headers.get("X-RateLimit-Remaining") == "0"
        or "Retry-After" in resp.headers
        or "rate limit" in resp.text.lower()
    )


def _wait_for_rate_limit(resp):
    """Sleep until the rate limit resets, then let the caller retry."""
    retry_after = resp.headers.get("Retry-After")
    if retry_after and retry_after.isdigit():
        wait = int(retry_after) + 1          # secondary rate limit
    else:
        reset = resp.headers.get("X-RateLimit-Reset")
        reset_ts = int(reset) if reset and reset.isdigit() else int(time.time()) + 60
        wait = max(reset_ts - int(time.time()) + 5, 5)
    print(f"Rate limit reached (HTTP {resp.status_code}). Waiting {wait} seconds...")
    time.sleep(wait)


def get(path, params=None, headers=None):
    """Call the GitHub API and return the parsed JSON."""
    return _request(path, params, headers).json()


def get_text(path, params=None, headers=None):
    """Call the GitHub API and return the body as text (e.g. raw README).

    Returns None if the resource does not exist (404).
    """
    resp = _request(path, params, headers, allow_404=True)
    return None if resp is None else resp.text


def _request(path, params=None, headers=None, allow_404=False):
    """Call the GitHub API with retries and return the response object."""
    headers = {**HEADERS, **(headers or {})}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(f"{BASE}{path}", headers=headers, params=params, timeout=30)

            if _is_rate_limited(resp):
                _wait_for_rate_limit(resp)
                continue

            if resp.status_code == 404 and allow_404:
                return None

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
            return resp

        except requests.HTTPError:
            # 4xx (404 Not Found, 410 Gone, ...) won't fix itself on retry.
            # Raise a normal error so the caller can skip just this repo.
            raise
        except requests.RequestException as exc:
            if attempt == MAX_RETRIES:
                raise SystemExit(f"GitHub API request failed: {exc}")
            print(f"Request error ({exc}), retry {attempt}/{MAX_RETRIES}...")
            time.sleep(10 * attempt)

    raise SystemExit("GitHub API request failed after all retries.")
