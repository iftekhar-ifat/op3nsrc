"""Auto-generate a candidate repo list from multiple domain searches.

Runs several GitHub search queries (one per domain), applies inclusion
filters, dedupes, and writes the results to a CSV so the team can review
and prune.

Usage:
    python3 data_collection/generate_repo_list.py
    python3 data_collection/generate_repo_list.py --queries "fastapi" "django"
    python3 data_collection/generate_repo_list.py --per-query 60 --output data/repo_list_candidates.csv

Defaults:
    queries      = Python, JavaScript, TypeScript, Go and Rust focus
    per-query    = 30 repos per query
    max-stars    = no cap
    min-stars    = 1000
    output       = data/repo_list_candidates.csv (never overwrites repo_list.csv)
"""

import argparse
import csv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from github_client import ROOT, get

DEFAULT_QUERIES = [
    "language:python fastapi",
    "language:python django",
    "language:python flask",
    "language:python pandas",
    "language:python scikit-learn",
    "language:python pytorch",
    "language:python data",
    "language:python airflow",
    "language:python langchain",
    "language:python jupyter",
    "language:javascript react",
    "language:javascript node",
    "language:javascript express",
    "language:typescript next.js",
    "language:typescript vue",
    "language:typescript graphql",
    "language:go web",
    "language:go cli",
    "language:go kubernetes",
    "language:rust cli",
]

FILTER_WORDS = ("awesome", "tutorial", "cheat-sheet", "samples", "example")


def matches_inclusion(repo, min_stars, max_age_days):
    """Return True if repo passes the inclusion filters."""
    if repo.get("archived"):
        return False
    if (repo.get("stargazers_count") or 0) < min_stars:
        return False

    desc = (repo.get("description") or "").lower()
    if any(w in desc for w in FILTER_WORDS):
        return False

    pushed = repo.get("pushed_at")
    if pushed:
        pushed_ts = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - pushed_ts > timedelta(days=max_age_days):
            return False

    return True


def search(query, per_query, min_stars, max_age_days):
    data = get("/search/repositories", {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": per_query,
    })
    return [
        r for r in data.get("items", []) if matches_inclusion(r, min_stars, max_age_days)
    ]


def main():
    parser = argparse.ArgumentParser(description="Generate candidate repo list.")
    parser.add_argument("--queries", nargs="+", default=DEFAULT_QUERIES,
                        help="GitHub search queries (default: Python, JS/TS, Go, Rust domains)")
    parser.add_argument("--per-query", type=int, default=30,
                        help="Repos to fetch per query (default: 30)")
    parser.add_argument("--min-stars", type=int, default=1000,
                        help="Minimum star count (default: 1000)")
    parser.add_argument("--max-age-days", type=int, default=90,
                        help="Max days since last push to accept (default: 90 = 3 months)")
    parser.add_argument("--output", default="data/repo_list_candidates.csv",
                        help="Output file (default: data/repo_list_candidates.csv)")
    args = parser.parse_args()

    output = ROOT / args.output
    if str(output).endswith("repo_list.csv"):
        print("Refusing to overwrite repo_list.csv directly. Use a different --output.")
        sys.exit(1)

    seen = {}
    for query in args.queries:
        print(f"query: {query}")
        matched = search(query, args.per_query, args.min_stars, args.max_age_days)
        for repo in matched:
            seen[repo["full_name"]] = repo
        print(f"  -> {len(matched)} matched")

    seen = dict(sorted(seen.items(), key=lambda kv: -kv[1]["stargazers_count"]))

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["owner", "repo", "full_name"])
        for full in seen:
            owner, repo = full.split("/", 1)
            writer.writerow([owner, repo, full])

    print(f"\nWrote {len(seen)} unique candidate repos to {output}")
    print("Review the list, prune it, then copy it to data/repo_list.csv before running main.py.")


if __name__ == "__main__":
    main()