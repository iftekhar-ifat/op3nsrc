# Op3nSrc — Design Notes

The details behind `PROJECT_OVERVIEW.md`: **how** each part works, **why** it works that way, and a log of
the decisions we made along the way. Useful when writing the report or answering questions in the
presentation.

Contents:

- [Op3nSrc — Design Notes](#op3nsrc--design-notes)
  - [1. Who counts as a "developer"](#1-who-counts-as-a-developer)
  - [2. Developer profiles — three kinds](#2-developer-profiles--three-kinds)
    - [2.1 EDA summary — `developer_profiles.csv` (built in `data_collection/clean.py`)](#21-eda-summary--developer_profilescsv-built-in-data_collectioncleanpy)
    - [2.2 Training text (built in `recommender/classification.py`)](#22-training-text-built-in-recommenderclassificationpy)
    - [2.3 App profile for a new user (built in `recommender/github_profile.py`)](#23-app-profile-for-a-new-user-built-in-recommendergithub_profilepy)
    - [Why the three differ, and what that costs](#why-the-three-differ-and-what-that-costs)
  - [3. The classifier dataset and how we avoid giving away the answer](#3-the-classifier-dataset-and-how-we-avoid-giving-away-the-answer)
  - [4. Why a standard random train/test split is valid](#4-why-a-standard-random-traintest-split-is-valid)
  - [5. How the model is chosen and how to read the metrics](#5-how-the-model-is-chosen-and-how-to-read-the-metrics)
  - [6. Why TF-IDF beats Sentence-BERT here](#6-why-tf-idf-beats-sentence-bert-here)
  - [7. How the top 5 repos are chosen](#7-how-the-top-5-repos-are-chosen)
  - [8. How issues are chosen inside a repo](#8-how-issues-are-chosen-inside-a-repo)
  - [9. How the "Why" words are computed](#9-how-the-why-words-are-computed)
  - [10. How bots, beginner labels and PR→issue links are detected](#10-how-bots-beginner-labels-and-prissue-links-are-detected)
  - [11. Gotchas](#11-gotchas)
  - [12. Decision log](#12-decision-log)

---

## 1. Who counts as a "developer"

We never downloaded profiles of the people in our data. A **developer** is any **non-bot author of a merged
PR** in our 202 repos (collected: merged, references an issue, created since 2026-06-24, max 50 per repo).
That gives **1,843 developers**. Everything we know about them comes from:

- the PRs they merged (title, description, repo, merge date),
- the info of the repos those PRs went into (languages, topics, description),
- issues they opened in our data.

Real example — developer `0-wiz-0`, our complete knowledge about them:

| repo      | PR    | title                                                | description    |
| --------- | ----- | ---------------------------------------------------- | -------------- |
| jqlang/jq | #3579 | Fix strftime-related functions on NetBSD             | "closes #3568" |
| jqlang/jq | #3574 | Cast char to unsigned char before passing to isspace | "closes #3569" |

68% of developers look like this or thinner: **exactly one merged PR**.

---

## 2. Developer profiles — three kinds

```text
merged PRs in our 202 repos ──┬─▶ 2.1 EDA summary        PRs + repo languages/topics + issue titles
   (author = developer)       └─▶ 2.2 training text      PR text + issue titles, templates & owner names removed, label = main repo

a new user's own GitHub data ───▶ 2.3 app profile        bio, own repos, languages, PRs, issues, starred
   (dummy users for now)
```

### 2.1 EDA summary — `developer_profiles.csv` (built in `data_collection/clean.py`)

- **Languages / topics:** taken from the _repos the developer contributed to_, weighted by how many PRs they
  made there (language share in the repo × number of PRs; tiny weights dropped; max 8 languages / 15 topics).
- **PR titles** they wrote, **issue titles** they opened, and descriptions of their repos.
- All joined into `experience_text`.

```text
0-wiz-0 → languages: c, m4, shell | topics: jq | repos: jqlang/jq | merged PRs: 2
experience_text: "c m4 shell | jq | command-line json processor | cast char to unsigned char … |
                  fix strftime-related functions on netbsd | jq 1.8.2 self test failure on netbsd | …"
```

**Used only for EDA.** Not used by the model: its languages and topics come _from the label repo itself_,
so a model trained on it would just read the answer off the repo description.

### 2.2 Training text (built in `recommender/classification.py`)

- **Text:** the developer's merged-PR titles + descriptions (up to 2,000 characters each) + titles of issues
  they opened in our data.
- **Removed:** owner names and `owner/repo` strings, each repo's PR-template sentences, and very short
  sentences such as "closes #3568." (see §3).
- **Label:** the repo they merged most PRs into.

```text
0-wiz-0 → text:  "fix strftime-related functions on netbsd. | cast char to unsigned char before passing to isspace. |
                  bug: 2.5.2: error: expected declaration specifiers … | sphinx 9.0.4 breaks build of khard 0.20.0 |
                  ctype(3) functions used unsafely | jq 1.8.2 self test failure on netbsd"
          label: jqlang/jq        (the last four parts are titles of issues they opened)
```

### 2.3 App profile for a new user (built in `recommender/github_profile.py`)

A new user may have **no PRs in our repos at all** (especially beginners), so their profile comes from their
own GitHub account:

| GitHub API response                                 | What goes into the profile                                               |
| --------------------------------------------------- | ------------------------------------------------------------------------ |
| `GET /users/{u}`                                    | bio                                                                      |
| `GET /users/{u}/repos`                              | own repos — **forks skipped** — name, description, topics, main language |
| `GET /repos/{o}/{r}/languages`                      | the user's top 5 languages by bytes of code (non-fork repos)             |
| `GET /search/issues?q=author:{u}+type:pr+is:merged` | PR titles + first 2,000 chars of descriptions + target repo name         |
| `GET /search/issues?q=author:{u}+type:issue`        | issue titles + target repo name                                          |
| `GET /users/{u}/starred`                            | starred repos: name, description, topics, language (interests)           |

Forks are skipped because a fork contains someone else's code, not the user's skills. Until the live fetch
exists, this data comes from `dummy_users/*.json`, which have exactly these API structures.

### Why the three differ, and what that costs

The model is **trained on 2.2** (PR text + issue titles) but **used on 2.3** (mostly repos and starred projects). The texts
look different, so live recommendations are looser than the test score. This is limitation #1 in the report.

---

## 3. The classifier dataset and how we avoid giving away the answer

**One row per developer:** `text` (2.2) → `repo` (label). Only repos with **≥ 5 developers** become classes
(a class needs a few examples to be learnable): **117 repos, 1,724 developers**, 5–39 developers each.

**Leakage = the input already contains the answer.** PR text often names its own repo
("see facebook/react#123", "tiangolo said …"). If we kept that, the model would learn to spot repo names, not
skills. So `build_dataset` removes, from every text:

- every `owner/repo` string of all 202 repos (old and new names, since 17 repos were renamed),
- every **owner name** (`facebook`, `tiangolo`, `pola-rs`, …).

Project and technology words (`react`, `tokio`, `jq`) are **kept**: a real user's profile contains those
too, and they are legitimate skill signals. Check in the notebook: 0 profiles contain their own `owner/repo`.


**PR templates are removed too.** Many repos have a PR template ("Thanks for contributing! Checklist: …").
Those sentences identify the *repo*, not the developer, so the model could win by recognising templates.
`build_dataset` removes every sentence that appears in **3 or more PRs of the same repo** (about 7% of PR
text; 40% of PRs had some). Keeping them would add about 5 points of accuracy — earned the wrong way.
Very short sentences (≤ 15 characters, e.g. "closes #3568.") are dropped as well; they carry no skill signal.

**Features.** The text is turned into TF-IDF of **words + word pairs** and of **character 3–5-grams**.
Character pieces help with code names (`strftime`, `useState`, `webcontents`) and their variants.
---

## 4. Why a standard random train/test split is valid

A random split assumes rows are **independent**. Here each row is a **different developer** who appears
**once**, so nothing about a test developer is in the training data.

- **Stratified:** every repo appears in train and test in the same proportion (80/20).
- `random_state = 42` → the same split every run.

_Why we did not do this at first:_ the earlier design ranked individual **issues** for a developer at a point
in time. There, a random split would leak — the same developer would be in train and test, and a PR and the
issue it fixes share almost the same words. That design needed a time-based split. Reframing the task as
"developer → repo" removed that problem (see the decision log).

---

## 5. How the model is chosen and how to read the metrics

- **Choice:** 4-fold stratified **cross-validation on the training set** — every model is trained and scored
  4 times on different parts of the training data. The test set is not used for choosing; it is scored once at
  the end. Winner: **TF-IDF + Naive Bayes**.
- **Final model:** retrained on all 1,724 developers before use in the app.

| Metric             | Plain meaning                                                           | TF-IDF + NB (test) |
| ------------------ | ----------------------------------------------------------------------- | ------------------ |
| Accuracy           | the top prediction is the right repo                                    | 75%                |
| **Top-5 accuracy** | the right repo is among the 5 we would show → **the app's real metric** | **88%**            |
| Macro F1           | quality averaged per repo, small repos count as much as big ones        | 0.68               |
| Weighted F1        | same, weighted by repo size                                             | 0.72               |

Context: with 117 repos, guessing the most common repo gets 2% accuracy / 6% top-5. Macro F1 is lower than
accuracy because small repos (5–6 developers, only 1 in the test set) are harder.

**Settings** are tuned with the same cross-validation, on small grids (Naive Bayes smoothing `alpha`,
Logistic Regression `C`), and chosen by **top-5 accuracy** because that is what the app shows. Chosen:
`alpha = 0.1`, `C = 100`.

---

## 6. Why TF-IDF beats Sentence-BERT here

- **TF-IDF** scores _exact words_, with rare, specific words weighted most. What links a developer to a repo
  is mostly exact names: `tokio`, `pydantic`, `webcontents`, `strftime`, `polars`.
- **Sentence-BERT** encodes _general meaning_. "fix strftime on NetBSD" and "fix date parsing on Windows" look
  similar to it — useful for semantics, but it blurs the exact names that matter here. It also reads only the
  first ~256 tokens.
- Result: TF-IDF + NB 88% top-5 vs Sentence-BERT + LR 67%. With longer texts the gap grows: Sentence-BERT
  still reads only the start, while TF-IDF uses every word.

---

## 7. How the top 5 repos are chosen

1. The classifier gives a probability for each of its **117 repos**.
2. Repos **without open issues** in the snapshot are excluded (the user would have nothing to start on) →
   **116** can be recommended. Separately, 5 of the 202 repos have no open issues at all (`tiangolo/fastapi`,
   `tiangolo/typer`, `pnpm/pnpm`, `d3/d3`, `koajs/koa` — e.g. fastapi uses GitHub Discussions).
3. The 5 highest are shown, **by rank only**. Naive Bayes ranks well, but its probability values are squashed
   toward 1/117 (all ≈ 1%), so showing them would mislead.
4. Repos the user already contributes to are **not** treated specially — they are ranked like any other.

---

## 8. How issues are chosen inside a repo

For each of the 5 repos, every **open** issue gets a score:

```text
score = cosine( TF-IDF(app profile), TF-IDF(issue text) )  +  0.05 if labelled good first issue / help wanted
```

- **Issue text** = title + cleaned body + the repo's name, language, topics and description.
- **Cosine similarity** (0–1) is how much the two texts share their weighted words; good matches are around
  0.1–0.3.
- The **+0.05 boost** nudges beginner-friendly issues up without overriding relevance.
- The top 3 are shown. Titles that are only a template (e.g. React's "Bug:") get the start of the body appended.
- This step is a simple ranking for display; it is **not evaluated** (no ground truth for "would this person
  enjoy this issue").

---

## 9. How the "Why" words are computed

The cosine similarity of two TF-IDF vectors is a sum over words: `Σ weight_profile(w) × weight_doc(w)`.
The "Why" lists the words with the **largest share of that sum** (words shorter than 3 letters skipped).

Real example — `demo-jordan-web` vs `vitejs/vite` (cosine 0.236):

| word       | share of the score |
| ---------- | ------------------ |
| vite       | 0.058              |
| vitejs     | 0.036              |
| frontend   | 0.031              |
| tooling    | 0.016              |
| generation | 0.010              |

→ shown as _"Why: vite, vitejs, frontend, tooling, generation"_. The "Why" always uses TF-IDF (readable words),
whichever model picked the repo.

---

## 10. How bots, beginner labels and PR→issue links are detected

**Bots** (`clean.py`, `is_bot`) — an account is a bot if any of:

- GitHub marks it `type: "Bot"` (e.g. the Copilot coding agent, 71 PRs),
- the login ends in `bot` or `robot` (`gopherbot`, `tekton-robot`, `…[bot]`),
- it is a known CI reporter registered as a normal user: `cockroach-teamcity`, `elasticsearchmachine`,
  `GordonTheTurtle` (they file auto-generated "test failed" issues).

About 280 issues and 125 PRs were removed. Two ClickHouse accounts that look like AI agents (`clickgapai`,
`groeneai`) were **kept** on purpose — their content is substantive.

**Beginner-friendly / help wanted** — labels are lowercased, emoji removed, then matched with patterns:

- beginner: `good first`, `first-time`, `first-contribution`, `beginner`, `starter`, `newcomer`, `easy`
  (but not `not-as-easy-as-it-looks`),
- help wanted: `help wanted`, `help-needed`, `contrib-help`.

Catches variants like `good-first-issue`, `e-easy`, `🌱 good first issue`, `status: help wanted`
→ 210 beginner-friendly, 226 help wanted.

**PR → issue links** — GitHub's closing keywords (`close/closes/closed`, `fix/fixes/fixed`,
`resolve/resolves/resolved`) followed by `#N`, `owner/repo#N` (same repo only) or a full issue URL.
`refs #N` only _mentions_ an issue, so it is stored as a reference, not as a closing link.

---

## 11. Gotchas

- **Empty text becomes NaN** in pandas by default → always `pd.read_csv(path, keep_default_na=False)`
  (or use `recommender.data.load`).
- **List columns are JSON strings** (`labels`, `topics`, …) → `json.loads`.
- **Renamed repos:** 17 repos were renamed on GitHub (e.g. `tiangolo/fastapi` → `fastapi/fastapi`). Files and
  `repo_id` use the name from `repo_list.csv`; the current name is in `current_full_name`.
- **Issue time window:** GitHub's `since` means _updated_ since, so 24% of issues were created before
  2026-06-24 (flag `created_in_window`).
- **Issue cap:** 101 repos hit the 100-issue cap, so we only see their 100 most recently updated issues.
- **Symlinked READMEs:** some repos' README is a symlink (axum, actix-web, dagster); the collector follows it.
- **Naive Bayes probabilities** are not meaningful as percentages — use the ranking.
- **Data is not in git** (`data/` is ignored) and the README share link still points to the old, incomplete
  collection.

---

## 12. Decision log

| Date       | Decision                                                                                                                                                                            | Why                                                                                               |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| 2026-09-30 | Fixed the collector (PR paging stops at the date window, resumable, 4xx skips a repo) and re-ran it                                                                                 | the first run stopped at row 108 on a repo with Issues disabled; half the repos had no issues/PRs |
| 2026-10-01 | READMEs fetched via the `/readme` API (follows symlinks)                                                                                                                            | 28 READMEs were saved as "404 Not Found" pages, 3 as bare symlink paths                           |
| 2026-10-01 | Dropped 17 repos (12 Issues disabled, 5 archived/inactive) → 202                                                                                                                    | nothing to recommend from them; they break the "active, has issues" criteria                      |
| 2026-10-01 | Kept issues created before the window (flagged)                                                                                                                                     | they are still active; filtering is a one-liner if needed                                         |
| 2026-10-01 | `refs #N` is not a closing link                                                                                                                                                     | it only mentions an issue                                                                         |
| 2026-10-01 | Dropped PR size columns (commits, additions, …)                                                                                                                                     | the PR list endpoint doesn't return them; not needed                                              |
| 2026-10-01 | Kept `clickgapai` / `groeneai`                                                                                                                                                      | content looks substantive; not clearly bots                                                       |
| 2026-10-01 | Recommend **repos + issues** (top 5 repos, 3 issues each)                                                                                                                           | matches "suggest repos that fit my profile" and the original issue idea                           |
| 2026-10-01 | Pool = our 202 repos, snapshot 2026-10-01, no live re-check                                                                                                                         | course-project scope                                                                              |
| 2026-10-01 | No special handling of repos the user already contributes to                                                                                                                        | not needed                                                                                        |
| 2026-10-01 | Dummy users in GitHub API format                                                                                                                                                    | build the app before the live fetch exists                                                        |
| 2026-10-02 | **Reframed modeling as classification (developer → repo) with a standard random train/test split**; removed the time-based ranking evaluation and the `developer_issue_pairs` table | simpler, standard ML; the time split was only needed for per-issue ranking                        |
| 2026-10-02 | Standard models only (TF-IDF + NB / LR, Sentence-BERT + LR), no hand-tuning grid                                                                                                    | course-project scope                                                                              |
| 2026-10-02 | TF-IDF + Naive Bayes chosen                                                                                                                                                         | best cross-validation accuracy; best test top-5 accuracy                                          |
| 2026-10-02 | Show repos by rank, not probability                                                                                                                                                 | NB probabilities are all ≈ 1%                                                                     |
| 2026-10-02 | Implementation in `recommender/*.py`, notebooks only call it                                                                                                                        | cleaner notebooks, reusable code for the app                                                      |
| 2026-10-02 | **Improved the classifier:** full PR descriptions (≤ 2,000 chars) + titles of issues the developer opened; TF-IDF of words + word pairs + character 3–5-grams; small CV grids (`alpha`, `C`) chosen by top-5 accuracy | test accuracy 0.51 → 0.75, top-5 0.73 → 0.88, macro F1 0.36 → 0.68 |
| 2026-10-02 | Remove each repo's PR-template sentences (in ≥ 3 PRs of the same repo) from the training text | templates identify the repo, not the developer; they inflated accuracy by ~5 points |
| 2026-10-02 | App profile uses the same PR-description length (2,000 chars) as training | keep training and app input as similar as possible |
