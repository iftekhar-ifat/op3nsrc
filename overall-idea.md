# MINI PROJECT CANVAS

**Title (preliminary):** Op3nSrc: Personalized Open-Source Contribution Recommendation

**Group members:**  
[Add names]

**Workshop #:**  
[Add workshop number]

---

## MOTIVATION

**Target group:** Developers who want to contribute to open-source projects, particularly beginner-to-intermediate contributors.

**End-user:** Developers looking for open-source contribution opportunities that match their existing skills and interests.

### Which is the target group of our mini-project? Who is the end-user? What are their objectives? What needs do we need to address with our work?

Many developers are interested in contributing to open source but struggle to identify **which projects and issues are suitable for their current skill level**. GitHub contains a very large number of repositories and open issues, making it difficult for users to find relevant contribution opportunities.

Our target users are developers who want to start or continue contributing to open source. Their objective is to find meaningful issues where their existing technical skills, experience and interests are relevant.

The main needs we aim to address are:

- Difficulty navigating the large number of open-source issues.
- Difficulty determining whether an issue matches the developer's skills.
- Lack of personalized recommendations.
- Difficulty identifying beginner-friendly or realistically achievable issues.
- "Backlog fatigue", where developers become overwhelmed by the number of available issues.

### How will they benefit from this proposed solution? (Added value)

The system will analyze a developer's technical profile and match it with open-source issues.

Instead of simply showing popular repositories, it will answer:

> **"Which open-source issues are a good match for me?"**

For example:

> **Recommended issue:** Add pagination to a FastAPI endpoint  
> **Match:** 89%  
> **Why:** Your GitHub activity indicates experience with Python, FastAPI and REST APIs. The issue is also labelled `good first issue`.

This can reduce the time spent searching and help developers make more confident contributions.

Potential additional benefits include:

- Faster discovery of relevant projects.
- Better matching between developer skills and project needs.
- Easier entry into open source for newcomers.
- More meaningful contribution opportunities.
- Reduced backlog fatigue.

---

# DATA COLLECTION

### Which data sources are we planning to use?

We plan to collect **real-world public data directly from GitHub rather than using a pre-existing Kaggle dataset**.

The primary source will be the **GitHub REST API**, using publicly available information from open-source repositories, issues and pull requests.

Potential data sources include:

### GitHub repositories

For selected open-source repositories:

- Repository name
- Description
- README
- Programming languages
- Topics
- Stars
- Forks
- Number of issues
- Repository activity
- Creation/update dates

### GitHub issues

For open and historical issues:

- Issue title
- Issue description/body
- Labels
- Creation date
- Closing date
- Number of comments
- Issue state
- Repository
- Associated users
- Linked pull requests where available

### GitHub pull requests

For historical contribution analysis:

- PR title
- PR description
- Repository
- Author
- Linked issue
- Programming language
- Number of commits
- Files changed
- Lines added/deleted
- Whether the PR was merged
- Time taken to merge

### Developer profile/activity

For users who choose to connect their GitHub account, we may use publicly available information such as:

- Public repositories
- Programming languages
- Repository topics
- Project descriptions
- Contribution history

We will initially focus on a manageable subset of active open-source repositories, potentially concentrating on **Python/AI/ML and software-development projects**.

### Data management plan

Raw GitHub API responses will be stored separately from processed data.

```text
GitHub API
    ↓
Raw JSON
    ↓
Cleaned datasets
    ↓
Feature tables
    ↓
ML-ready data
```

Possible storage formats:

- JSON for raw API responses
- Parquet/CSV for processed datasets
- PostgreSQL for the application database

We will retain the raw data so that the preprocessing and feature-engineering pipeline can be reproduced.

---

# PREPROCESSING

### What are the goals of the preprocessing pipeline?

The main goal is to transform raw GitHub repository, issue, pull-request and developer data into structured representations that can be used for matching and recommendation.

Possible preprocessing steps include:

- Remove duplicate issues and repositories.
- Handle missing descriptions and metadata.
- Remove invalid or deleted records.
- Normalize programming language names.
- Standardize GitHub labels.
- Handle timestamps and convert them into useful temporal features.
- Filter inactive or extremely small repositories where appropriate.
- Remove bots and automated accounts where identifiable.
- Parse issue body only to extract structural metadata (word count, checklist item count, code block count) — not for text modeling.
- Handle very short or empty issue descriptions by flagging them or imputing defaults.

### Data transformations and feature engineering

We will create structured numerical and categorical features representing both **developer capabilities** and **issue requirements**.

#### Developer features

Examples:

- Programming language experience (count of repos per language).
- Number of repositories.
- Repository activity (commits per month, recent activity score).
- Experience with specific frameworks (based on repo topics/descriptions).
- Domain experience scores (ML, web development, DevOps, etc.).
- Frequency of contributions (PRs per month).
- Number of previous pull requests.
- Number of merged contributions (merge rate).
- Average PR size (lines changed).
- Number of unique projects contributed to.
- Account age.
- Contribution recency (days since last contribution).

#### Issue features

Examples:

- Programming languages involved (one-hot or multi-hot encoded).
- Issue type (bug, feature, documentation, etc.) from labels (one-hot encoded).
- Binary flags for labels: `good first issue`, `help wanted`, `beginner`, `easy`.
- Difficulty-related signals (label-based, comment count, files changed in linked PR).
- Number of comments (as engagement/complexity indicator).
- Issue age (days since creation).
- Repository activity (stars, forks, recent commit frequency).
- Number of files changed in linked PRs.
- Lines of code added/deleted in linked PRs.
- Number of assignees / linked PRs (indicates demand/competition).
- Temporal features: day of week created, month created.
- Description length (word count) as a basic complexity signal.
- Number of bullet points or checklists in issue body (parsed as count, not text).

All features are **purely numerical and categorical** — no text vectorization, no NLP pipelines and no deep-learning embeddings. This ensures full compatibility with standard ML models such as Logistic Regression, Random Forest and XGBoost.

The result will be a structured feature vector such as:

```text
Developer Feature Vector
lang_python          1
lang_javascript      0
repos_count          12
pr_count             34
merge_rate           0.76
avg_pr_size          48
framework_fastapi    1
framework_django     0
domain_web           1
domain_ml            0
...

Issue Feature Vector
lang_python          1
lang_javascript      0
label_good_first     1
label_help_wanted    0
comments_count       5
issue_age_days       12
repo_stars           1420
repo_forks           310
...
```

These structured representations can then be used for recommendation and ranking with standard ML algorithms.

---

# EXPLORATORY DATA ANALYSIS (EDA)

We will first explore the characteristics of the collected open-source ecosystem.

Planned analysis includes:

### Repository analysis

- Distribution of repository sizes.
- Most common programming languages.
- Repository activity.
- Distribution of stars and forks.
- Most common repository topics.

### Issue analysis

- Number of issues per repository.
- Distribution of issue age.
- Most common labels.
- Frequency of `good first issue` and `help wanted`.
- Issue description length.
- Number of comments.
- Relationship between issue characteristics and eventual resolution.

### Pull-request analysis

- Distribution of PR sizes.
- Number of commits.
- Files changed.
- Merged vs non-merged PRs.
- Time between issue creation and PR merge.

### Developer analysis

Where sufficient public data is available:

- Distribution of programming language experience.
- Contribution frequency.
- Number of repositories.
- Previous contribution patterns.

EDA will help us understand whether meaningful patterns exist before building the recommendation model.

---

# VISUALIZATIONS

Planned visualizations include:

### Repository ecosystem

- Bar chart of programming languages.
- Distribution of repository activity.
- Repository size/stars distribution.

### Issue characteristics

- Issue-label distribution.
- Issue age distribution.
- Issue complexity indicators.
- Relationship between issue complexity and resolution time.

### Developer profiles

Interactive skill profiles showing:

```text
Python       ████████████████
Java         ███████████
JavaScript   ████████
Docker       █████
C++          ███
```

### Feature importance and model analysis

- Feature importance bar charts from tree-based models.
- Correlation heatmap of numerical features.
- Distribution of match scores.

### Recommendation visualization

For an individual developer:

**Top recommended issues**

| Issue | Repository | Match |
|---|---|---:|
| API pagination | Project A | 91% |
| Add unit tests | Project B | 87% |
| Fix async handling | Project C | 83% |

We may also use **PCA** to visualize developer and issue representations in a lower-dimensional space.

Interactive visualizations could allow users to:

- Filter by programming language.
- Filter by difficulty.
- Filter by repository/domain.
- Explore why an issue was recommended.
- View the skills matched to each issue.

---

# LEARNING TASK

### Define the problem setting.

The primary problem is a **personalized recommendation and ranking task**.

It can be approached as a combination of:

1. **Supervised classification** to predict whether a developer-issue pair is a good match (based on historical contribution outcomes).
2. **Supervised regression** to predict a suitability/match score.
3. **Learning-to-rank** to rank candidate issues for a given developer.

### What are we planning to learn?

The system aims to learn or calculate:

> **How suitable is a particular open-source issue for a particular developer?**

The input consists of:

### Developer features

- Programming language experience (numerical counts).
- Number of repositories.
- Contribution frequency.
- Merge rate.
- Average PR size.
- Framework and domain experience scores.
- Account age and recency.

### Issue features

- Programming languages involved (encoded).
- Labels (encoded as binary flags).
- Difficulty signals.
- Number of comments.
- Issue age.
- Repository metrics (stars, forks, activity).
- PR size metrics from linked pull requests.

### Possible learning outcome

A relevance/suitability score:

```text
Developer Feature Vector
        +
Issue Feature Vector
        ↓
ML Model (e.g., XGBoost, Random Forest)
        ↓
87% Match Score
```

The system will then rank candidate issues and recommend the highest-scoring ones.

### Optional research extension

Using historical issue to pull request relationships, we could investigate whether developer/issue compatibility features can predict **successful contribution outcomes**, such as whether a contribution is eventually merged. This becomes a binary classification task.

---

# LEARNING APPROACH

### Which ML/statistical methods seem relevant and why?

We plan to use standard machine learning models that work well with structured tabular features.

### 1. Baseline: Weighted scoring model

A simple heuristic baseline that combines:

- Skill overlap (Jaccard similarity on programming languages).
- Label match (e.g., bonus for `good first issue`).
- Repository activity score.
- Difficulty compatibility.

This provides a non-ML baseline to compare against.

### 2. Random Forest / Gradient Boosted Trees

**XGBoost, LightGBM, or scikit-learn's GradientBoostingClassifier/Regressor**

These models are well-suited for:
- Mixed numerical and categorical features.
- Capturing non-linear relationships.
- Providing feature importance rankings.
- Working without extensive hyperparameter tuning.

The model will take concatenated developer and issue feature vectors as input and predict a match score or contribution success probability.

### 3. Logistic Regression / Linear models

A linear baseline for interpretability:
- Easy to understand feature weights.
- Fast training and inference.
- Useful for identifying which features matter most.

### 4. Clustering for segmentation

We may use clustering techniques such as:

- K-Means
- HDBSCAN

to identify groups of issues or developer profiles with similar characteristics. Cluster assignments become additional categorical features for the ML model.

For example:

```text
Backend/API issues
ML issues
Frontend issues
Documentation issues
DevOps issues
Testing issues
```

### 5. Learning-to-rank

For ranking candidate issues per developer, we may use:

- XGBoost with `rank:pairwise` objective.
- LambdaMART-style approaches.
- Alternatively, sort by predicted match score from a regression model.

### Evaluation metrics

Potential metrics include:

- Precision@K
- Recall@K
- NDCG@K
- Mean Reciprocal Rank (MRR)
- Hit Rate@K

For example:

> Of the top 5 issues recommended to a developer, how many are considered relevant?

For a supervised success-prediction extension, possible metrics include:

- Precision
- Recall
- F1
- ROC-AUC

### Data splitting / validation

Because GitHub data is **temporal**, random train/test splitting may cause information leakage.

We will consider a **time-based split**, for example:

```text
Historical GitHub activity
        ↓
Training data

Later GitHub activity
        ↓
Test data
```

This better reflects the real-world use case where the model recommends future contribution opportunities using past information.

---

# COMMUNICATION OF RESULTS

The main deliverable will be an **interactive web application** targeted at developers.

### Proposed workflow

```text
1. User connects GitHub account
             ↓
2. System analyzes public technical activity
             ↓
3. Developer feature vector is computed
             ↓
4. User selects preferences
             ↓
5. System retrieves candidate open-source issues
             ↓
6. Feature vectors are constructed for each pair
             ↓
7. ML model scores and ranks issues
             ↓
8. User receives personalized recommendations
```

The interface will display:

### Your developer profile

```text
Python          91%
FastAPI         84%
Machine Learning 76%
Docker          52%
JavaScript      44%
```

### Recommended contributions

```text
#1  Add API pagination
    FastAPI / Project X
    Match: 91%

#2  Improve test coverage
    MLflow / Project Y
    Match: 87%

#3  Fix data validation
    Project Z
    Match: 84%
```

### Explainability

For every recommendation, the system should explain:

> **Why was this recommended?**

Using feature importance from tree-based models or feature contributions:

```text
✓ Matches your Python experience
✓ Matches your FastAPI experience
✓ Similar to projects you have contributed to
✓ Marked "good first issue"
✓ Repository is actively maintained
```

This explanation is an important part of communicating the recommendation rather than presenting it as a black-box prediction.

---

# DATA PRIVACY AND ETHICAL CONSIDERATIONS

The project will primarily use **publicly available GitHub data**.

However, several considerations apply.

### Privacy

- Only collect information necessary for the recommendation task.
- Avoid collecting private repositories or private account information.
- Do not expose unnecessary personal information in the application.
- Developer identities should be pseudonymized in the research dataset where possible.
- If users connect their GitHub account, clearly communicate what information is being accessed and why.

### API and platform considerations

We will follow GitHub's API terms, rate limits and applicable policies rather than scraping GitHub aggressively.

### Fairness

The recommendation system may unintentionally favor developers with more GitHub activity.

For example:

> A developer with 100 public repositories may appear more experienced than someone with strong skills but little public GitHub activity.

Therefore, the system should avoid treating **GitHub activity volume as equivalent to technical ability**.

We will investigate whether recommendations differ systematically based on factors such as:

- Contribution history.
- Account age.
- Amount of public activity.
- Experience level.

### Other ethical considerations

The system should present recommendations as **potentially suitable opportunities**, not guarantee that a developer will successfully complete an issue.

---

# ADDED VALUE

### Is there a possibility for added value from the data?

Yes.

The combination of repository metadata, issue descriptions, labels, developer activity and historical pull requests can reveal relationships between:

```text
Developer skills
        ↕
Technical requirements
        ↕
Open-source issues
        ↕
Successful contributions
```

This allows us to create a personalized contribution discovery system rather than simply searching GitHub using keywords.

### What is the added value?

The primary added value is **reducing the gap between developers who want to contribute and open-source projects that need contributors**.

Instead of searching through thousands of issues, users receive a ranked shortlist of issues relevant to their skills and interests.

### How are predictions turned into added value for the end-user?

The ML model produces a compatibility score:

```text
Developer Feature Vector + Issue Feature Vector
        ↓
ML Model (XGBoost / Random Forest)
        ↓
Compatibility Score
        ↓
Ranked Issues
        ↓
Actionable contribution opportunities
```

The user can then directly investigate the recommended issue and decide whether to contribute.

The system therefore converts raw GitHub activity into an **actionable recommendation for the developer**.

---

# LEGEND / PROJECT TIMELINE

### WEEK 1 — Data Collection & Preprocessing

- Identify 100-200 relevant repositories.
- Set up GitHub API access.
- Collect repositories, issues and pull requests.
- Store raw JSON.
- Build preprocessing pipeline.
- Define developer and issue features.
- Engineer numerical and categorical features.

### WEEK 2 — EDA & Visualizations

- Analyze repository ecosystem.
- Analyze issue characteristics.
- Explore contribution patterns.
- Build initial visualizations (bar charts, distributions, correlation heatmaps).
- Investigate relationships between issue characteristics and successful contributions.

### WEEKS 3-4 — Machine Learning

**Week 3**

- Build weighted-score baseline model.
- Construct feature matrices for developer-issue pairs.
- Train Logistic Regression and Random Forest baselines.
- Experiment with feature selection and hyperparameter tuning.
- Perform K-Means clustering for developer/issue segmentation.

**Week 4**

- Train XGBoost / LightGBM models.
- Implement learning-to-rank approach.
- Evaluate Precision@K, Recall@K, NDCG@K and MRR.
- Compare baseline vs ML approaches.
- Analyze feature importance for explainability.
- Build recommendation explanations from model outputs.
- Integrate model into application.

### WEEK 5 — Fairness & Data Privacy

- Analyze potential biases.
- Evaluate limitations of GitHub activity as a proxy for skill.
- Review privacy considerations.
- Review API usage and data retention.
- Document ethical considerations.
- Finalize application and presentation.
