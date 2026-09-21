"""Collect issues and pull requests for every repo in repo_list.csv.

Run standalone:
    python3 data_collection/collect_issues_and_prs.py

Or through the orchestrator:
    python3 data_collection/main.py --step issues_and_prs

Collects records created in the last 6 months (SINCE). Saves pages into:
    data/raw/issues/<owner>__<repo>__page<N>.json
    data/raw/pulls/<owner>__<repo>__page<N>.json

The issues endpoint mixes PRs into the results; that is expected and is
filtered out during cleaning.
"""

import csv
import json
import time

from github_client import RAW, REPO_LIST, get

(RAW / "issues").mkdir(parents=True, exist_ok=True)
(RAW / "pulls").mkdir(parents=True, exist_ok=True)

SINCE = "2026-03-21T00:00:00Z"  # last 6 months


def fetch_pages(stem, subfolder, path, params):
    page = 1
    while True:
        items = get(f"/repos/{path}", {**params, "page": page})
        if not items:
            break
        (RAW / subfolder / f"{stem}__page{page}.json").write_text(
            json.dumps(items)
        )
        page += 1
        time.sleep(0.1)


def collect_issues_and_prs() -> int:
    """Download issues + pull requests for every repo in repo_list.csv.

    Returns the number of repos processed.
    """
    if not REPO_LIST.exists():
        raise SystemExit(
            f"{REPO_LIST} not found. Create it (owner,repo,full_name) first."
        )

    repos = list(csv.DictReader(REPO_LIST.open()))
    if not repos:
        raise SystemExit("repo_list.csv is empty.")

    for one in repos:
        full = one["full_name"]
        stem = full.replace("/", "__")

        fetch_pages(
            stem,
            "issues",
            full,
            {"state": "all", "per_page": 100, "since": SINCE},
        )

        fetch_pages(
            stem,
            "pulls",
            full,
            {"state": "all", "per_page": 100, "sort": "created", "direction": "desc"},
        )

        print("  collected:", full)

    return len(repos)


if __name__ == "__main__":
    collect_issues_and_prs()