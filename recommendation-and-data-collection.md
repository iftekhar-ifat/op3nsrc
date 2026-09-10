# Op3nSrc: Recommendation Algorithm and Data Collection Plan

## 1. Recommended approach

Op3nSrc should use a **structured-feature recommendation system with a simple supervised machine-learning ranking model**.

The system will compare structured developer attributes with structured issue and repository attributes to produce a suitability score. This is appropriate because a new user may not have any previous interaction history in our application. The system can still make recommendations from the user's skills, experience and contribution history.

### Recommended model

The recommended model is **logistic regression used as a binary relevance classifier**.

For each developer-issue pair, the model predicts:

```text
1 = relevant or suitable recommendation
0 = not relevant or unsuitable recommendation
```

The predicted probability of class `1` becomes the recommendation score. Issues are sorted by this score, and the highest-ranked issues are shown to the user.

Logistic regression is suitable because it is:

- Simple to implement and explain.
- An established machine-learning model.
- Fast to train on a small or medium-sized dataset.
- Suitable for a mixture of numeric and categorical features.
- More interpretable than complex neural models.
- Able to show which features contribute to a recommendation.

The project should begin with a **popularity and compatibility baseline**. This baseline is not the final model, but it gives us a transparent comparison:

```text
Developer attributes + issue attributes
        ↓
      Compatibility features
        ↓
    Initial ranking score
```

The supervised model can then use these structured features:

```text
Developer-issue feature vector
              ↓
       Logistic regression
              ↓
      Suitability probability
              ↓
          Ranked issues
```

## 2. Other models we could use

### A. Compatibility and popularity baseline

This ranks issues using transparent rules based on skill overlap, experience compatibility, repository activity and issue accessibility. It does not use text representations or NLP.

**Advantages:** very simple, fast, interpretable and works without labeled training data.

**Limitations:** fixed rules cannot learn complex relationships between developer and issue features.

This should be the baseline model.

### B. Linear support vector machine

A linear support vector machine (Linear SVM) can classify developer-issue pairs using the structured compatibility features described below.

**Advantages:** a well-established supervised model that works efficiently with numeric and one-hot encoded features.

**Limitations:** it does not produce calibrated probabilities without additional calibration, and its decision score is less directly interpretable than logistic regression.

This should be used as a classical comparison model if time allows. NLP, attention-based models, transformer models and newer neural models are outside the scope of the first version.

### C. Logistic regression ranking model

Logistic regression can learn from historical examples of developer-issue pairs. Features may include shared programming languages, shared topics, issue labels, estimated difficulty, repository activity and developer experience.

**Advantages:** simple supervised ML, interpretable, fast and appropriate for a small project.

**Limitations:** it needs labeled examples and depends on the quality of the labels.

This is the recommended final model.

### D. Decision tree or random forest

These models can learn non-linear relationships between structured features such as issue age, number of comments, repository activity and skill overlap.

**Advantages:** handles non-linear feature interactions and is relatively easy to use.

**Limitations:** can overfit a small dataset and may be less interpretable than logistic regression.

This can be used as a standard ML comparison model, but it should not be the first choice.

### E. Matrix factorization or collaborative filtering

This learns from user-item interaction history, such as users viewing, saving or contributing to issues.

**Advantages:** useful when many users have interacted with many issues.

**Limitations:** suffers from the cold-start problem. A new user or a new issue has no interaction history, which makes it unsuitable as the main method for this project.

## 3. Final model design

The model should use structured compatibility features only. Raw descriptions, README files, issue titles and pull-request bodies may be retained for auditability, but they must not be used as model inputs in this pure ML version.

### Candidate features

For every developer-issue pair, create one row containing:

| Feature                      | Description                                                         |
| ---------------------------- | ------------------------------------------------------------------- |
| `language_overlap`           | Proportion of issue languages also present in the developer profile |
| `topic_overlap`              | Overlap between developer interests and repository topics           |
| `framework_overlap`          | Shared frameworks or technical tools                                |
| `good_first_issue`           | Whether the issue has a beginner-friendly label                     |
| `help_wanted`                | Whether the issue has a `help wanted` label                         |
| `issue_age_days`             | Age of the open issue at recommendation time                        |
| `issue_comment_count`        | Number of comments                                                  |
| `repository_activity`        | A recent activity measure for the repository                        |
| `estimated_difficulty`       | Difficulty estimated from labels and issue characteristics          |
| `developer_experience_level` | Experience level estimated from contribution history                |
| `difficulty_difference`      | Difference between issue difficulty and developer experience        |

Categorical variables should be encoded numerically. Numeric features should be scaled when appropriate. Missing values should be represented consistently and documented.

### Training labels

The strongest available positive label is a historical developer-issue pair where:

- The developer opened a pull request linked to the issue, and
- The pull request was merged.

Possible negative examples include:

- A developer-issue pair with no contribution, sampled from issues available at that time.
- A linked pull request that was closed without being merged, if this is treated as an unsuccessful outcome.

Negative sampling must be done carefully. The absence of a pull request does not prove that the developer considered or rejected the issue. Therefore, the dataset should describe these as **unobserved or assumed-negative examples**, not confirmed failures.

A row could look like this:

```text
 developer_id   issue_id   language_overlap   topic_overlap   good_first_issue   difficulty_difference   label
 dev_001        issue_942  0.80                0.50            1                   0.10                    1
 dev_001        issue_517  0.20                0.10            0                   0.75                    0
```

### Scoring new recommendations

For a new user:

1. Build a developer profile from selected public repositories and contributions.
2. Retrieve currently open issues from the selected repository set.
3. Convert each developer-issue pair into the model's feature vector.
4. Predict the probability that each issue is relevant.
5. Apply practical filters, such as issue still being open and repository not being archived.
6. Sort by predicted probability.
7. Display the top results together with the feature-based explanation.

The displayed score should be described as a **match score**, not a guarantee that the developer can complete the issue.

## 4. Data collection strategy

The data collection should support both the recommendation features and the historical labels. Collect data in four related groups:

```text
Repositories
    ↓
Issues and pull requests
    ↓
Developer profiles and contribution links
    ↓
Developer-issue training examples
```

Initially, use a manageable set of approximately 100-200 active repositories. Select repositories from a limited domain, such as Python, web development or AI/ML. This keeps the programming languages, issue types and project characteristics sufficiently consistent for a five-week project.

Use the GitHub REST API or GraphQL API and respect GitHub's rate limits and terms. Store the raw API responses before cleaning them.

## 5. Data that should be collected

### A. Repository table

One row per repository.

| Field              | Example                     | Purpose                        |
| ------------------ | --------------------------- | ------------------------------ |
| `repository_id`    | `repo_001`                  | Internal identifier            |
| `github_full_name` | `fastapi/fastapi`           | GitHub repository reference    |
| `description`      | `A modern web framework...` | Repository text                |
| `readme_text`      | Cleaned README text         | Optional provenance and audit  |
| `primary_language` | `Python`                    | Language matching              |
| `languages`        | `Python, HTML, Shell`       | Full language profile          |
| `topics`           | `api, web, asyncio`         | Domain and technology matching |
| `stars`            | `78000`                     | Popularity/context feature     |
| `forks`            | `6200`                      | Repository context             |
| `open_issue_count` | `410`                       | Availability of opportunities  |
| `is_archived`      | `false`                     | Remove inactive repositories   |
| `created_at`       | `2018-12-01`                | Repository age                 |
| `updated_at`       | `2026-09-08`                | Recent activity                |
| `collected_at`     | `2026-09-10`                | Reproducibility                |

The README should be retained in raw form and also stored as cleaned text. Do not use stars as a measure of developer skill; they are only repository context.

### B. Issue table

One row per issue.

| Field                     | Example                         | Purpose                           |
| ------------------------- | ------------------------------- | --------------------------------- |
| `issue_id`                | `issue_942`                     | Internal identifier               |
| `github_issue_number`     | `942`                           | Original GitHub issue number      |
| `repository_id`           | `repo_001`                      | Repository relationship           |
| `title`                   | `Add pagination to endpoint`    | Issue text                        |
| `body`                    | Cleaned issue description       | Issue text                        |
| `labels`                  | `enhancement, good first issue` | Issue type and difficulty signals |
| `state`                   | `open`                          | Candidate filtering               |
| `created_at`              | `2026-05-02`                    | Temporal features                 |
| `closed_at`               | `null`                          | Resolution information            |
| `comment_count`           | `6`                             | Activity/complexity signal        |
| `author_id`               | `user_456`                      | Optional analysis field           |
| `linked_pull_request_ids` | `pr_119`                        | Outcome relationship              |
| `is_pull_request`         | `false`                         | Exclude PRs from issue candidates |
| `collected_at`            | `2026-09-10`                    | Reproducibility                   |

Collect both current open issues for recommendation and historical issues for training. Historical records should include their state at the relevant time where possible, so future information does not leak into the training features.

### C. Pull-request table

One row per pull request.

| Field             | Example                         | Purpose                    |
| ----------------- | ------------------------------- | -------------------------- |
| `pull_request_id` | `pr_119`                        | Internal identifier        |
| `repository_id`   | `repo_001`                      | Repository relationship    |
| `author_id`       | `user_789`                      | Developer relationship     |
| `linked_issue_id` | `issue_942`                     | Training pair relationship |
| `title`           | `Implement endpoint pagination` | Contribution text          |
| `body`            | PR description                  | Technical content          |
| `state`           | `closed`                        | Outcome information        |
| `merged`          | `true`                          | Positive outcome label     |
| `created_at`      | `2026-05-10`                    | Temporal ordering          |
| `merged_at`       | `2026-05-15`                    | Outcome timing             |
| `commit_count`    | `4`                             | Complexity signal          |
| `changed_files`   | `5`                             | Complexity signal          |
| `additions`       | `120`                           | Contribution size          |
| `deletions`       | `30`                            | Contribution size          |
| `labels`          | `enhancement`                   | Issue/PR context           |
| `collected_at`    | `2026-09-10`                    | Reproducibility            |

The `merged` field is the main outcome signal. A merged PR should not automatically be interpreted as proof that the recommendation algorithm caused the contribution; it is only a historical relevance signal.

### D. Developer profile table

Only collect information needed for the experiment. Avoid storing unnecessary personal data.

| Field                       | Example                   | Purpose                                    |
| --------------------------- | ------------------------- | ------------------------------------------ |
| `developer_id`              | `dev_001`                 | Pseudonymous internal identifier           |
| `github_user_id_hash`       | `hashed_value`            | Link records without exposing the username |
| `public_repository_count`   | `12`                      | Limited experience context                 |
| `languages`                 | `Python, JavaScript, SQL` | Skill profile                              |
| `topics`                    | `api, machine-learning`   | Interest/domain profile                    |
| `contribution_count`        | `18`                      | Activity context                           |
| `merged_pr_count`           | `7`                       | Contribution outcome context               |
| `recent_contribution_count` | `4`                       | Recency                                    |
| `first_contribution_at`     | `2024-03-12`              | Experience duration                        |
| `collected_at`              | `2026-09-10`              | Reproducibility                            |

For the first version, developer profiles can be created from authors of historical pull requests. For the interactive application, a user may optionally connect their GitHub account and provide their public repositories and contribution activity.

### E. Developer-issue interaction table

This is the most important table for supervised learning. It contains one row for each developer-issue pair used for training or evaluation.

| Field                    | Example               | Purpose                            |
| ------------------------ | --------------------- | ---------------------------------- |
| `developer_id`           | `dev_001`             | Developer relationship             |
| `issue_id`               | `issue_942`           | Issue relationship                 |
| `developer_profile_date` | `2026-05-01`          | Prevent future-information leakage |
| `issue_available_date`   | `2026-05-02`          | Confirms the issue was available   |
| `language_overlap`       | `0.80`                | Feature                            |
| `topic_overlap`          | `0.50`                | Feature                            |
| `language_overlap`       | `0.80`                | Feature                            |
| `topic_overlap`          | `0.50`                | Feature                            |
| `good_first_issue`       | `1`                   | Feature                            |
| `difficulty_difference`  | `0.10`                | Feature                            |
| `label`                  | `1`                   | Historical relevance target        |
| `label_source`           | `merged_pull_request` | Label provenance                   |

The interaction table should be generated after cleaning the source tables and engineering the features. It should not be manually edited, because it needs to be reproducible from the raw data.

## 6. Data preprocessing and feature engineering

Apply the following steps:

1. Remove duplicate repositories, issues and pull requests.
2. Exclude archived repositories, bots and deleted records where identifiable.
3. Exclude pull requests from the issue-candidate table.
4. Normalize language names, labels and topic names to lowercase standard forms.
5. Represent missing structured values consistently and record missingness where useful.
6. Encode categorical variables such as languages, topics and labels.
7. Calculate structured overlap features between developer profiles and issues.
8. Estimate issue difficulty using labels and indicators such as changed files, comments and historical resolution time.
9. Calculate developer experience from contribution count, merged pull requests and contribution recency.
10. Scale numeric features and encode categorical features for logistic regression and Linear SVM.
11. Keep all model features limited to structured metadata; do not tokenize, vectorize or otherwise process text for prediction.

Do not use information that would only be known after the recommendation date. For example, when predicting whether an issue available in May would be relevant, do not use its eventual merge status as an input feature. Merge status may be used only as the training label.

## 7. Dataset split and evaluation

Use a chronological split rather than a random split:

```text
Older issues and contributions  -> training set
More recent issues              -> validation set
Newest issues                   -> test set
```

This better represents the real use case: using past GitHub activity to recommend future issues.

Compare at least these systems:

1. Popularity baseline, such as recent repository activity or issue quality.
2. Structured compatibility and popularity baseline.
3. Logistic regression using structured features.
4. Linear SVM using the same structured feature set as a classical comparison model.
5. Random forest or gradient boosting using the same structured feature set.

Use Precision@K, Recall@K, NDCG@K and Mean Reciprocal Rank. Report results for values such as `K = 5` and `K = 10`. Also report how many candidate issues and developer profiles were available, because metric values are difficult to interpret without dataset size.

## 8. Recommended scope for the mini-project

For a realistic first version:

- Collect 100-200 active repositories.
- Focus on one or two technical domains.
- Collect historical issues and pull requests from a defined time window.
- Use merged pull requests as positive examples.
- Use carefully sampled unobserved pairs as negative examples.
- Build the structured compatibility and popularity baseline first.
- Train logistic regression as the main ML model.
- Compare logistic regression with a linear SVM if time allows.
- Compare with a random forest or gradient boosting model if the dataset is large enough.
- Present feature-based explanations instead of claiming that the score is a guaranteed prediction.

This scope gives the project a clear pure-ML component, a reproducible data pipeline and an explainable recommendation system without using NLP, attention-based models, newer neural architectures or a mature user-interaction dataset.
