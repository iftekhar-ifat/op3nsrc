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

The system analyzes a developer's technical profile and matches it with open-source issues.

Instead of simply showing popular repositories, it answers:

> **"Which open-source issues are a good match for me?"**

For example:

> **Recommended issue:** Add pagination to a FastAPI endpoint  
> **Match:** 89%  
> **Why:** Your GitHub activity indicates experience with Python, FastAPI and REST APIs. The issue is also labelled `good first issue`.

This can reduce the time spent searching and help developers make more confident contributions.

The overall pipeline is:

```text
GitHub public data (repositories, issues, pull requests, developer activity)
        ↓
Preprocessing + feature engineering
        ↓
Recommendation model
        ↓
Ranked, personalized issue recommendations
        ↓
Interactive web application for developers
```

### Approach A — NLP-based recommendation

Uses standard NLP techniques such as **TF-IDF** and small pretrained models (e.g. **Sentence-BERT / BERT embeddings**) to represent issue and developer text, then matches developers to issues using textual and semantic similarity.

→ See **`nlp-recommendation.md`** for the full model implementation plan.

→ See **`data-collection-and-processing.md`** for the step-by-step data collection and preprocessing workflow.

---

## ADDED VALUE

The primary added value is **reducing the gap between developers who want to contribute and open-source projects that need contributors**.

Instead of searching through thousands of issues, users receive a ranked shortlist of issues relevant to their skills and interests.

Potential benefits include:

- Faster discovery of relevant projects.
- Better matching between developer skills and project needs.
- Easier entry into open source for newcomers.
- More meaningful contribution opportunities.
- Reduced backlog fatigue.

The recommendation is converted into an actionable outcome for the end-user:

```text
Developer profile + open issues
        ↓
Recommendation model
        ↓
Compatibility score
        ↓
Ranked issues
        ↓
Actionable contribution opportunities
```

The user can then directly investigate the recommended issue and decide whether to contribute.

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

### WEEKS 3–4 — Modeling

- Build the TF-IDF baseline recommendation model.
- Build the Sentence-BERT embedding-based recommendation model (see `nlp-recommendation.md`).
- Evaluate with Precision@K, Recall@K, NDCG@K and MRR.
- Compare the embedding model against the TF-IDF baseline.
- Integrate the chosen model into the web application.

### WEEK 5 — Fairness, Privacy & Finalization

- Analyze potential biases (e.g. GitHub activity volume as a proxy for skill).
- Review privacy considerations and API usage.
- Finalize the application and presentation.
