# Op3nSrc: Week 1 Task — Data Collection

**Goal for this week:** download the repos in `data/repo_list.csv` (hand-picked by the team) plus their issues and pull requests, and save everything as raw JSON under `data/raw/`.

Everyone works on their **own machine**. Nothing is pushed or shared anywhere.

---

## 0. What data are we grabbing?

For each repo:

1. Repo info — description, topics, stars, etc.
2. README — the raw text file
3. Issues created in the last 3 months — title + body are the text the NLP model matches on
4. Pull requests in the last 3 months — tells us which developer fixed which issue

Output is just a folder of JSON files, sitting on your machine.

---

## 1. First-time setup

1. Make sure Python 3.10+ is installed (`python3 --version`).
2. Install the two libraries we need:
   ```bash
   pip3 install requests python-dotenv
   ```
3. Generate a GitHub personal access token:
   - https://github.com/settings/tokens → **Generate new token (classic)**
   - Name it `op3nsrc-course`, expiry 90 days, **no scopes ticked**
   - Copy the token (shown only once)
4. Save it locally:
   ```bash
   touch .env
   ```
   Put this in `.env` (with your real token):
   ```
   GITHUB_TOKEN=ghp_your_token_here
   ```

> The token stays on your machine. Don't paste it into any script you might end up sharing, and don't send it in chat.

---

## 2. The scripts are already written

All collection scripts live in the `data_collection/` folder:

```text
data_collection/
├── main.py                     # runs everything in one go (or a single step)
├── github_client.py            # shared API client (reads the token from .env)
├── find_repos.py               # search a single query for candidate repos
├── collect_repos.py            # repo info + README + languages + topics
└── collect_issues_and_prs.py   # issues + pull requests (last 3 months, filtered)
```

No one needs to write any code. Just use these as-is.

---

## 3. The repo list (already decided)

`data/repo_list.csv` was **hand-picked by the team members** — we agreed on the final list of repos together, so there's nothing to generate. Collection uses exactly this file as-is.

If you ever want to double-check a candidate during a team discussion, you can search with:

```bash
python3 data_collection/find_repos.py "language:python stars:>5000"
```

Change the query to whatever fits (e.g. `fastapi`, `django`, `react`, `go`). This is just for reference — it does not change what gets collected.

Each row in `data/repo_list.csv` is one repo. Any edits you make to this file (adding/removing rows) directly change what `main.py` collects.
   ```csv
   owner,repo,full_name
   fastapi,fastapi,fastapi/fastapi
   pydantic,pydantic,pydantic/pydantic
   pandas-dev,pandas,pandas-dev/pandas
   ```

`main.py` reads from this one file, so everyone pulls the same repos.

> **Note:** run `main.py` once over the whole list — it collects every repo in `repo_list.csv`.

---

## 4. Run the collection

The normal way — one command runs everything in order (repo metadata, then issues + PRs), and checks that `.env` and `repo_list.csv` exist first:

```bash
python3 data_collection/main.py
```

You can also run just one part:

```bash
python3 data_collection/main.py --step repos          # only repo metadata
python3 data_collection/main.py --step issues_and_prs # only issues + PRs
```

Or run the two scripts directly:

```bash
python3 data_collection/collect_repos.py
python3 data_collection/collect_issues_and_prs.py
```

- `collect_repos.py` saves repo info, README, languages and topics.
- `collect_issues_and_prs.py` saves issues + pull requests created in the **last 3 months** (the 3-month window is set in `SINCE` at the top of the script).
- The API returns 100 records per page, so the scripts page through until there's nothing left (PR paging stops as soon as it reaches PRs older than `SINCE`).
- **Resuming:** finished repos are recorded in `data/raw/issues_prs_done.txt`, so if the run stops (rate limit, laptop closed, Ctrl+C) just run the same command again and it continues with the remaining repos. Delete a line from that file to re-collect that repo.
- **Broken READMEs:** `python3 data_collection/main.py --step readmes` re-fetches only READMEs that are missing or were saved as a "404: Not Found" page.

Note on the issues endpoint: it returns PRs mixed in with issues. A record where `"pull_request"` is not null is actually a PR — that's expected, we filter it during cleaning in Week 2.

The issues + PRs step is the slow one (big repos have thousands of issues), expect **10–30 minutes for the full repo list** (202 repos as of now). Getting rate-limited is fine — just wait a bit and rerun; it overwrites the same files.

---

## 5. Check your work

`data/` should end up like this:

```text
op3nsrc/
├── .env
├── data/
│   ├── repo_list.csv
│   └── raw/
│       ├── repos/     # e.g. fastapi__fastapi.json, ...__languages.json, ...__topics.json
│       ├── readmes/   # e.g. fastapi__fastapi.md
│       ├── issues/    # e.g. fastapi__fastapi__page1.json ... pageN.json
│       └── pulls/     # same pattern
└── data_collection/
    ├── main.py
    ├── github_client.py
    ├── find_repos.py
    ├── collect_repos.py
    └── collect_issues_and_prs.py
```

Verify:

```bash
ls data/raw/issues | wc -l
ls data/raw/pulls | wc -l
ls data/raw/repos | wc -l
```

- Repo files match `repo_list.csv`.
- Pages are present for the bigger repos.
- Open one issue file — you should see `title` and `body`.

A repo with genuinely no issues is fine; a repo with zero issue files otherwise means the script stopped early.

---

## 6. Common problems

| Problem                         | Why                     | Fix                                                                   |
| ------------------------------- | ----------------------- | --------------------------------------------------------------------- |
| `401 Unauthorized`              | Wrong/missing token     | Check `.env`, rerun                                                   |
| `403 API rate limit exceeded`   | Out of hourly quota     | Wait for reset; use `per_page=100`; everyone collects different repos |
| `404 Not Found`                 | Repo name doesn't exist | Check spelling in `repo_list.csv` (case matters)                      |
| 403 with "secondary rate limit" | Requests too fast       | Increase `time.sleep(0.1)` to `0.5`, rerun                            |

---

## 7. Definition of Done

- [ ] You have a working token and `python3 data_collection/main.py --help` runs on your machine.
- [ ] You collected **all of `repo_list.csv`** (via `main.py`).
- [ ] `data/raw/{repos,readmes,issues,pulls}` are populated on your machine.

Once done, we combine everything and start Week 2 (text cleaning + tables) — the plan is in `data-collection-and-processing.md`.
