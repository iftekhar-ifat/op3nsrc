"""Collect issues and pull requests for every repo in repo_list.csv.

Run standalone:
    python3 data_collection/collect_issues_and_prs.py

Or through the orchestrator:
    python3 data_collection/main.py --step issues_and_prs

Collects records created in the last 3 months (SINCE). Saves pages into:
    data/raw/issues/<owner>__<repo>__page<N>.json
    data/raw/pulls/<owner>__<repo>__page<N>.json

Re-running is safe: repos listed in data/raw/issues_prs_done.txt are
skipped, so an interrupted run picks up where it stopped. Delete that file
(or a line in it) to re-collect those repos.

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
    Repos with Issues / PRs disabled (has_issues / has_pull_requests: false)
    skip that call.
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

DONE_FILE = RAW / "issues_prs_done.txt"

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


def _older_than_since(items):
    """PR pages are sorted newest first, so once the last PR on a page is
    older than SINCE every later page is too. (/pulls ignores `since`.)"""
    return (items[-1].get("created_at") or "") < SINCE


def fetch_pages(stem, subfolder, endpoint, params, useful, max_records, stop=None):
    for old in (RAW / subfolder).glob(f"{stem}__page*.json"):
        old.unlink()  # don't mix pages from an earlier run

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

        if stop and stop(items):
            break
        page += 1
        time.sleep(0.1)


def _load_done():
    """Repos already collected. The first run had no done-file, so any repo
    with saved issue/PR pages from it also counts as done."""
    done = set(DONE_FILE.read_text().split()) if DONE_FILE.exists() else set()
    if not DONE_FILE.exists():
        for sub in ("issues", "pulls"):
            done |= {f.name.split("__page")[0] for f in (RAW / sub).glob("*__page*.json")}
        DONE_FILE.write_text("".join(f"{s}\n" for s in sorted(done)))
    return done


def _repo_flag(stem, flag):
    """Read has_issues / has_pull_requests from the saved repo info."""
    info_path = RAW / "repos" / f"{stem}.json"
    if not info_path.exists():
        return True
    return json.loads(info_path.read_text()).get(flag, True)


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

    done = _load_done()
    todo = [one for one in repos if one["full_name"].replace("/", "__") not in done]
    print(f"  {len(repos) - len(todo)} repos already done, {len(todo)} to collect")

    for n, one in enumerate(todo, 1):
        full = one["full_name"]
        stem = full.replace("/", "__")
        print(f"[{n}/{len(todo)}] {full}")
        try:
            if _repo_flag(stem, "has_issues"):
                fetch_pages(
                    stem,
                    "issues",
                    f"/repos/{full}/issues",
                    {"state": "all", "per_page": 100, "since": SINCE},
                    _is_useful_issue,
                    MAX_ISSUES_PER_REPO,
                )
            else:
                print("  issues disabled on GitHub, skipping issues")
            if _repo_flag(stem, "has_pull_requests"):
                fetch_pages(
                    stem,
                    "pulls",
                    f"/repos/{full}/pulls",
                    {"state": "all", "per_page": 100, "sort": "created", "direction": "desc"},
                    _is_useful_pull,
                    MAX_PULLS_PER_REPO,
                    stop=_older_than_since,
                )
            else:
                print("  pull requests disabled on GitHub, skipping PRs")
            with DONE_FILE.open("a") as f:
                f.write(f"{stem}\n")
            print("  done:", full)
        except SystemExit:
            raise
        except Exception as exc:
            print(f"  !!! failed on {full}: {exc} (skipping repo)")

    return len(repos)


if __name__ == "__main__":
    collect_issues_and_prs()