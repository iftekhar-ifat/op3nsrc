# op3nsrc

**Personalized open-source contribution recommendations.** Op3nSrc matches a developer's skills (from their GitHub activity) to open GitHub issues they are likely able to solve, using NLP (TF-IDF baseline + Sentence-BERT embeddings).

> **Recommended issue:** Add pagination to a FastAPI endpoint — **Match: 89%**
> *Why:* your activity shows Python, FastAPI and REST APIs, and the issue is labelled `good first issue`.

See [`overall-idea.md`](overall-idea.md) for the motivation and plan, and [Status](#status) below for current progress.

## Pipeline

```text
data/repo_list.csv (202 hand-picked repos)
        ↓  data_collection/main.py      (GitHub API → data/raw/, needs a token)
raw JSON: repos, READMEs, issues, merged PRs
        ↓  data_collection/clean.py     (offline → data/cleaned/)
cleaned tables (CSV)
        ↓  EDA → TF-IDF / Sentence-BERT models → web app   (Weeks 2–5)
ranked issue recommendations
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
| `developer_profiles.csv`    | 1,843  | One row per PR author; `experience_text` is the NLP input               |
| `developer_issue_pairs.csv` | 10,932 | 1,822 positive (developer solved issue) + 9,110 sampled negative pairs  |

Load with `pd.read_csv(path, keep_default_na=False)`; list columns are JSON strings (`json.loads`).

17 repos from the original 219 were dropped: 12 have GitHub Issues disabled (django, postgres, git, mongo, kafka, flink, zookeeper, hibernate-orm, ruby, FFmpeg, emacs, calibre) and 5 are archived/inactive (minio, vue, zig, jinja, httpx).

## Repository layout

```text
op3nsrc/
├── README.md
├── overall-idea.md                      # project idea, motivation, timeline
├── data-collection-task.md              # Week 1 how-to (collection)
├── data-collection-and-processing.md    # data model, cleaning rules, tables
├── nlp-recommendation.md                # model plan (TF-IDF, SBERT, evaluation)
├── notebooks/
│   └── eda.ipynb                        # exploratory analysis + key findings
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
    └── find_repos.py                    # search helper for picking repos
```

## Status

- [x] Week 1 — data collection (202 repos)
- [x] Week 2 — cleaning + tables
- [x] Week 2 — EDA (`notebooks/eda.ipynb`)
- [ ] Weeks 3–4 — TF-IDF baseline, Sentence-BERT model, evaluation (P@K, R@K, NDCG@K, MRR)
- [ ] Week 4 — web app
- [ ] Week 5 — fairness, privacy, final report
