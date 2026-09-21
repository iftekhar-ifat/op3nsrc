"""Find candidate repositories with the GitHub search API.

Usage:
    python3 data_collection/find_repos.py "fastapi"
    python3 data_collection/find_repos.py "language:python stars:>5000"

Prints full_name + description so the team can build data/repo_list.csv.
"""

import sys

from github_client import get


def main(query):
    data = get("/search/repositories", {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 50,
    })
    print(f"{data['total_count']} results found. Showing top {len(data['items'])}:\n")
    for repo in data["items"]:
        desc = (repo.get("description") or "").strip() or "(no description)"
        print(f"{repo['full_name']:40s} stars={repo['stargazers_count']:>7}  {desc}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])