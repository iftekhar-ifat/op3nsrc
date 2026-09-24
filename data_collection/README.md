# Data Collection Scripts

Scripts for downloading public GitHub data for the Op3nSrc recommendation project. They pull repository metadata, READMEs, issues and pull requests from the GitHub API and save them as raw JSON under `data/raw/`.

## Files

| Script                      | What it does                                                                                                                               |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `main.py`                   | **The standard way to run collection.** Runs every step in order, or a single step with `--step`. Checks `.env` and `repo_list.csv` first. |
| `github_client.py`          | Shared API client. Reads the token from `<project_root>/.env`. Imported by the other scripts, not run directly.                            |
| `generate_repo_list.py`     | Auto-generates a candidate repo list from multiple domain searches, applies filters, writes to `data/repo_list_candidates.csv`.            |
| `find_repos.py`             | Searches GitHub for candidate repositories given a single search query. Prints results so the team can build `data/repo_list.csv`.         |
| `collect_repos.py`          | For every repo in `repo_list.csv`: downloads repo info, README, languages and topics.                                                      |
| `collect_issues_and_prs.py` | For every repo in `repo_list.csv`: downloads issues and pull requests created in the last 3 months, page by page, with quality filters.    |

## Requirements

- Python 3.10+
- A GitHub personal access token

```bash
pip3 install requests python-dotenv
```

## Setup

1. Create a GitHub token at https://github.com/settings/tokens → **Generate new token**.
2. From the project root, copy the template and fill in your token:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env`:
   ```
   GITHUB_TOKEN=ghp_your_token_here
   ```
3. Create `data/repo_list.csv` in the project root. This file lists the repositories to collect, one per row:
   ```csv
   owner,repo,full_name
   fastapi,fastapi,fastapi/fastapi
   pydantic,pydantic,pydantic/pydantic
   pandas-dev,pandas,pandas-dev/pandas
   ```

Run everything from the project root:

```bash
cd /Users/iftekhar/Documents/codes/op3nsrc
```

## Usage

### 1. Find candidate repositories

**Auto-generate a first list (recommended):**

```bash
python3 data_collection/generate_repo_list.py
```

This runs several domain queries (Python + JavaScript/TypeScript + Go + Rust), keeps archiving-friendly + recently-active + non-tutorial repos, dedupes them, and writes the result to `data/repo_list_candidates.csv` (it never overwrites `repo_list.csv` directly).

Use the results to decide the final `repo_list.csv`.

### 2. Collect everything

```bash
python3 data_collection/main.py
```

This does two things in order:

1. Collects repo metadata (info, README, languages, topics).
2. Collects issues and pull requests from the last 3 months.

Before touching the API it checks that `.env` and `data/repo_list.csv` exist, so it fails fast instead of burning requests on a broken setup.

You can also run just one part:

```bash
python3 data_collection/main.py --step repos          # only repo metadata
python3 data_collection/main.py --step issues_and_prs # only issues + PRs
```

### 3. Run the steps individually (optional)

Each step can still be run on its own:

```bash
python3 data_collection/collect_repos.py
python3 data_collection/collect_issues_and_prs.py
```

`collect_repos.py` saves one file per repo into `data/raw/repos/` plus the README into `data/raw/readmes/`:

```text
data/raw/repos/fastapi__fastapi.json
data/raw/repos/fastapi__fastapi__languages.json
data/raw/repos/fastapi__fastapi__topics.json
data/raw/readmes/fastapi__fastapi.md
```

`collect_issues_and_prs.py` saves page files into `data/raw/issues/` and `data/raw/pulls/`:

```text
data/raw/issues/fastapi__fastapi__page1.json ... pageN.json
data/raw/pulls/fastapi__fastapi__page1.json ... pageN.json
```

The 3-month window is set in the `SINCE` constant at the top of `collect_issues_and_prs.py`. Adjust it if needed.

Note: GitHub's issues endpoint returns pull requests mixed in with issues. A record where `"pull_request"` is not null is actually a PR — that's expected and is filtered out during cleaning.

## Output

```text
data/
├── repo_list.csv          # the repo list you created
└── raw/
    ├── repos/             # repo JSON + languages + topics
    ├── readmes/           # raw README markdown
    ├── issues/            # issue/PR page JSON
    └── pulls/             # pull request page JSON
```

### What each file is for

**`data/repo_list.csv`** — the master list of repositories the team agreed on. It has one row per repo, three columns: `owner`, `repo`, `full_name` (`owner/repo` combined). The CSV format just makes it easy for the scripts to read one row at a time and for you to review/edit the list in Excel or a text editor. Changing this file and re-running `main.py` is all you need to change which repos get collected.

```csv
owner,repo,full_name
fastapi,fastapi,fastapi/fastapi
pydantic,pydantic,pydantic/pydantic
```

Row 1 is always the header (column names). Each row after it is one repository.

### How many files per repo

For every repo in `repo_list.csv`, running `collect_repos.py` and `collect_issues_and_prs.py` together produces:

| Repo `full_name`  | Files produced                                                                                        | Where they land     |
| ----------------- | ----------------------------------------------------------------------------------------------------- | ------------------- |
| `fastapi/fastapi` | 4 files: `fastapi__fastapi.json`, `fastapi__fastapi__languages.json`, `fastapi__fastapi__topics.json` | `data/raw/repos/`   |
|                   | 1 file: `fastapi__fastapi.md` (the README)                                                            | `data/raw/readmes/` |
|                   | Up to 100 issues (1 or more page files) — **capped at 100 issues per repo**                           | `data/raw/issues/`  |
|                   | Up to 50 PRs (1 or more page files) — **capped at 50 pull requests per repo**                         | `data/raw/pulls/`   |

So it's not "one file per repo" — it's:

- `collect_repos.py` → **4 files per repo** (3 JSON in `repos/` + 1 README in `readmes/`).
- `collect_issues_and_prs.py` → **a variable number of page files**, because the number depends on how many issues/PRs the repo had in the last 3 months (and caps at 100 / 50 per repo).

Why the `__` in the filename? A repo name is `owner/repo`, which can't be used as a filename, so the `/` is replaced with `__`. `fastapi/fastapi` → `fastapi__fastapi`.

### Understanding the page files

The GitHub API returns at most **100 records per request**. Collection also **caps how many records we keep per repo** so one huge repo can't dominate the dataset. So:

- Issues: up to **100 issues** kept per repo, e.g. a repo with 250 issues gives you 100; one with 30 gives you all 30.
- Pull requests: up to **50 PRs** kept per repo, e.g. a repo with 80 PRs gives you 50; one with 20 gives you all 20.
- 0 issues/PRs → no page file at all (or one empty).

Each page file is a JSON **array** starting with `[`, so a `page1.json` for a big repo will contain up to 100 issue records. Don't worry if you see a huge file — more records is normal.

Also note: GitHub returns pull requests inside the issues endpoint too. A record that has a non-null `"pull_request"` key is actually a PR, not an issue. That's expected — the cleaning step (Week 2) separates them.

### Why we store JSON and not CSV for the raw data

The raw GitHub responses are nested (e.g. labels are a list of objects, dates are strings with a `Z` suffix). JSON keeps that structure exactly as GitHub returned it, so nothing is lost. CSV is for Week 2, when we flatten the useful fields into tables.

### Sample output (what to see when you open a file)

`data/raw/repos/fastapi__fastapi.json` (shortened):

```json
{
  "full_name": "fastapi/fastapi",
  "description": "FastAPI framework, high performance, easy to learn, fast to code, ready for production",
  "topics": ["fastapi", "api", "web"],
  "stargazers_count": 78000,
  "forks_count": 6200,
  "open_issues_count": 410,
  "archived": false,
  "created_at": "2018-12-01T17:41:36Z",
  "updated_at": "2026-09-08T10:12:00Z",
  "language": "Python"
}
```

`data/raw/issues/fastapi__fastapi__page1.json` — an array of records; each one looks like (shortened):

```json
[
  {
    "number": 942,
    "title": "Add pagination to endpoint",
    "state": "open",
    "labels": [{ "name": "enhancement" }, { "name": "good first issue" }],
    "created_at": "2026-05-02T09:00:00Z",
    "closed_at": null,
    "comments": 6,
    "body": "### Context\nUsers can't navigate large lists. Need `limit` and `offset`...",
    "user": { "login": "octocat" },
    "pull_request": null
  }
]
```

`data/raw/pulls/fastapi__fastapi__page1.json` — an array of PR records; each one looks like (shortened):

```json
[
  {
    "number": 119,
    "title": "Implement endpoint pagination",
    "state": "closed",
    "user": { "login": "scientist_99" },
    "created_at": "2026-05-10T14:00:00Z",
    "merged_at": "2026-05-15T08:00:00Z",
    "body": "Adds `limit`/`offset` query params... Fixes #942",
    "commits": 4,
    "changed_files": 5,
    "additions": 120,
    "deletions": 30
  }
]
```

### How to verify your collection

- **Files per repo:** for each repo in your chunk of `repo_list.csv`, you should count exactly **4 files** from `collect_repos.py` (3 in `repos/`, 1 README in `readmes/`) plus at least one issue/PR page file if the repo has activity. A repo with 0 issues/PRs in the last 3 months may have none.
- **File names match:** `ls data/raw/repos/` should show `<owner>__<repo>.json` plus `<owner>__<repo>__languages.json` and `<owner>__<repo>__topics.json` for each entry in your list.
- **Content looks right:** open a file — repos should show `full_name`, `language` and `archived`; issues should show `title`, `state` and `body`; PRs should show `merged_at`.
- **Size makes sense:** total kept records per repo should be at most **100 issues** and **50 PRs**, and each page file (except the last) should hold a full page of records.
- **No errors:** the script printed `done: <repo>` for every repo it collected.

A quick spot-check command:

```bash
ls data/raw/repos/ | wc -l        # should be 3 x (number of repos in your chunk)
ls data/raw/issues/ | wc -l       # should be at least (number of repos in your chunk)
ls data/raw/pulls/ | wc -l        # should be at least (number of repos in your chunk)
```

If a repo genuinely has no issues, having no issue page file is normal. If a repo that clearly has issues produced nothing, the script likely stopped early — check the troubleshooting table below.

The raw JSON is the input for the cleaning step (Week 2), documented in `../data-collection-and-processing.md`. Raw responses are never hand-edited; any fixes happen in the cleaning scripts so the pipeline stays reproducible.

## Rate limits

- Authenticated requests: 5,000/hour per account.
- Both `collect_repos.py` and `collect_issues_and_prs.py` request data in pages of `per_page=100`, which is the maximum.
- If you hit the limit you'll get a clear error message; wait until the reset time and rerun. The scripts overwrite the same files, so rerunning is safe.
- If the team splits the repo list, each person uses their own token, so the quota doesn't collide.

## Troubleshooting

| Error                         | Meaning                                 | Fix                                               |
| ----------------------------- | --------------------------------------- | ------------------------------------------------- |
| `401 Unauthorized`            | Token missing or wrong                  | Check `GITHUB_TOKEN` in `.env`                    |
| `403 API rate limit exceeded` | Out of hourly requests                  | Wait for reset; don't collect more repos per run  |
| `404 Not Found`               | A repo in `repo_list.csv` doesn't exist | Check the `owner/repo` spelling (case matters)    |
| 403 "secondary rate limit"    | Requests too fast                       | Increase `time.sleep(0.1)` to `0.5` in the script |
