# Data collection & cleaning

Downloads public GitHub data for the repos in `data/repo_list.csv` (→ `data/raw/`, raw JSON) and turns it
into clean tables (→ `data/cleaned/`, CSV).

| File | What it does |
|---|---|
| `main.py` | Runs the collection: all steps, or one with `--step repos` / `--step issues_and_prs` |
| `github_client.py` | Shared API client: reads the token, waits on rate limits, retries network/server errors, skips a repo on 4xx |
| `collect_repos.py` | Per repo: info, README (any file name, symlinks followed), languages, topics |
| `collect_issues_and_prs.py` | Per repo: issues and merged PRs from the last 3 months, filtered; resumable |
| `clean.py` | **Offline:** `data/raw/` → `data/cleaned/` |

## Setup (only needed to re-collect)

1. Activate the project environment (see the root `README.md`).
2. Create a token at https://github.com/settings/tokens → *Generate new token (classic)*, **no scopes**.
3. Put it in `.env` in the project root (never commit it):
   ```bash
   cp .env.example .env      # then set GITHUB_TOKEN=ghp_...
   ```

## Run

From the project root:

```bash
python3 data_collection/main.py       # collect (~30 min for 202 repos)
```

```bash
python3 data_collection/clean.py      # build the cleaned tables (~10 s, offline)
```

- **Resumable:** finished repos are listed in `data/raw/issues_prs_done.txt` and skipped on the next run.
  If a run stops, run it again. Delete a line to re-collect that repo.
- Repos with Issues or PRs disabled on GitHub skip that request; a repo returning 404 is skipped and retried
  next run.

## What is collected

- **Issues:** active since `SINCE` (2026-06-24, top of `collect_issues_and_prs.py`), max **100 per repo**.
  GitHub's `since` means *updated* since, so some older issues are included (`created_in_window = False`).
  PRs mixed into the issues endpoint, bot authors and near-empty issues are dropped.
- **PRs:** merged, non-bot, created since `SINCE`, and referencing an issue (`Fixes/Closes/Resolves/Refs #N`);
  max **50 per repo**. Paging stops once PRs are older than `SINCE`.
- Files: `data/raw/{repos,readmes,issues,pulls}/<owner>__<repo>…` (`/` → `__`). Pages with nothing kept
  are not saved, so page numbers can have gaps.

## What `clean.py` does

1. Deduplicates issues/PRs by repo + number; drops archived repos.
2. Removes bots: GitHub `type: Bot`, logins ending in `bot`/`robot`, and CI accounts
   (`cockroach-teamcity`, `elasticsearchmachine`, `GordonTheTurtle`).
3. Cleans text: removes issue-template comments/checklists, code, URLs, images, HTML, markdown; lowercases.
4. Normalises labels and flags beginner-friendly / help-wanted issues (`good first issue`, `e-easy`,
   `first-contribution`, `status: help wanted`, …).
5. Links PRs to issues with GitHub's closing keywords (`fixes #N`, `owner/repo#N`, issue URLs);
   `refs #N` counts as a reference only.

### Output tables (`data/cleaned/`)

Read with `pd.read_csv(path, keep_default_na=False)` (or `recommender.data.load`); list columns are JSON.

| Table | Rows | Columns |
|---|---|---|
| `repositories.csv` | 202 | `repo_id` (as in `repo_list.csv`), `current_full_name` (after renames), `description_clean`, `readme_clean`, `topics`, `primary_language`, `languages` (share of bytes), `stars`, `forks`, `open_issues`, `created_at`, `pushed_at`, `html_url` |
| `issues.csv` | 15,053 | `issue_id` (`owner/repo#N`), `repo_id`, `number`, `title`, `title_clean`, `body_clean`, `final_text` (title + body), `labels`, `is_beginner_friendly`, `is_help_wanted`, `state`, `state_reason`, `created_at`, `updated_at`, `closed_at`, `created_in_window`, `author_login`, `author_association`, `html_url`, `linked_pr_ids` |
| `pull_requests.csv` | 4,003 | `pr_id` (`owner/repo!N`), `repo_id`, `number`, `title`, `title_clean`, `body_clean`, `author_login`, `author_association`, `created_at`, `merged_at`, `labels`, `closes_issue_ids`, `references_issue_ids`, `closes_issue_ids_in_data`, `html_url` |

Running `clean.py` twice gives identical files; `data/raw/` is never modified.

## Troubleshooting

| Message | Meaning | Fix |
|---|---|---|
| `401 Unauthorized` | token missing, wrong or expired | set a valid `GITHUB_TOKEN` in `.env` |
| `Rate limit reached … Waiting N seconds` | hourly quota used up | nothing — it continues by itself |
| `!!! failed on owner/repo: 404` | repo renamed/deleted, or Issues/PRs disabled | check the name in `repo_list.csv` |
| run stopped halfway | Ctrl+C, sleep, network | run the same command again — it resumes |
