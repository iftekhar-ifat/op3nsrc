# Op3nSrc — Project Overview

A complete walkthrough of the project as it stands: what it does, how the data was collected and cleaned,
how developer profiles are built, how the model works, and what everyone on the team should know.
For the motivation see `overall-idea.md`; for model details see `nlp-recommendation.md`; for **how each part
works in detail, why, and the decision log** see `NOTES.md`.

---

## 1. What Op3nSrc does

> **You enter a GitHub username → Op3nSrc recommends 5 open-source projects that fit your skills, and
> 3 open issues inside each project you could start with, with a short "Why" for every match.**

```text
Recommendations for demo-jordan-web  (languages: css, javascript, html, typescript; merged PRs: 0)

1. vitejs/vite
   Why: vite, vitejs, frontend, tooling, generation
   Issues to start with:
     • #23179 Stale refresh when editing script in html file with bundledDev
     • #23472 fix: image-set() URL rewrite truncates on nested parentheses
     • #23393 Provide a way to run `transformIndexHtml` hooks of a per-environment p…
2. grafana/grafana
   …
```

It is a **data science course project** (5 weeks). The goal is a working, well-explained pipeline with
standard methods, not a production system.

---

## 2. The pipeline at a glance

```text
 data/repo_list.csv  (202 hand-picked repos)
        │
        ▼  1. COLLECT   data_collection/main.py         GitHub API, needs a token, ~30 min
 data/raw/           repo info, READMEs, issues, merged PRs (raw JSON)
        │
        ▼  2. CLEAN     data_collection/clean.py        offline, ~10 s
 data/cleaned/       repositories · issues · pull_requests · developer_profiles (CSV)
        │
        ├─▶ 3. EXPLORE   notebooks/eda.ipynb             charts + findings
        │
        ├─▶ 4. TRAIN     notebooks/classification.ipynb  developer text → repo (train/test split)
        │
        └─▶ 5. RECOMMEND notebooks/recommender.ipynb     GitHub user → top 5 repos → top 3 issues
                         (input: dummy_users/*.json until the live GitHub fetch exists)
```

The **notebooks only call functions**; the implementation lives in `recommender/*.py`
(modeling) and `data_collection/*.py` (collection + cleaning).

---

## 3. Data collection

### 3.1 Which repos

- The team hand-picked **219** popular, active repos across Python, JavaScript/TypeScript, Go, Rust,
  Java, C# and a few others (`data/repo_list.csv`).
- After collection, **17 were dropped**, leaving **202**:
  - 12 have **GitHub Issues disabled** (they use Jira, Trac or mailing lists): django, postgres, git,
    mongo, kafka, flink, zookeeper, hibernate-orm, ruby, FFmpeg, emacs, calibre.
  - 5 are **archived or inactive**: minio (archived), vue (last push 2024), zig (moved to Codeberg),
    jinja, httpx.

### 3.2 What we fetched (GitHub REST API)

| Data          | API call                                                      | Kept                                               |
| ------------- | ------------------------------------------------------------- | -------------------------------------------------- |
| Repo info     | `GET /repos/{owner}/{repo}`                                   | description, stars, forks, language, archived, …   |
| Languages     | `GET /repos/{owner}/{repo}/languages`                         | bytes of code per language                         |
| Topics        | `GET /repos/{owner}/{repo}/topics`                            | topic tags                                         |
| README        | `GET /repos/{owner}/{repo}/readme`                            | raw README text (any file name; symlinks followed) |
| Issues        | `GET /repos/{owner}/{repo}/issues?state=all&since=2026-06-24` | up to **100 per repo**                             |
| Pull requests | `GET /repos/{owner}/{repo}/pulls?state=all`                   | up to **50 per repo**                              |

**Filters applied while collecting:**

- **Issues:** active since **2026-06-24** (≈ 3 months). GitHub's `since` means _updated_ since, so 24% of
  issues were created earlier but had recent activity (`created_in_window = False`). PRs that the issues
  endpoint mixes in, bot authors, and near-empty issues are dropped.
- **PRs:** only **merged**, non-bot PRs created since 2026-06-24 whose text references an issue
  (`Fixes / Closes / Resolves / Refs #N`). These tell us _who works on which repo_.
- Caps (100 issues / 50 PRs per repo) stop a few huge repos from dominating.

**Snapshot date:** collected **2026-09-30 → 2026-10-01**. We do not re-check issues live.

### 3.3 How the collector works

- `python3 data_collection/main.py` runs all steps; `--step repos | issues_and_prs | readmes` runs one.
- **Resumable:** finished repos are listed in `data/raw/issues_prs_done.txt`; re-running skips them.
- Waits automatically on rate limits; a 404 on one repo skips that repo instead of stopping the run;
  repos with Issues/PRs disabled skip that request.
- Needs a personal GitHub token in `.env` (`GITHUB_TOKEN=…`, no scopes). Never commit it.

Raw layout: `data/raw/{repos,readmes,issues,pulls}/<owner>__<repo>…json` — `/` becomes `__` in file names.

---

## 4. Data cleaning (`data_collection/clean.py`)

Runs offline in ~10 s and never modifies `data/raw/`. Steps:

1. **Deduplicate** issues and PRs by repo + number (pages can overlap while new items arrive).
2. **Remove bots**: GitHub `type: Bot` accounts (e.g. the Copilot agent), logins ending in `bot`/`robot`,
   and CI reporters registered as users (`cockroach-teamcity`, `elasticsearchmachine`, `GordonTheTurtle`).
   About 280 issues and 125 PRs were removed this way.
3. **Clean text**: remove issue-template comments and checklists, code blocks (including unclosed ones),
   inline code, images, HTML, URLs and markdown syntax; lowercase. Issue `final_text` = title + body
   (title alone if the body is empty). No stemming.
4. **Normalize labels** (lowercase, emoji removed) and flag **beginner-friendly** / **help wanted** issues,
   catching variants such as `e-easy`, `good-first-issue`, `first-contribution`, `status: help wanted`.
5. **Link PRs to issues** with GitHub's closing keywords (`close/closes/closed`, `fix/fixes/fixed`,
   `resolve/resolves/resolved`) in `#N`, `owner/repo#N` or full-URL form. `refs #N` counts as a
   reference only.
6. **IDs:** `repo_id = "owner/repo"` (as in `repo_list.csv`; 17 repos were renamed on GitHub, the new
   name is in `current_full_name`), `issue_id = "owner/repo#123"`, `pr_id = "owner/repo!456"`,
   `developer_id = GitHub login`.

**Output — `data/cleaned/`:**

| Table                    | Rows   | Contents                                                                             |
| ------------------------ | ------ | ------------------------------------------------------------------------------------ |
| `repositories.csv`       | 202    | description, cleaned README, topics, language shares, stars, forks                   |
| `issues.csv`             | 15,053 | `final_text`, labels, beginner / help-wanted flags, state (7,453 open), links to PRs |
| `pull_requests.csv`      | 4,003  | author, title/body, merge date, issues it closes                                     |
| `developer_profiles.csv` | 1,843  | per PR author: languages, topics, PR/issue titles, `experience_text`                 |

Load with `pd.read_csv(path, keep_default_na=False)` (keeps empty text as `""`); list columns are JSON
strings (`json.loads`). Running `clean.py` twice gives byte-identical files.

---

## 5. What the data looks like (EDA, `notebooks/eda.ipynb`)

- **Languages:** Python 54 repos, Go 37, Rust 31, TypeScript 24, JavaScript 16 — 80% of the repos.
  Java / C# / C++ have few repos → recommendations are weaker for those developers.
- **Issues:** median 150 words; 101 repos hit the 100-issue cap; 27% have no label.
- **Beginner labels are rare:** only 2.6% of issues (397) are beginner-friendly or help wanted, mostly in
  projects that label actively.
- **Developers:** 1,843 PR authors; **68% have exactly one merged PR**, and only 6.9% contributed to more
  than one repo.
- **Classes for the classifier:** 117 repos have at least 5 developers (1,724 developers).
- The most common issue words are template headings ("expected behavior", "steps to reproduce") — TF-IDF's
  `max_df` filters them out.

---

## 6. Developer profiles — three kinds, for three purposes

| Profile                                                      | Built from                                                                                                                                                                                                 | Used for                            |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| **EDA summary** (`developer_profiles.csv`)                   | all merged PRs of a PR author: languages and topics of the repos they contributed to, PR titles, issue titles → `experience_text`                                                                          | describing developers in EDA        |
| **Training text** (built in `recommender/classification.py`) | the developer's merged-PR titles + descriptions (up to 2,000 chars each, **repo PR-template sentences removed**) + titles of issues they opened. **Owner names and `owner/repo` strings are removed** so the text does not contain the answer. Label = the repo they merged most PRs into | training and testing the classifier |
| **App profile** (`recommender/github_profile.py`)            | the user's GitHub data: bio, **own repos (forks skipped)** — name, description, topics, language — top 5 languages by bytes of code, merged-PR titles/bodies, opened-issue titles, starred repos           | recommending for a new user         |

Why the app profile is different: a new user — especially a beginner — may have no merged PRs at all, so
we also use their own repos and starred projects. The training data only has PR text and issue titles. This difference is a
known limitation (§10).

**Dummy users** (`dummy_users/*.json`): three fictional users with exactly the structure of the GitHub API
responses, so the live fetch can replace them without other changes:

| User              | Profile                                     | Tests                              |
| ----------------- | ------------------------------------------- | ---------------------------------- |
| `demo-alex-py`    | Python backend (FastAPI, pydantic)          | a forked repo that must be ignored |
| `demo-sam-rust`   | Rust / Go systems (tokio, clap, Kubernetes) | a different ecosystem              |
| `demo-jordan-web` | beginner frontend, **no merged PRs**        | the newcomer case                  |

---

## 7. The model — repo classification (`notebooks/classification.ipynb`)

**Question:** given a developer's text, which repo do they contribute to?

|              |                                                                                              |
| ------------ | -------------------------------------------------------------------------------------------- |
| Rows         | 1,724 developers (one each)                                                                  |
| Classes      | 117 repos (5–39 developers each, median 13)                                                  |
| Split        | stratified random **80/20** → 1,379 train / 345 test                                         |
| Features     | TF-IDF of words + word pairs, plus character 3–5-grams                                       |
| Settings     | small grids tuned with 4-fold cross-validation on the training set, chosen by top-5 accuracy |
| Metrics      | accuracy, **top-5 accuracy** (true repo among the 5 we would recommend), macro / weighted F1 |

**Models** (all standard scikit-learn pipelines, `recommender/models.py`):

| Model                                                        | Test accuracy | Test top-5 accuracy |
| ------------------------------------------------------------ | ------------- | ------------------- |
| Most frequent repo (baseline)                                | 2%            | 6%                  |
| **TF-IDF + Naive Bayes** ← chosen (best in cross-validation) | 75%           | **88%**             |
| TF-IDF + Logistic Regression                                 | 69%           | 84%                 |
| Sentence-BERT + Logistic Regression                          | 41%           | 67%                 |

- **TF-IDF** gives every word a weight: rare, specific words (`tokio`, `pydantic`, `webcontents`) count
  much more than common ones (`bug`, `error`).
- **Naive Bayes / Logistic Regression** learn which words point to which repo.
- **Sentence-BERT** turns text into a "meaning" vector; it did worse here because exact project and library
  names matter more than general meaning.
- **How we got here:** the first version (PR text cut at 500 chars, single words, default settings) scored
  51% / 73%. Using the full PR descriptions + issue titles, adding word pairs and character n-grams, and light
  tuning raised it to 75% / 88%. Repo PR-template sentences are removed so the model can't win by
  recognising templates (details in `NOTES.md` §3).
- The chosen model is **retrained on all 1,724 developers** before it is used in the app.

Results are saved in `results/test_results.csv`.

---

## 8. Making a recommendation (`recommender/recommend.py`, `notebooks/recommender.ipynb`)

```text
username
  → 1. load GitHub data            (dummy_users/<username>.json for now)
  → 2. build the app profile       (§6)
  → 3. classifier → top 5 repos    only repos the classifier knows (117) that have open issues (116)
  → 4. top 3 open issues per repo  TF-IDF cosine similarity to the profile
                                   + 0.05 boost for good first issue / help wanted
  → 5. "Why"                       the words with the biggest share in the TF-IDF match
```

- Repos are shown by **rank**, not probability: Naive Bayes ranks well, but its probability values are not
  meaningful (all close to 1%).
- Repos with **no open issues** in the snapshot are never recommended (e.g. `tiangolo/fastapi` uses
  GitHub Discussions instead of issues).
- Issue titles that are only a template (e.g. "Bug:") are shown with the start of the body.

---

## 9. Things to know

**Running the project**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt                      # requirements-lock.txt = exact tested versions
python -m ipykernel install --user --name op3nsrc --display-name "Python (op3nsrc)"
python data_collection/clean.py                      # only if data/raw/ changed
```

Then open the notebooks with the **Python (op3nsrc)** kernel, in this order: `eda` → `classification` →
`recommender`.

**Data and git**

- `data/` is **not in git** (only `data/repo_list.csv`). Get the data from the team share link in
  `README.md` or rebuild it with `main.py` + `clean.py`. The share link still points to the **old,
  incomplete** collection — re-upload `data/raw/` + `data/cleaned/` and update it.
- `.env` (token) is never committed.

**GitHub access**

- Only the collection scripts call GitHub; everything else runs offline on `data/`.
- Sentence-BERT downloads its pretrained model (~90 MB) from Hugging Face on first use.

**Reproducibility**

- Fixed seeds (`random_state = 42`) for the split and models; `clean.py` is deterministic.
- All numbers in this document come from the 2026-10-01 snapshot.

**Code layout**

| Path                                                          | What                                          |
| ------------------------------------------------------------- | --------------------------------------------- |
| `data_collection/main.py`, `collect_*.py`, `github_client.py` | GitHub collection                             |
| `data_collection/clean.py`                                    | raw JSON → cleaned tables                     |
| `recommender/data.py`                                         | load tables, build repo / issue texts         |
| `recommender/classification.py`                               | classifier dataset, train/test split, metrics |
| `recommender/models.py`                                       | the four classifiers + TF-IDF text matcher    |
| `recommender/github_profile.py`                               | GitHub data → app profile                     |
| `recommender/recommend.py`                                    | user → repos → issues, with "Why"             |
| `notebooks/`                                                  | EDA, classification, recommender demo         |
| `dummy_users/`                                                | fictional users in GitHub API format          |
| `results/`                                                    | saved test metrics                            |

---

## 10. Limitations (for the report)

1. **Training vs app text:** the classifier learns from PR text and issue titles; a new user's profile also includes their own
   repos and starred projects, so live recommendations are looser than the 88% test number.
2. **Limited pool:** only 116 repos can be recommended (≥ 5 developers and open issues), from a fixed
   snapshot.
3. **Issue suggestions are not evaluated** — they are a simple similarity ranking for convenience.
4. **Language bias:** most repos and developers are Python / Go / Rust / JS / TS.
5. **Thin profiles:** most developers have a single merged PR.
6. **Beginner labels are rare and inconsistent** across projects, so the "good first issue" boost helps only
   in some repos.

## 11. What's next

1. **Web page** (e.g. Streamlit): username box → the output of `Recommender.recommend_user`.
2. **Live GitHub fetch:** produce the same JSON keys as `dummy_users/` from the API.
3. **Week 5:** fairness and privacy review, report and presentation.
