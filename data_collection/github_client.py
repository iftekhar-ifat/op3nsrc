"""Shared GitHub API client for data collection.

Loads the token from <project_root>/.env and provides a get() helper
that raises a clear error on rate limits.

Not meant to be run directly; imported by the other scripts in this folder.
"""

import os
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

if not TOKEN:
    raise SystemExit(
        "No GITHUB_TOKEN found. Put it in <project_root>/.env as "
        "GITHUB_TOKEN=ghp_your_token_here"
    )


def get(path, params=None, headers=None):
    """Call the GitHub API and return the parsed JSON."""
    headers = {**HEADERS, **(headers or {})}
    resp = requests.get(f"{BASE}{path}", headers=headers, params=params)

    if resp.status_code in (403, 429):
        reset = resp.headers.get("X-RateLimit-Reset", "unknown")
        raise SystemExit(
            "Rate limit hit (403/429). Wait for the reset, or ask who "
            f"has quota left. (reset time: {reset})"
        )
    resp.raise_for_status()
    return resp.json()