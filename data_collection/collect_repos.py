"""Collect repo info, README, languages, topics for every repo in repo_list.csv.

Run standalone:
    python3 data_collection/collect_repos.py

Or through the orchestrator:
    python3 data_collection/main.py --step repos

Saves into:
    data/raw/repos/<owner>__<repo>.json
    data/raw/repos/<owner>__<repo>__languages.json
    data/raw/repos/<owner>__<repo>__topics.json
    data/raw/readmes/<owner>__<repo>.md
"""

import csv
import json

import requests

from github_client import RAW, REPO_LIST, get

(RAW / "repos").mkdir(parents=True, exist_ok=True)
(RAW / "readmes").mkdir(parents=True, exist_ok=True)


def collect_repos() -> int:
    """Download repo metadata for every repo in repo_list.csv.

    A failure on one repo is reported and skipped, so the rest still gets
    collected. Returns the number of repos attempted.
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
            info = get(f"/repos/{full}")
            (RAW / "repos" / f"{stem}.json").write_text(json.dumps(info, indent=2))

            readme = requests.get(
                f"https://raw.githubusercontent.com/{full}/HEAD/README.md",
                timeout=30,
            )
            (RAW / "readmes" / f"{stem}.md").write_text(readme.text)

            langs = get(f"/repos/{full}/languages")
            (RAW / "repos" / f"{stem}__languages.json").write_text(
                json.dumps(langs, indent=2)
            )

            topics = get(
                f"/repos/{full}/topics",
                headers={"Accept": "application/vnd.github.mercy-preview+json"},
            )
            (RAW / "repos" / f"{stem}__topics.json").write_text(
                json.dumps(topics, indent=2)
            )

            print("  collected:", full)
        except SystemExit:
            raise
        except Exception as exc:
            print(f"  !!! failed on {full}: {exc} (skipping repo)")

    return len(repos)


if __name__ == "__main__":
    collect_repos()