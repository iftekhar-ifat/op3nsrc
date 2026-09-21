# Op3nSrc: Week 1 Task — Data Collection

**Goal for this week:** download 100–200 repositories plus their issues and pull requests, and save everything as raw JSON under `data/raw/`.

Everyone works on their **own machine**. Nothing is pushed or shared anywhere. Once everyone has collected their part, we get together and combine it in a discussion.

---

## 0. What data are we grabbing?

For each repo:

1. Repo info — description, topics, stars, etc.
2. README — the raw text file
3. Issues created in the last 6 months — title + body are the text the NLP model matches on
4. Pull requests in the last 6 months — tells us which developer fixed which issue

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
├── find_repos.py               # search for candidate repos
├── collect_repos.py            # repo info + README + languages + topics
└── collect_issues_and_prs.py   # issues + pull requests (last 6 months)
```

No one needs to write any code. Just use these as-is.

---

## 3. Pick the repos (human decision, do this first)

Everything depends on this list, so agree on it before collecting.

1. Find candidates with the search API:

   ```bash
   python3 data_collection/find_repos.py "language:python stars:>5000"
   ```

   Or search directly for a term (e.g. `fastapi`, `django`, `pandas`, `langchain`).

2. Keep repos that are:
   - active (updated within the last 6 months)
   - not archived
   - have open issues
   - in 1–2 focused domains (e.g. Python web/API or Python data/ML)

3. Save the agreed list to `data/repo_list.csv`:
   ```csv
   owner,repo,full_name
   fastapi,fastapi,fastapi/fastapi
   pydantic,pydantic,pydantic/pydantic
   pandas-dev,pandas,pandas-dev/pandas
   ```

`main.py` reads from this one file, so everyone pulls the same repos.

> **Splitting the work:** each of you takes a chunk of this list (e.g. 30–40 repos each). You collect your chunk on your machine; we combine everything in the discussion afterwards. No one should collect the full 100–200 alone — you'll burn through the API quota.
> **Note for your chunk:** keep only **your** repos in `repo_list.csv` before running, so you don't collect everything.

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
- `collect_issues_and_prs.py` saves issues + pull requests created in the **last 6 months** (the 6-month window is set in `SINCE` at the top of the script).
- The API returns 100 records per page, so the scripts page through until there's nothing left.

Note on the issues endpoint: it returns PRs mixed in with issues. A record where `"pull_request"` is not null is actually a PR — that's expected, we filter it during cleaning in Week 2.

The issues + PRs step is the slow one (big repos have thousands of issues), expect ~10–15 minutes for 150 repos. Getting rate-limited is fine — just wait a bit and rerun; it overwrites the same files.

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

- Repo files match the repos you were assigned.
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
- [ ] You collected **your assigned chunk** of `repo_list.csv` (via `main.py`).
- [ ] `data/raw/{repos,readmes,issues,pulls}` are populated on your machine.

Once everyone is done, we combine everything and start Week 2 (text cleaning + tables) — the plan is in `data-collection-and-processing.md`.
