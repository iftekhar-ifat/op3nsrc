# op3nsrc

**Personalized open-source contribution recommendations.** Enter a GitHub username and Op3nSrc recommends the **open-source projects that fit your skills**, plus **open issues inside each project** to start with. A text classifier (TF-IDF + Naive Bayes) picks the repos; text similarity picks the issues.

> **1. vitejs/vite** — *Why:* vite, frontend, tooling
> • #23179 Stale refresh when editing script in html file … 
> • #23472 fix: image-set() URL rewrite truncates on nested parentheses

**New here? Read [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md)** — the whole project end to end; [`NOTES.md`](NOTES.md) explains each part in detail and why. [`overall-idea.md`](overall-idea.md) has the motivation and plan, [Status](#status) below the progress.

## Pipeline

```text
data/repo_list.csv (202 hand-picked repos)
        ↓  data_collection/main.py      (GitHub API → data/raw/, needs a token)
raw JSON: repos, READMEs, issues, merged PRs
        ↓  data_collection/clean.py     (offline → data/cleaned/)
cleaned tables (CSV)
        ↓  notebooks/eda.ipynb             (explore)
        ↓  notebooks/classification.ipynb  (train + test: developer text → repo)
        ↓  notebooks/recommender.ipynb     (GitHub user → top 5 repos → top 3 issues each)
recommendations → web app (Week 4)
```

## Quick start

Create the virtual environment (Python 3.10+, one-time):

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
python -m ipykernel install --user --name op3nsrc --display-name "Python (op3nsrc)"
```

`requirements.txt` lists the direct dependencies; `requirements-lock.txt` pins the exact versions that were tested (`pip install -r requirements-lock.txt` to reproduce exactly). Activate the environment (`source .venv/bin/activate`) in every new terminal; in Jupyter/VS Code pick the **Python (op3nsrc)** kernel.

Then set up the GitHub token (only needed for collection):

```bash
cp .env.example .env            # then put your GitHub token in .env
```

```bash
python3 data_collection/main.py       # 1. collect raw data (resumable, ~30 min)
```

```bash
python3 data_collection/clean.py      # 2. build the cleaned tables (~10 s, offline)
```

Details: [`data_collection/README.md`](data_collection/README.md).

## Dataset

`data/` is **not in git** (except `data/repo_list.csv`). Either rebuild it with the two commands above or download the shared copy:

Collected dataset (local-only, uploaded externally):
https://helsinkifi-my.sharepoint.com/:f:/g/personal/hongphan_ad_helsinki_fi/IgAv-VOvACUnQIBf-XSJrNbBAY5JkBTlGM-UinaqJdqfDx8?e=mWsG7X

> ⚠️ The shared copy predates the 2026-10-01 re-collection (it is missing issues/PRs for about half the repos). Re-upload `data/raw/` + `data/cleaned/` and update this note.

Current dataset (collection window: issues/PRs active since 2026-06-24):

| Table (`data/cleaned/`)     | Rows   | What it is                                                              |
| --------------------------- | ------ | ----------------------------------------------------------------------- |
| `repositories.csv`          | 202    | Repo description, cleaned README, topics, languages, stars              |
| `issues.csv`                | 15,053 | Issues; `final_text` is the NLP input (7,453 open, 210 beginner-friendly) |
| `pull_requests.csv`         | 4,003  | Merged PRs that reference an issue (1,821 close an issue in our data)   |

Load with `pd.read_csv(path, keep_default_na=False)`; list columns are JSON strings (`json.loads`). All columns: [`data_collection/README.md`](data_collection/README.md#output-tables-datacleaned).

17 repos from the original 219 were dropped: 12 have GitHub Issues disabled (django, postgres, git, mongo, kafka, flink, zookeeper, hibernate-orm, ruby, FFmpeg, emacs, calibre) and 5 are archived/inactive (minio, vue, zig, jinja, httpx).

## Repository layout

```text
op3nsrc/
├── README.md
├── PROJECT_OVERVIEW.md                  # start here: the whole project end to end
├── NOTES.md                             # details: profiles, leakage, split, metrics, "Why", decision log
├── overall-idea.md                      # project idea, motivation, timeline
├── notebooks/                           # run things + show results (implementation is in recommender/)
│   ├── eda.ipynb                        # exploratory analysis + key findings
│   ├── classification.ipynb             # dataset, train/test split, model comparison, test metrics
│   └── recommender.ipynb                # demo: GitHub user → top 5 repos → top 3 issues each
├── recommender/                         # implementation used by the notebooks
│   ├── data.py                          # load cleaned tables, build repo/issue texts
│   ├── classification.py                # dataset (developer text → repo), split, metrics
│   ├── models.py                        # standard classifiers + TF-IDF text matcher
│   ├── github_profile.py                # GitHub user data → profile text
│   └── recommend.py                     # Recommender: user → repos → issues, with "Why"
├── dummy_users/                         # fictional users in GitHub API format (input until live fetch)
├── results/                             # test metrics per model (CSV)
├── .env.example                         # copy to .env and add your token
├── requirements.txt                     # direct dependencies
├── requirements-lock.txt                # exact tested versions
├── data/
│   ├── repo_list.csv                    # the 202 repos (tracked in git)
│   ├── raw/                             # raw API JSON (not in git)
│   └── cleaned/                         # cleaned tables (not in git)
└── data_collection/
    ├── main.py                          # run collection (all steps or --step)
    ├── github_client.py                 # shared API client (token, retries, rate limits)
    ├── collect_repos.py                 # repo info, README, languages, topics
    ├── collect_issues_and_prs.py        # issues + merged PRs (last 3 months)
    ├── clean.py                         # raw JSON → cleaned tables
    └── README.md                        # running the collection, cleaning rules, table columns
```

## Status

- [x] Week 1 — data collection (202 repos)
- [x] Week 2 — cleaning + tables
- [x] Week 2 — EDA (`notebooks/eda.ipynb`)
- [x] Week 3 — repo classifier: TF-IDF + Naive Bayes, test accuracy 75%, top-5 accuracy 88% vs 2% / 6% baseline (`notebooks/classification.ipynb`)
- [x] Week 3 — recommender demo: GitHub user → repos + issues (`notebooks/recommender.ipynb`, dummy users)
- [ ] Week 4 — web page
- [ ] Week 4 — web app
- [ ] Week 5 — fairness, privacy, final report
