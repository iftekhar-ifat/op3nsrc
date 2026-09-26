# Op3nSrc: Data Collection & Processing Guide

This is the practical, step-by-step guide for **Week 1** of the project. It explains what data we collect, how to get it from the GitHub API, how to store it, and how to clean it for the NLP models.

Read this together with:

- **`overall-idea.md`** — what the project is trying to do.
- **`nlp-recommendation.md`** — how the NLP model uses the data.

---

## 1. What data do we need?

We collect **public** data only, in four related groups:

```text
Repositories (only ~200, hand-picked)
        ↓
Issues + Pull Requests (historical and current)
        ↓
Developer profiles (from PR authors)
        ↓
Cleaned text documents (for the NLP model)
```

| Data group         | Why we need it                                                                                     |
| ------------------ | -------------------------------------------------------------------------------------------------- |
| Repositories       | Context of each issue, plus project description/README/topics (developer-side and issue-side text) |
| Issues             | The items we recommend (title + body are NLP inputs)                                               |
| Pull requests      | Historical positive labels (merged PR linked to an issue) and developer experience text            |
| Developer profiles | The developer-side text document used for matching                                                 |

---

## 2. Choose a repository set first

We will **not** collect all of GitHub. We pick a bounded, relevant set:

- **Size:** 218 active repositories (hand-picked, in `data/repo_list.csv`).
- **Domain:** a few focused ecosystems — e.g. Python (web/AI/ML), JavaScript/TypeScript (web), Go, Rust (`fastapi`, `pandas`, `django`, `react`, `langchain`, `go`, ...).
- **Criteria for inclusion:** not archived, has open issues, has a `good first issue` or `help wanted` label somewhere, active in the last 3 months.

### How the repo list was chosen

The repos in `data/repo_list.csv` were **hand-picked by the team members** — we agreed on the final set of projects together, so no scripts or searches are needed to decide them. Collection reads this file as-is.

If a discussion needs a quick reference for a candidate, search manually:

```bash
curl -s "https://api.github.com/search/repositories?q=language:python+stars:>5000&sort=stars&order=desc&per_page=50" -H "Accept: application/vnd.github+json"
```

The list lives in one shared file, `data/repo_list.csv`:

```csv
owner,repo,full_name
fastapi,fastapi,fastapi/fastapi
pydantic,pydantic,pydantic/pydantic
pandas-dev,pandas,pandas-dev/pandas
```

---

## 3. GitHub API setup

Workflow: we are allowed **5,000 requests/hour** with an authenticated token, and only **60/hour** without one. So everyone needs a token.

### Create a token (one-time)

1. GitHub → Settings → Developer settings → **Personal access tokens** → **Tokens (classic)**.
2. Generate a token with **no scopes** (public data only; `public_repo` only if you later need private — we don't).
3. Store it in a local `.env` file. **Never commit it.**

### Set up the API client

Minimal setup so everyone is consistent:

```python
# github_client.py
import os
import requests

TOKEN = os.environ["GITHUB_TOKEN"]
BASE = "https://api.github.com"
HEADERS = {"Authorization": f"Bearer {TOKEN}",
           "Accept": "application/vnd.github+json"}

def get(path, params=None):
    r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params)
    if r.status_code == 403:            # rate-limit hit
        reset = int(r.headers.get("X-RateLimit-Reset", 0))
        raise SystemExit(f"Rate limited, retry after {reset}")
    r.raise_for_status()
    return r.json()
```

**Tips to stay inside the rate limit:**

- Use `per_page=100` (the max) and paginate with the `Link` header.
- Never refetch the same URL; cache responses to disk.
- Sleep ~0.1s between calls; spread work across teammates if needed.

---

## 4. What to fetch and how

### 4.1 Repositories

For each repo in `repo_list.csv`, call:

```
GET /repos/{owner}/{repo}
GET /repos/{owner}/{repo}/readme        (header: Accept: application/vnd.github.raw)
GET /repos/{owner}/{repo}/languages     -> JSON map {language: bytes}
GET /repos/{owner}/{repo}/topics        (header: Accept: application/vnd.github.mercy-preview+json)
```

**Example response** (`GET /repos/fastapi/fastapi` — shortened):

```json
{
  "full_name": "fastapi/fastapi",
  "description": "FastAPI framework, high performance, easy to learn...",
  "topics": ["fastapi", "api", "web", "async"],
  "stargazers_count": 78000,
  "forks_count": 6200,
  "open_issues_count": 410,
  "archived": false,
  "created_at": "2018-12-01T17:41:36Z",
  "updated_at": "2026-09-08T10:12:00Z",
  "language": "Python"
}
```

Store each raw response as one JSON file:

```text
data/raw/repos/fastapi__fastapi.json
data/raw/readmes/fastapi__fastapi.md
```

### 4.2 Issues

For each repo, fetch **both open and closed** issues from a defined time window (e.g. the last 3 months). Issues endpoint returns issues **and** PRs mixed — filter with `type`.

```
GET /repos/{owner}/{repo}/issues?state=all&per_page=100&since=2026-06-24T00:00:00Z
```

**Example response element** (shortened):

```json
{
  "number": 942,
  "title": "Add pagination to endpoint",
  "state": "open",
  "labels": [{ "name": "enhancement" }, { "name": "good first issue" }],
  "created_at": "2026-05-02T09:00:00Z",
  "closed_at": null,
  "comments": 6,
  "body": "### Context\nUsers can't navigate large lists. Need `limit` and `offset`...",
  "user": { "login": "octocat", "id": 1 },
  "pull_request": null
}
```

Note:

- If `pull_request` is present, it is **not an issue** — skip it (or store separately as a PR).
- Store raw: `data/raw/issues/fastapi__fastapi_page1.json`, etc.

### 4.3 Issue comments (optional but useful)

Comments add developer context. Fetch for issues that will become training/recommendation candidates:

```
GET /repos/{owner}/{repo}/issues/{number}/comments
```

### 4.4 Pull requests

For each repo, fetch PRs in the same time window:

```
GET /repos/{owner}/{repo}/pulls?state=all&per_page=100&sort=created&direction=desc
```

**Example response element** (shortened):

```json
{
  "number": 119,
  "title": "Implement endpoint pagination",
  "state": "closed",
  "user": { "login": "scientist_99", "id": 456 },
  "created_at": "2026-05-10T14:00:00Z",
  "merged_at": "2026-05-15T08:00:00Z",
  "body": "Adds `limit`/`offset` query params... Fixes #942",
  "commits": 4,
  "changed_files": 5,
  "additions": 120,
  "deletions": 30
}
```

Extra calls you may need (they cost API quota, so do them only for collected PRs):

```
GET /repos/{owner}/{repo}/pulls/{number}/files     -> changed file paths
GET /repos/{owner}/{repo}/pulls/{number}/commits   -> commit messages
```

### 4.5 Link PRs to issues (important for labels)

We need to know which PR "solved" which issue. Two ways:

1. **From PR text:** look for `Fixes #942`, `Closes #942`, `Resolves #942` in the PR body; a PR can link multiple issues.
2. **From PR details:** `GET /repos/{owner}/{repo}/pulls/{number}` returns `"body"` and the API sometimes exposes `"head"`/`"base"` only — so the regex on the body is the reliable way.

**Example extraction rule:**

```python
import re
LINK = re.compile(r"(?:fixes|closes|resolves|refs)\s+#(\d+)", re.IGNORECASE)
```

```python
links = [int(m) for m in LINK.findall(pr["body"])]       # e.g. [942]
```

A **merged** PR that links issue `#942` gives us a positive label: `(developer, issue_942, merged=True)`.

---

## 5. Storage layout (keep it simple and reproducible)

```text
data/
├── raw/                      # untouched API responses
│   ├── repos/
│   ├── readmes/
│   ├── issues/               # one JSON file per page (per repo)
│   ├── pulls/
│   └── comments/
├── cleaned/                  # processed tables (CSV/Parquet)
│   ├── repositories.csv
│   ├── issues.csv
│   ├── pull_requests.csv
│   ├── developer_profiles.csv
│   └── developer_issue_pairs.csv
└── repo_list.csv             # hand-picked repo list
```

| Store             | Format                        | Why                                           |
| ----------------- | ----------------------------- | --------------------------------------------- |
| Raw API responses | JSON                          | Do not lose information; full reproducibility |
| Cleaned tables    | CSV (small) / Parquet (large) | Easy to load with pandas                      |
| Final text docs   | JSONL/CSV                     | Input prepared for the NLP models             |

**Golden rule:** never edit `raw/`. Any fix happens in the cleaning code, so the pipeline can be re-run.

---

## 6. Cleaning the data

Run everything as scripts so results are reproducible (`data_collection/clean.py`).

### 6.1 Clean the metadata (structured fields)

1. **Deduplicate** repos/issues/PRs by GitHub number + repo.
2. **Drop:** archived repos, bots (identify via `user.login` containing `[bot]` or known bot lists), deleted records.
3. **Normalize:** lowercase language names, labels, topics (`"Good First Issue"` → `"good first issue"`).
4. **Parse timestamps** to `datetime`, keep a numeric column such as `days_since_creation`.
5. **Keep both** `language` names and their byte counts from the `/languages` call.
6. **Validate:** an issue that links a PR must have the PR exist in our data; otherwise mark `link_verified=False`.

### 6.2 Clean the text (for NLP)

````python
import re

MD = re.compile(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)")
CODE = re.compile(r"```.*?```|`[^`]+`", re.DOTALL)
URL = re.compile(r"https?://\S+|www\.\S+")

def clean_text(raw):
    t = raw or ""
    t = MD.sub(" ", t)          # strip HTML + markdown images
    t = CODE.sub(" ", t)        # strip code blocks / inline code
    t = URL.sub(" ", t)         # strip URLs
    t = t.lower()
    t = " ".join(t.split())     # collapse whitespace (keeps basic punctuation)
    return t.strip()
````

**Example — before / after:**

| Before                                                                                                   | After                                                                       |
| -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| ``"### Context\nUsers can't navigate large lists. See `docs` at https://x.com. Need `limit`/`offset`."`` | `"context users can't navigate large lists see docs at need limit/offset."` |

Notes:

- Keep it **light** — do not aggressively stem/stopword for the embedding model; that's only useful for the TF-IDF baseline.
- For very short/empty issue bodies, fall back to the title: `final_text = clean(body) or clean(title)`.

---

## 7. Building the tables

### 7.1 `repositories.csv`

One row per repo (subset shown):

```csv
repository_id,full_name,description_clean,readme_clean,topics,primary_language,stars,forks,open_issues,is_archived,created_at,updated_at
repo_001,fastapi/fastapi,"fastapi framework high performance easy to learn",<long cleaned readme text>,"[fastapi, api, web]","Python",78000,6200,410,false,2018-12-01,2026-09-08
```

### 7.2 `issues.csv`

One row per issue (subset shown):

```csv
issue_id,repo_id,number,title,body_clean,final_text,labels,state,created_at,closed_at,comment_count,author_login,linked_pr_numbers,is_pull_request
issue_942,repo_001,942,"Add pagination to endpoint","context users can't navigate large lists see docs need limit offset","context users can't navigate large lists see docs need limit offset","[enhancement, good first issue]",open,2026-05-02,,6,scientist_99,"119",false
```

### 7.3 `pull_requests.csv`

One row per PR (subset shown):

```csv
pr_id,repo_id,number,title,body_clean,author_login,state,merged,created_at,merged_at,commits,changed_files,additions,deletions,linked_issue_ids
pr_119,repo_001,119,"Implement endpoint pagination","adds limit offset query params fixes 942",scientist_99,closed,true,2026-05-10,2026-05-15,4,5,120,30,"[issue_942]"
```

### 7.4 `developer_profiles.csv`

One row per developer. The `experience_text` is the **developer-side document** for the NLP model:

```csv
developer_id,login,languages,topics,featured_repo_descs,pr_titles,issue_titles,experience_text,merged_pr_count,contrib_count,first_contribution_at
dev_001,scientist_99,"[Python, JavaScript]","[api, ml]",...,"| implement endpoint pagination | update docs ...","| add pagination to endpoint | ...","python javascript api ml implement endpoint pagination ...",7,18,2024-03-12
```

`experience_text` is assembled from cleaned strings, joined with `|` or newlines, e.g.:

```text
python | javascript | api | machine-learning |
implement endpoint pagination | update docs for pagination |
add pagination to endpoint
```

### 7.5 `developer_issue_pairs.csv` — the training/recommendation input

One row per developer–issue pair. **Positive label = merged PR linking that issue.**

```csv
developer_id,issue_id,pair_text_score_features...,label,label_source
dev_001,issue_942,...,1,merged_pull_request
dev_001,issue_517,...,0,unobserved_negative
```

Negative examples are sampled issues the developer did **not** contribute to (made available before the issue closed). Treat them as **assumed-negative**, not confirmed refusals.

---

## 8. Checklist before moving on (Week 2 begins)

- [ ] Repo list reviewed and saved (`data/repo_list.csv`, 218 repos).
- [ ] All raw responses collected and stored under `data/raw/`.
- [ ] Dedup, drop archived/bots, normalize labels and languages.
- [ ] Text cleaning applied and `final_text` column exists for every issue.
- [ ] PR-to-issue links extracted and verified.
- [ ] `developer_profiles.csv` built with `experience_text`.
- [ ] Cleaned tables load in pandas with no unexpected missing values.

---

## 9. Team task ideas

| Task                                   | Owner (suggested)          |
| -------------------------------------- | -------------------------- |
| Pick + review the 218-repo list        | 1 person                   |
| Write `data_collection/main.py` + the collection scripts | 1–2 people |
| Run `data_collection/main.py` and cache raw responses to `data/raw/` | whoever runs the scripts |
| Write cleaning + text pipeline         | 1 person                   |
| PR→issue linking + label generation    | 1 person                   |
| EDA notebooks on cleaned tables        | 1 person (Week 2)          |

Everyone should be able to rerun the pipeline locally and get the same 5 tables at the end.
