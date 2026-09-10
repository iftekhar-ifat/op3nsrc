# Op3nSrc: NLP-Based Recommendation Plan

This document describes the **NLP-based** implementation of Op3nSrc. It uses standard NLP techniques — **TF-IDF** and small pretrained models such as **Sentence-BERT / BERT** — to represent the text of issues, repositories and developer profiles, and recommends issues based on textual and semantic similarity.

The high-level idea shared with the team is described in **`overall-idea.md`**, and the step-by-step data collection/processing workflow is in **`data-collection-and-processing.md`**.

---

## 1. Approach

### 1. Content-based text similarity

Represent the developer's technical experience and each open issue as text, then rank issues by similarity to the developer profile.

```text
Developer experience text (repos, descriptions, commit messages)
                ↕
             Text model (TF-IDF or Sentence-BERT)
                ↕
          Issue title + body
                ↕
           Similarity score
                ↕
            Ranked issues
```

This allows the system to match developers and issues even when they do not share the exact same keywords.

For example:

> Developer: "REST API development"

could match:

> Issue: "Implement pagination for HTTP endpoints"

even if the word "REST" does not appear in the issue, because a pretrained embedding model understands that the two texts are semantically related.

### 2. Models we plan to use

Two tiers of NLP models, both small and standard:

#### A. TF-IDF baseline (no pretrained model needed)

- Use `TfidfVectorizer` (e.g. from scikit-learn) on issue titles/bodies and developer experience text.
- Compute cosine similarity between developer text vectors and issue vectors.
- Fast, fully offline, and a transparent baseline for comparison.

#### B. Small pretrained embeddings (BERT-based)

- Use a small Sentence-BERT model such as **`all-MiniLM-L6-v2`** to embed:
  - Issue title and body.
  - Developer experience text (repositories, topics, descriptions).
- Compare vectors with cosine similarity.
- Captures semantic meaning, so synonyms and paraphrases still match.
- Optionally combine sentence embeddings with single-vector BERT `CLS` pooling for shorter texts.

#### C. Optional: clustering of issues

- Apply K-Means or HDBSCAN on the TF-IDF or embedding vectors to group issues into themes (e.g. backend/API, ML, frontend, documentation, DevOps, testing).
- Cluster assignments can be used to filter candidates before ranking or to visualize the issue ecosystem.

---

## 2. Data collection

The same GitHub data sources described in **`data-collection-and-processing.md`** are used, with extra emphasis on **text fields**, since the NLP models consume text.

### A. Repository table

One row per repository. Text fields used by the NLP models are marked.

| Field              | Example                     | Kept as model text? |
| ------------------ | --------------------------- | ------------------- |
| `repository_id`    | `repo_001`                  | No                  |
| `github_full_name` | `fastapi/fastapi`           | No                  |
| `description`      | `A modern web framework...` | **Yes**             |
| `readme_text`      | Cleaned README text         | **Yes**             |
| `primary_language` | `Python`                    | No                  |
| `languages`        | `Python, HTML, Shell`       | No                  |
| `topics`           | `api, web, asyncio`         | **Yes**             |
| `stars`            | `78000`                     | No                  |
| `forks`            | `6200`                      | No                  |
| `open_issue_count` | `410`                       | No                  |
| `is_archived`      | `false`                     | No                  |
| `created_at`       | `2018-12-01`                | No                  |
| `updated_at`       | `2026-09-08`                | No                  |
| `collected_at`     | `2026-09-10`                | No                  |

### B. Issue table

One row per issue. The title and body are the primary NLP inputs.

| Field                     | Example                         | Kept as model text? |
| ------------------------- | ------------------------------- | ------------------- |
| `issue_id`                | `issue_942`                     | No                  |
| `github_issue_number`     | `942`                           | No                  |
| `repository_id`           | `repo_001`                      | No                  |
| `title`                   | `Add pagination to endpoint`    | **Yes**             |
| `body`                    | Cleaned issue description       | **Yes**             |
| `labels`                  | `enhancement, good first issue` | No                  |
| `state`                   | `open`                          | No                  |
| `created_at`              | `2026-05-02`                    | No                  |
| `closed_at`               | `null`                          | No                  |
| `comment_count`           | `6`                             | No                  |
| `author_id`               | `user_456`                      | No                  |
| `linked_pull_request_ids` | `pr_119`                        | No                  |
| `is_pull_request`         | `false`                         | No                  |
| `collected_at`            | `2026-09-10`                    | No                  |

### C. Pull-request table

PR titles and bodies contribute to the developer's experience text and to historical labels.

| Field             | Example                         | Kept as model text? |
| ----------------- | ------------------------------- | ------------------- |
| `pull_request_id` | `pr_119`                        | No                  |
| `repository_id`   | `repo_001`                      | No                  |
| `author_id`       | `user_789`                      | No                  |
| `linked_issue_id` | `issue_942`                     | No                  |
| `title`           | `Implement endpoint pagination` | **Yes**             |
| `body`            | PR description                  | **Yes**             |
| `state`           | `closed`                        | No                  |
| `merged`          | `true`                          | No (training label) |
| `created_at`      | `2026-05-10`                    | No                  |
| `merged_at`       | `2026-05-15`                    | No                  |
| `commit_count`    | `4`                             | No                  |
| `changed_files`   | `5`                             | No                  |
| `additions`       | `120`                           | No                  |
| `deletions`       | `30`                            | No                  |
| `labels`          | `enhancement`                   | No                  |
| `collected_at`    | `2026-09-10`                    | No                  |

### D. Developer profile text

For each developer, assemble an **experience text document** from public information:

- Repository names, descriptions and topics.
- Issue and PR titles/bodies they wrote.
- Project languages (as text tokens).

This document becomes the developer-side input to the similarity model.

---

## 3. Preprocessing for NLP

The text preprocessing pipeline:

```text
Raw text (issue body, README, descriptions)
    ↓
Strip HTML / Markdown formatting
    ↓
Remove code blocks and URLs
    ↓
Normalize whitespace, lowercase
    ↓
Tokenize, remove stopwords
    ↓
Stem/lemmatize (for TF-IDF only; not needed for pretrained embeddings)
    ↓
Clean text for embedding / vectorization
```

Additional steps:

- For TF-IDF: unigrams and bigrams, with a controlled vocabulary size (e.g. top 5,000 terms) to keep vectors manageable.
- For Sentence-BERT: pass cleaned sentences/paragraphs through the tokenizer; no manual vocabulary is needed.
- Handle very short or empty issue bodies by falling back to the title text.
- Keep raw text stored separately for reproducibility; only cleaned text feeds the models.

---

## 4. Feature construction

The final representation for matching:

```text
Developer Text
        ↓ TF-IDF / Sentence-BERT
Developer vector

Issue Text (title + body + repo topics)
        ↓ TF-IDF / Sentence-BERT
Issue vector
```

Similarity score per pair (cosine similarity):

```text
score(developer, issue) = cosine(dev_vector, issue_vector)
```

Optional hybrid features that remain simple and standard:

- Label boost: add a small bonus for `good first issue` / `help wanted`.
- Repository activity bonus from structured metadata.
- These are combined with the text similarity as a weighted score, not a learned model.

---

## 5. Learning / ranking setup

- **Baseline:** TF-IDF cosine similarity ranking.
- **Advanced:** Sentence-BERT embedding cosine similarity ranking.
- **Optional:** K-Means / HDBSCAN clustering on the same vectors for issue segmentation.

Since the main signals are similarities (not time-indexed), validation still uses a **chronological split** to avoid leaking future information:

```text
Older issues and contributions  -> training set
More recent issues              -> validation set
Newest issues                   -> test set
```

## 6. Evaluation

Metrics (same as the standard-ML approach, so both can be compared fairly):

- Precision@K
- Recall@K
- NDCG@K
- Mean Reciprocal Rank (MRR)
- Hit Rate@K

Report results for `K = 5` and `K = 10`, with the number of candidate issues and profiles available.

## 7. Timeline

- **Week 1:** Collect repositories, issues, PRs and developer text fields.
- **Week 2:** Text preprocessing and EDA (issue text lengths, topic distributions, label distributions).
- **Week 3:** TF-IDF baseline; cosine-similarity ranking.
- **Week 4:** Sentence-BERT embeddings; compare against TF-IDF; optional clustering.
- **Week 5:** Final evaluation, fairness/privacy review, integration into the web app.
