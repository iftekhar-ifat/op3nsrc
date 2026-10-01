# Data Collection Scripts

Scripts for downloading public GitHub data for the Op3nSrc recommendation project and turning it into clean tables. The collection scripts pull repository metadata, READMEs, issues and pull requests from the GitHub API and save them as raw JSON under `data/raw/`; `clean.py` turns that into CSV tables under `data/cleaned/`.

## Files

| Script                      | What it does                                                                                                                               |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `main.py`                   | **The standard way to run collection.** Runs every step in order, or a single step with `--step`. Checks `.env` and `repo_list.csv` first. |
| `github_client.py`          | Shared API client. Reads the token from `<project_root>/.env`; waits on rate limits, retries network/server errors, fails fast on 404. Not run directly. |
| `find_repos.py`             | Searches GitHub for candidate repositories given a single search query. Prints results so the team can build `data/repo_list.csv`.         |
| `collect_repos.py`          | For every repo in `repo_list.csv`: downloads repo info, README (any file name, follows symlinks), languages and topics.                    |
| `collect_issues_and_prs.py` | For every repo in `repo_list.csv`: downloads issues and merged pull requests from the last 3 months, with quality filters. Resumable.      |
| `clean.py`                  | **Offline.** Turns `data/raw/` into the cleaned tables in `data/cleaned/` (see [Cleaning](#cleaning)).                                     |

## Requirements

- Python 3.10+
- A GitHub personal access token

Use the project environment (see the root `README.md`):

```bash
source .venv/bin/activate
pip install -r requirements.txt
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
3. `data/repo_list.csv` is already created in the project root. **The repos in it were hand-picked by the team members** — everyone agreed on which projects to include. You collect exactly what's in this file, nothing else:
   ```csv
   owner,repo,full_name
   tiangolo,fastapi,tiangolo/fastapi
   pydantic,pydantic,pydantic/pydantic
   pandas-dev,pandas,pandas-dev/pandas
   ```

Run everything from the project root (the folder that contains `data/` and `.env`).

## Usage

### 1. Find candidate repositories (optional)

The repos in `data/repo_list.csv` were **hand-picked by the team members** — everyone agreed on the final list before collection started. If you want to explore which projects exist before deciding, you can search:

```bash
python3 data_collection/find_repos.py "language:python fastapi"
```

This prints candidate results; change the query to whatever fits (e.g. `react`, `django`, `go`). Use it only to *inform* decisions already made — `main.py` collects exactly what's in `repo_list.csv`, no more.

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
python3 data_collection/main.py --step readmes        # re-fetch only missing/broken READMEs
```

**Resuming:** `collect_issues_and_prs.py` records every finished repo in `data/raw/issues_prs_done.txt` and skips those on the next run. If a run stops (rate limit, Ctrl+C, laptop sleep), just run the same command again. To re-collect a repo, delete its line from that file — its old page files are replaced automatically.

**Repos with Issues or PRs disabled on GitHub** (`has_issues` / `has_pull_requests` is `false` in the repo JSON) skip that request. A repo that returns `404` is reported as `!!! failed on ...` and skipped without stopping the run; it is retried on the next run.

### 3. Run the steps individually (optional)

Each step can still be run on its own:

```bash
python3 data_collection/collect_repos.py
python3 data_collection/collect_issues_and_prs.py
```

`collect_repos.py` saves one file per repo into `data/raw/repos/` plus the README into `data/raw/readmes/`:

```text
data/raw/repos/tiangolo__fastapi.json
data/raw/repos/tiangolo__fastapi__languages.json
data/raw/repos/tiangolo__fastapi__topics.json
data/raw/readmes/tiangolo__fastapi.md
```

`collect_issues_and_prs.py` saves page files into `data/raw/issues/` and `data/raw/pulls/`:

```text
data/raw/issues/tiangolo__fastapi__page1.json ... pageN.json
data/raw/pulls/tiangolo__fastapi__page1.json ... pageN.json
```

The 3-month window is set in the `SINCE` constant at the top of `collect_issues_and_prs.py`. Adjust it if needed.

Filters applied while collecting:

- **Issues:** PRs (the issues endpoint mixes them in), `[bot]` authors and near-empty issues are dropped; max 100 per repo. Note that GitHub's `since` filter means *updated* since, so some older issues with recent activity are included (flagged later as `created_in_window = False`).
- **PRs:** only merged, non-bot PRs whose text references an issue (`Fixes/Closes/Resolves/Refs #N`); max 50 per repo. The PR endpoint ignores `since`, so paging stops as soon as it reaches PRs created before `SINCE`.
- Pages with nothing worth keeping are not saved, so page numbers can have gaps (e.g. `page3`, `page5`).

## Output

```text
data/
├── repo_list.csv              # the 202 repos
├── raw/
│   ├── repos/                 # repo JSON + languages + topics
│   ├── readmes/               # raw README text
│   ├── issues/                # issue page JSON
│   ├── pulls/                 # merged-PR page JSON
│   └── issues_prs_done.txt    # repos already collected (for resuming)
└── cleaned/                   # tables built by clean.py
```

### What each file is for

**`data/repo_list.csv`** — the master list of repositories the team agreed on. It has one row per repo, three columns: `owner`, `repo`, `full_name` (`owner/repo` combined). The CSV format just makes it easy for the scripts to read one row at a time and for you to review/edit the list in Excel or a text editor. Changing this file and re-running `main.py` is all you need to change which repos get collected.

```csv
owner,repo,full_name
tiangolo,fastapi,tiangolo/fastapi
pydantic,pydantic,pydantic/pydantic
```

Row 1 is always the header (column names). Each row after it is one repository.

### How many files per repo

For every repo in `repo_list.csv`, running `collect_repos.py` and `collect_issues_and_prs.py` together produces:

| Repo `full_name`  | Files produced                                                                                        | Where they land     |
| ----------------- | ----------------------------------------------------------------------------------------------------- | ------------------- |
| `tiangolo/fastapi` | 3 files: `tiangolo__fastapi.json`, `tiangolo__fastapi__languages.json`, `tiangolo__fastapi__topics.json` | `data/raw/repos/`   |
|                   | 1 file: `tiangolo__fastapi.md` (the README)                                                            | `data/raw/readmes/` |
|                   | Up to 100 issues (1 or more page files) — **capped at 100 issues per repo**                           | `data/raw/issues/`  |
|                   | Up to 50 PRs (1 or more page files) — **capped at 50 pull requests per repo**                         | `data/raw/pulls/`   |

So it's not "one file per repo" — it's:

- `collect_repos.py` → **4 files per repo** (3 JSON in `repos/` + 1 README in `readmes/`).
- `collect_issues_and_prs.py` → **a variable number of page files**, because the number depends on how many issues/PRs the repo had in the last 3 months (and caps at 100 / 50 per repo).

Why the `__` in the filename? A repo name is `owner/repo`, which can't be used as a filename, so the `/` is replaced with `__`. `tiangolo/fastapi` → `tiangolo__fastapi`.

### Understanding the page files

The GitHub API returns at most **100 records per request**. Collection also **caps how many records we keep per repo** so one huge repo can't dominate the dataset. So:

- Issues: up to **100 issues** kept per repo, e.g. a repo with 250 issues gives you 100; one with 30 gives you all 30.
- Pull requests: up to **50 PRs** kept per repo, e.g. a repo with 80 PRs gives you 50; one with 20 gives you all 20.
- 0 issues/PRs → no page file at all (or one empty).

Each page file is a JSON **array** starting with `[`, so a `page1.json` for a big repo will contain up to 100 issue records. Don't worry if you see a huge file — more records is normal.

Also note: GitHub returns pull requests inside the issues endpoint too. A record that has a non-null `"pull_request"` key is actually a PR, not an issue. The collector already drops them, and `clean.py` checks again.

### Why we store JSON and not CSV for the raw data

The raw GitHub responses are nested (e.g. labels are a list of objects, dates are strings with a `Z` suffix). JSON keeps that structure exactly as GitHub returned it, so nothing is lost. CSV is for Week 2, when we flatten the useful fields into tables.

### Sample output (what to see when you open a file)

`data/raw/repos/tiangolo__fastapi.json` (shortened):

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

`data/raw/issues/tiangolo__fastapi__page1.json` — an array of records; each one looks like (shortened):

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

`data/raw/pulls/tiangolo__fastapi__page1.json` — an array of PR records; each one looks like (shortened):

```json
[
  {
    "number": 119,
    "title": "Implement endpoint pagination",
    "state": "closed",
    "user": { "login": "scientist_99" },
    "created_at": "2026-05-10T14:00:00Z",
    "merged_at": "2026-05-15T08:00:00Z",
    "body": "Adds `limit`/`offset` query params... Fixes #942"
  }
]
```

### How to verify your collection

- **Files per repo:** for each repo in `repo_list.csv`, you should count exactly **4 files** from `collect_repos.py` (3 in `repos/`, 1 README in `readmes/`) plus at least one issue/PR page file if the repo has activity. A repo with 0 issues/PRs in the last 3 months may have none.
- **File names match:** `ls data/raw/repos/` should show `<owner>__<repo>.json` plus `<owner>__<repo>__languages.json` and `<owner>__<repo>__topics.json` for each entry in your list.
- **Content looks right:** open a file — repos should show `full_name`, `language` and `archived`; issues should show `title`, `state` and `body`; PRs should show `merged_at`.
- **Size makes sense:** total kept records per repo should be at most **100 issues** and **50 PRs**. Page files hold only the records that passed the filters, so they are usually smaller than 100.
- **No errors:** the script printed `done: <repo>` for every repo, and `data/raw/issues_prs_done.txt` has one line per repo in `repo_list.csv`.

A quick spot-check command:

```bash
ls data/raw/repos/ | wc -l        # should be 3 x (number of repos)
ls data/raw/issues/ | wc -l       # should be at least (number of repos)
ls data/raw/pulls/ | wc -l        # should be at least (number of repos)
```

If a repo genuinely has no issues, having no issue page file is normal. If a repo that clearly has issues produced nothing, the script likely stopped early — check the troubleshooting table below.

The raw JSON is the input for the cleaning step (Week 2), documented in `../data-collection-and-processing.md`. Raw responses are never hand-edited; any fixes happen in the cleaning scripts so the pipeline stays reproducible.

## Rate limits

- Authenticated requests: 5,000/hour per account.
- Both `collect_repos.py` and `collect_issues_and_prs.py` request data in pages of `per_page=100`, which is the maximum.
- If you hit the limit the client prints how long it waits and continues by itself (it honours `Retry-After` for secondary limits). If you stop it, rerun — finished repos are skipped.

## Troubleshooting

| Error                         | Meaning                                 | Fix                                               |
| ----------------------------- | --------------------------------------- | ------------------------------------------------- |
| `401 Unauthorized`            | Token missing or wrong                  | Check `GITHUB_TOKEN` in `.env`                    |
| `Rate limit reached ... Waiting N seconds` | Out of hourly requests     | Nothing — it continues by itself after the reset  |
| `!!! failed on owner/repo: 404`           | Repo renamed/deleted, or Issues/PRs disabled | Check the spelling in `repo_list.csv` (case matters) and the repo on GitHub |
| Run stopped halfway                       | Ctrl+C / sleep / network    | Rerun the same command — it resumes               |
| 403 "secondary rate limit"                | Requests too fast           | Handled automatically; if frequent, raise `time.sleep(0.1)` to `0.5` |

## Cleaning

```bash
python3 data_collection/clean.py
```

Runs offline in ~10 s, never modifies `data/raw/`, and rewrites `data/cleaned/`:

| File                        | One row per                       | Key columns                                                                 |
| --------------------------- | --------------------------------- | --------------------------------------------------------------------------- |
| `repositories.csv`          | repo                              | `repo_id`, `current_full_name`, `description_clean`, `readme_clean`, `topics`, `languages`, `stars` |
| `issues.csv`                | issue                             | `issue_id`, `final_text`, `labels`, `is_beginner_friendly`, `is_help_wanted`, `state`, `created_in_window`, `linked_pr_ids` |
| `pull_requests.csv`         | merged PR                         | `pr_id`, `author_login`, `closes_issue_ids`, `references_issue_ids`, `link_verified` |
| `developer_profiles.csv`    | PR author                         | `developer_id`, `languages`, `topics`, `pr_titles`, `experience_text`, `merged_pr_count` |

What it does:

- **IDs:** `repo_id = "owner/repo"` as in `repo_list.csv` (17 repos were renamed on GitHub; the new name is in `current_full_name`), `issue_id = "owner/repo#123"`, `pr_id = "owner/repo!456"`, `developer_id = login`.
- **Bots removed:** GitHub `type: Bot` accounts (e.g. Copilot), logins ending in `bot`/`robot`, and CI reporters (`cockroach-teamcity`, `elasticsearchmachine`, `GordonTheTurtle`).
- **Text:** strips issue-template comments and checklists, code blocks, inline code, images, HTML, URLs and markdown syntax; lowercases. `final_text` = title + body (title alone if the body is empty). No stemming/stopwords — the TF-IDF model does that itself.
- **Labels:** lowercased, emoji removed; beginner/help-wanted flags catch variants like `e-easy`, `good-first-issue`, `first-contribution`, `status: help wanted`.
- **PR → issue links:** GitHub closing keywords (`close/closes/closed`, `fix/fixes/fixed`, `resolve/resolves/resolved`) with `#N`, `owner/repo#N` or a full issue URL. `refs #N` is kept as a reference only, not as a closing link.

Read the tables with:

```python
import json, pandas as pd
issues = pd.read_csv("data/cleaned/issues.csv", keep_default_na=False)
issues["labels"] = issues["labels"].map(json.loads)
```

