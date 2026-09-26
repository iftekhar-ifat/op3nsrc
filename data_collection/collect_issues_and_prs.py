"""Collect issues and pull requests for every repo in repo_list.csv.

Run standalone:
    python3 data_collection/collect_issues_and_prs.py

Or through the orchestrator:
    python3 data_collection/main.py --step issues_and_prs

Collects records created in the last 3 months (SINCE). Saves pages into:
    data/raw/issues/<owner>__<repo>__page<N>.json
    data/raw/pulls/<owner>__<repo>__page<N>.json

Filters applied while collecting (so the dataset stays clean):
    Issues:
      - drop records that are actually pull requests (issues endpoint mixes them in)
      - drop bot accounts ([bot] logins)
      - drop issues with empty/near-empty text (title + body must be usable)
    Pull requests:
      - keep only merged PRs
      - keep only PRs that reference an issue (body contains Fixes/Closes/#N)
    Both:
      - capped per repo so one huge repo can't dominate the dataset
"""

import csv
import json
import re
import time

from github_client import RAW, REPO_LIST, get

(RAW / "issues").mkdir(parents=True, exist_ok=True)
(RAW / "pulls").mkdir(parents=True, exist_ok=True)

SINCE = "2026-06-24T00:00:00Z"  # last 3 months
MIN_ISSUE_TEXT_CHARS = 15       # ignore issues whose title+body is basically empty
MAX_ISSUES_PER_REPO = 100       # stop paging after collecting this many issues
MAX_PULLS_PER_REPO = 50         # stop paging after collecting this many PRs

ISSUE_LINK = re.compile(r"(?:fixes|closes|resolves|refs)\s+#(\d+)", re.IGNORECASE)


def _is_bot(login):
    return bool(login) and login.endswith("[bot]")


def _is_useful_issue(rec):
    if rec.get("pull_request"):
        return False
    login = (rec.get("user") or {}).get("login", "")
    if _is_bot(login):
        return False
    text = f"{rec.get('title') or ''} {rec.get('body') or ''}".strip()
    return len(text) >= MIN_ISSUE_TEXT_CHARS


def _is_useful_pull(rec):
    if (rec.get("created_at") or "") < SINCE:
        return False
    if not rec.get("merged_at"):
        return False
    login = (rec.get("user") or {}).get("login", "")
    if _is_bot(login):
        return False
    text = f"{rec.get('body') or ''} {rec.get('title') or ''}"
    return bool(ISSUE_LINK.search(text))


def fetch_pages(stem, subfolder, endpoint, params, useful, max_records):
    page = 1
    kept = 0
    while kept < max_records:
        items = get(endpoint, {**params, "page": page})
        if not items:
            break

        useful_items = [rec for rec in items if useful(rec)]
        if useful_items:
            useful_items = useful_items[: max_records - kept]
            (RAW / subfolder / f"{stem}__page{page}.json").write_text(
                json.dumps(useful_items)
            )
            kept += len(useful_items)
            print(f"  {subfolder.strip('/')}: page {page}, +{len(useful_items)} kept, {kept} total")

        page += 1
        time.sleep(0.1)


def collect_issues_and_prs() -> int:
    """Download issues + pull requests for every repo in repo_list.csv.

    A failure on one repo is reported and skipped, so the rest still gets
    collected. Returns the number of repos processed.
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
        try:
            fetch_pages(
                stem,
                "issues",
                f"/repos/{full}/issues",
                {"state": "all", "per_page": 100, "since": SINCE},
                _is_useful_issue,
                MAX_ISSUES_PER_REPO,
            )
            fetch_pages(
                stem,
                "pulls",
                f"/repos/{full}/pulls",
                {"state": "all", "per_page": 100, "since": SINCE, "sort": "created", "direction": "desc"},
                _is_useful_pull,
                MAX_PULLS_PER_REPO,
            )
            print("  done:", full)
        except SystemExit:
            raise
        except Exception as exc:
            print(f"  !!! failed on {full}: {exc} (skipping repo)")

    return len(repos)


if __name__ == "__main__":
    collect_issues_and_prs()