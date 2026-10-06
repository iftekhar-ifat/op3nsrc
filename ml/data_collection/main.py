"""Run the whole data collection in one go.

Usage:
    python3 data_collection/main.py                     # everything
    python3 data_collection/main.py --step repos        # just repo metadata
    python3 data_collection/main.py --step issues_and_prs   # just issues + PRs

Steps run in order and each one is also runnable standalone:
    1. repos           -> collect_repos.collect_repos()
    2. issues_and_prs  -> collect_issues_and_prs.collect_issues_and_prs()
"""

import argparse
import sys
from pathlib import Path

from github_client import RAW, REPO_LIST

STEPS = {
    "repos": ("collect_repos", "collect_repos", "repo metadata (info, README, languages, topics)"),
    "issues_and_prs": ("collect_issues_and_prs", "collect_issues_and_prs", "issues + pull requests (last 3 months)"),
}


def check_prereqs():
    """Fail fast before any API call if setup is wrong."""
    if not Path(".env").exists() and not (Path(__file__).parent.parent / ".env").exists():
        print("Error: .env not found. Copy .env.example to .env and add your token.")
        sys.exit(1)
    if not REPO_LIST.exists():
        print(
            f"Error: {REPO_LIST} not found. "
            "Create 'owner,repo,full_name' rows in data/repo_list.csv first."
        )
        sys.exit(1)


def run_step(name: str) -> None:
    module_name, func_name, desc = STEPS[name]
    module = __import__(module_name)
    func = getattr(module, func_name)

    print(f"\n== Step: {name} ({desc}) ==")
    count = func()
    print(f"== done: {count} repos processed ==")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Op3nSrc data collection.")
    parser.add_argument(
        "--step",
        choices=list(STEPS),
        help="Run a single step instead of everything.",
    )
    args = parser.parse_args()

    check_prereqs()

    RAW.mkdir(parents=True, exist_ok=True)

    if args.step:
        run_step(args.step)
        return

    for name in STEPS:
        run_step(name)

    print("\nAll steps finished. Verify with: ls", RAW)


if __name__ == "__main__":
    main()