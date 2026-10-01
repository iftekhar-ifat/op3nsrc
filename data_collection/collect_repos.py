"""Collect repo info, README, languages, topics for every repo in repo_list.csv.

Run standalone:
    python3 data_collection/collect_repos.py

Or through the orchestrator:
    python3 data_collection/main.py --step repos
    python3 data_collection/main.py --step readmes   # only re-fetch missing/broken READMEs

Saves into:
    data/raw/repos/<owner>__<repo>.json
    data/raw/repos/<owner>__<repo>__languages.json
    data/raw/repos/<owner>__<repo>__topics.json
    data/raw/readmes/<owner>__<repo>.md
"""

import csv
import json

from github_client import RAW, REPO_LIST, get, get_text

(RAW / "repos").mkdir(parents=True, exist_ok=True)
(RAW / "readmes").mkdir(parents=True, exist_ok=True)

# Old runs guessed README.md on raw.githubusercontent.com and saved this
# error page when the file had another name (README.rst, readme.md, ...).
BROKEN_README = "404: Not Found"


def _load_repo_list():
    if not REPO_LIST.exists():
        raise SystemExit(
            f"{REPO_LIST} not found. Create it (owner,repo,full_name) first."
        )
    repos = list(csv.DictReader(REPO_LIST.open()))
    if not repos:
        raise SystemExit("repo_list.csv is empty.")
    return repos


def _is_symlink_target(text):
    """True if the README body is only a relative path like 'docs/README.md'."""
    t = text.strip()
    return "\n" not in t and " " not in t and len(t) < 200 and t.lower().endswith((".md", ".rst", ".txt"))


def _needs_readme(path):
    """README missing, saved as a 404 page, or saved as a bare symlink target."""
    if not path.exists():
        return True
    text = path.read_text(errors="ignore")
    return text.startswith(BROKEN_README) or _is_symlink_target(text)


def _fetch_readme(full, stem):
    """Save the repo's README (whatever its file name) via the /readme endpoint."""
    raw = {"Accept": "application/vnd.github.raw"}
    text = get_text(f"/repos/{full}/readme", headers=raw)
    # A symlinked README comes back as just its target path
    # (e.g. "axum/README.md") -> fetch the file it points to.
    if text and _is_symlink_target(text):
        text = get_text(f"/repos/{full}/contents/{text.strip()}", headers=raw)
    # No README at all -> save an empty file so the repo still has one.
    (RAW / "readmes" / f"{stem}.md").write_text(text or "")


def collect_repos() -> int:
    """Download repo metadata for every repo in repo_list.csv.

    A failure on one repo is reported and skipped, so the rest still gets
    collected. Returns the number of repos attempted.
    """
    repos = _load_repo_list()

    for one in repos:
        full = one["full_name"]
        stem = full.replace("/", "__")
        try:
            info = get(f"/repos/{full}")
            (RAW / "repos" / f"{stem}.json").write_text(json.dumps(info, indent=2))

            _fetch_readme(full, stem)

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


def collect_readmes() -> int:
    """Re-fetch only READMEs that are missing, a 404 page, or a symlink target."""
    repos = _load_repo_list()
    fixed = 0

    for one in repos:
        full = one["full_name"]
        stem = full.replace("/", "__")
        path = RAW / "readmes" / f"{stem}.md"
        if not _needs_readme(path):
            continue
        try:
            _fetch_readme(full, stem)
            fixed += 1
            print("  readme fixed:", full)
        except SystemExit:
            raise
        except Exception as exc:
            print(f"  !!! failed on {full}: {exc} (skipping repo)")

    print(f"  {fixed} READMEs re-fetched")
    return len(repos)


if __name__ == "__main__":
    collect_repos()
