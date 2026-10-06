# Op3nSrc: Personalized Open-Source Contribution Recommendation

**Group members:**  
[Add names]

**Workshop #:**  
[Add workshop number]

---

## MOTIVATION

**Target group:** Developers who want to contribute to open-source projects, particularly beginner-to-intermediate contributors.

**End-user:** Developers looking for open-source contribution opportunities that match their existing skills and interests.

Many developers are interested in contributing to open source but struggle to identify **which projects and issues are suitable for their current skill level**. GitHub contains a very large number of repositories and open issues, making it difficult for users to find relevant contribution opportunities.

Our target users are developers who want to start or continue contributing to open source. Their objective is to find meaningful issues where their existing technical skills, experience and interests are relevant.

The main needs we aim to address are:

- Difficulty navigating the large number of open-source issues.
- Difficulty determining whether an issue matches the developer's skills.
- Lack of personalized recommendations.
- Difficulty identifying beginner-friendly or realistically achievable issues.
- "Backlog fatigue", where developers become overwhelmed by the number of available issues.

---

## CORE IDEA

The system analyzes a developer's technical profile and matches it with open-source projects and their issues.

Instead of simply showing popular repositories, it answers:

> **"Which open-source projects, and which issues in them, are a good match for me?"**

**In one sentence:** the user enters their **GitHub username**, and Op3nSrc recommends the
**open-source projects (repos) that fit their skills**, plus **specific open issues inside each project**
they could start with.

What the user sees:

```text
Enter GitHub username: [ octocat ]  → Find matches

1. litestar-org/litestar
   Why: sqlalchemy, pydantic, openapi, pytest
   Issues to start with:
     • #2118 Enhancement: Revoke jwt token          good first issue, help wanted
     • #2015 Support for typing the `query` keyword good first issue, help wanted
     • #3362 Docs: move code-block directives …     help wanted

2. celery/celery
   …
(top 5 repos, 3 issues each)
```

### How it works

```text
GitHub username
        ↓  1. Fetch the user's public GitHub data (own repos, languages,
        ↓     merged PRs) → one profile text
        ↓  2. A text classifier predicts which of our repos fit the profile → top 5 repos
        ↓  3. Inside each of those repos, rank its open issues by text similarity to the profile
        ↓     (small boost for `good first issue` / `help wanted`) → top 3 issues
        ↓  4. Explain each match with the shared words ("Why: …")
Top 5 repos × 3 issues, shown in a simple web app
```

**The ML model is a standard text classifier:** _developer profile text → repo_. It is trained on the
developers in our data (their merged-PR text → the repo they contribute to). We compare standard
models — TF-IDF + Naive Bayes, TF-IDF + Logistic Regression, Sentence-BERT embeddings + Logistic
Regression — against a "most frequent repo" baseline. Issue ranking inside a repo (step 3) is a simple
TF-IDF similarity used for display; it is not a separately evaluated model.

### Scope decisions

- **Recommendation pool:** only the **202 repos** in `data/repo_list.csv` and their issues, not all of GitHub.
- **Data snapshot:** issues are from the **2026-10-01** collection; we do not re-check live whether an
  issue has been closed since.
- **No special handling** of repos the user already contributes to: they are ranked like any other repo.
- **User data:** until the live GitHub fetch is built, the app uses **dummy users** stored in exactly the
  format the GitHub API returns (`dummy_users/`), so swapping in the live fetch changes nothing
  else.

### How we show it works

A standard ML evaluation: one row per developer (profile text, repo), a **stratified random 80/20
train/test split**, model choice by cross-validation on the training set, and on the test set:
**accuracy**, **top-5 accuracy** (the true repo is among the 5 we would recommend) and **F1**.

### Approach — NLP-based recommendation

Uses standard NLP techniques — **TF-IDF** and a small pretrained model (**Sentence-BERT**) — to represent developer text, a standard classifier to predict fitting repos, and text similarity to pick issues inside them.

→ See **`PROJECT_OVERVIEW.md`** for how the whole project works (data, cleaning, model, results).

→ See **`NOTES.md`** for the details behind each step and the decision log.

---

## ADDED VALUE

The primary added value is **reducing the gap between developers who want to contribute and open-source projects that need contributors**.

Instead of searching through hundreds of projects and thousands of issues, users receive a short list of projects that fit their skills, each with concrete issues to start on.

Potential benefits include:

- Faster discovery of relevant projects.
- Better matching between developer skills and project needs.
- Easier entry into open source for newcomers.
- More meaningful contribution opportunities.
- Reduced backlog fatigue.

The recommendation is converted into an actionable outcome for the end-user:

```text
GitHub username → developer profile
        ↓
Recommendation model
        ↓
Ranked repos (classifier)
        ↓
Open issues in each, ranked by text similarity
        ↓
Actionable contribution opportunities
```

The user can then open the recommended project and issues directly and decide whether to contribute.

---

## PROJECT TIMELINE (HIGH LEVEL)

### WEEK 1 — Data Collection & Preprocessing

- Identify the repo set (202 hand-picked repos in `data/repo_list.csv`).
- Set up GitHub API access.
- Collect repositories, issues and pull requests.
- Store raw JSON.
- Build the shared preprocessing pipeline and feature tables.

### WEEK 2 — EDA & Visualizations

- Analyze the repository ecosystem and issue characteristics.
- Explore contribution patterns.
- Build initial visualizations.

### WEEKS 3–4 — Modeling & App

- Build the dataset (one row per developer: profile text → repo) and a stratified train/test split.
- Train standard classifiers: TF-IDF + Naive Bayes / Logistic Regression, Sentence-BERT + Logistic Regression.
- Evaluate with accuracy, top-5 accuracy and F1 against a most-frequent-repo baseline.
- Rank open issues inside the recommended repos with TF-IDF similarity.
- Build the user profile from (dummy) GitHub data and integrate the chosen model into the web application.

### WEEK 5 — Fairness, Privacy & Finalization

- Analyze potential biases (e.g. GitHub activity volume as a proxy for skill).
- Review privacy considerations and API usage.
- Finalize the application and presentation.
