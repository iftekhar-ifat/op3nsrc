# Op3nSrc: Week 1 Task — Data Collection

**Goal for this week:** download 100–200 repositories plus their issues and pull requests, and save everything as raw JSON under `data/raw/`.

Everyone works on their **own machine**. Nothing is pushed or shared anywhere. Once everyone has collected their part, we get together and combine it in a discussion.

---

## 0. What data are we grabbing?

For each repo:

1. Repo info — description, topics, stars, etc.
2. README — the raw text file
3. Issues created in the last 2 years — title + body are the text the NLP model matches on
4. Pull requests in the last 2 years — tells us which developer fixed which issue

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

## 2. Copy this into `github_client.py`

```python
import os

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
BASE = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}


def get(path, params=None):
    url = f"{BASE}{path}"
    resp = requests.get(url, headers=HEADERS, params=params)

    if resp.status_code in (403, 429):
        raise SystemExit(
            "Rate limit hit. Wait for the reset, or ask who has quota left."
        )
    resp.raise_for_status()
    return resp.json()
```

Every other script uses `get()` from this file. No one needs to touch the URL/headers logic again.

---

## 3. Pick the repos (human decision, do this first)

Everything depends on this list, so agree on it before collecting.

1. Find candidates with the search API:

   ```python
   # find_repos.py
   from github_client import get

   data = get("/search/repositories", {
       "q": "language:python stars:>5000",
       "sort": "stars",
       "order": "desc",
       "per_page": 50,
   })
   for repo in data["items"]:
       print(repo["full_name"], repo["description"])
   ```

   Change the query as needed (e.g. `fastapi`, `django`, `pandas`, `langchain`).

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

The collector scripts read from this one file, so everyone pulls the same repos.

> **Splitting the work:** each of you takes a chunk of this list (e.g. 30–40 repos each). You collect your chunk on your machine; we combine everything in the discussion afterwards. No one should collect the full 100–200 alone — you'll burn through the API quota.

---

## 4. Run the collectors

### `collect_repos.py` — repo info, README, languages, topics

```python
# collect_repos.py
import csv
import json
import os

import requests

from github_client import get

RAW = "data/raw/repos"
os.makedirs(RAW, exist_ok=True)
os.makedirs("data/raw/readmes", exist_ok=True)

with open("data/repo_list.csv") as f:
    repos = list(csv.DictReader(f))

for one in repos:
    full = one["full_name"]
    stem = full.replace("/", "__")

    info = get(f"/repos/{full}")
    with open(f"{RAW}/{stem}.json", "w") as f:
        json.dump(info, f, indent=2)

    readme = requests.get(f"https://raw.githubusercontent.com/{full}/HEAD/README.md")
    with open(f"data/raw/readmes/{stem}.md", "w") as f:
        f.write(readme.text)

    langs = get(f"/repos/{full}/languages")
    topics = get(f"/repos/{full}/topics", {"Accept": "application/vnd.github.mercy-preview+json"})
    with open(f"{RAW}/{stem}__languages.json", "w") as f: json.dump(langs, f)
    with open(f"{RAW}/{stem}__topics.json", "w") as f:  json.dump(topics, f)

    print("done:", full)
```

### `collect_issues_and_prs.py` — issues + pull requests (the bulk)

The API gives 100 records per page, so we page through until empty.

```python
# collect_issues_and_prs.py
import csv
import json
import os
import time

from github_client import get

os.makedirs("data/raw/issues", exist_ok=True)
os.makedirs("data/raw/pulls", exist_ok=True)

SINCE = "2024-09-01T00:00:00Z"   # 2-year window

with open("data/repo_list.csv") as f:
    repos = list(csv.DictReader(f))

for one in repos:
    full = one["full_name"]
    stem = full.replace("/", "__")

    page = 1
    while True:
        items = get(f"/repos/{full}/issues", {
            "state": "all",
            "per_page": 100,
            "page": page,
            "since": SINCE,
        })
        if not items:
            break
        with open(f"data/raw/issues/{stem}__page{page}.json", "w") as f:
            json.dump(items, f)
        page += 1
        time.sleep(0.1)

    page = 1
    while True:
        items = get(f"/repos/{full}/pulls", {
            "state": "all",
            "per_page": 100,
            "page": page,
            "sort": "created",
            "direction": "desc",
        })
        if not items:
            break
        with open(f"data/raw/pulls/{stem}__page{page}.json", "w") as f:
            json.dump(items, f)
        page += 1
        time.sleep(0.1)

    print("done:", full)
```

Note on the issues endpoint: it returns PRs mixed in with issues. A record where `"pull_request"` is not null is actually a PR — that's expected, we filter it during cleaning in Week 2.

Run:

```bash
python3 collect_repos.py
python3 collect_issues_and_prs.py
```

The second script is slow (big repos have thousands of issues), expect ~10–15 minutes for 150 repos. Getting rate-limited is fine — just wait a bit and rerun; it overwrites the same files.

---

## 5. Check your work

`data/` should end up like this:

```text
op3nsrc/
├── .env
├── github_client.py
├── find_repos.py
├── collect_repos.py
├── collect_issues_and_prs.py
└── data/
    ├── repo_list.csv
    └── raw/
        ├── repos/     # e.g. fastapi__fastapi.json, ...__languages.json, ...__topics.json
        ├── readmes/   # e.g. fastapi__fastapi.md
        ├── issues/    # e.g. fastapi__fastapi__page1.json ... pageN.json
        └── pulls/     # same pattern
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

- [ ] You have a working token and `github_client.py` runs on your machine.
- [ ] You collected **your assigned chunk** of `repo_list.csv`.
- [ ] `data/raw/{repos,readmes,issues,pulls}` are populated on your machine.

Once everyone is done, we combine everything and start Week 2 (text cleaning + tables) — the plan is in `data-collection-and-processing.md`.
