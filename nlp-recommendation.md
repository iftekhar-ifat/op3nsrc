# Op3nSrc: NLP / Model Plan

How Op3nSrc turns text into recommendations. The overall idea is in **`overall-idea.md`**, data
collection and cleaning in **`data-collection-and-processing.md`**, and a full walkthrough in
**`PROJECT_OVERVIEW.md`**.

---

## 1. Approach

Two steps, both based on text:

```text
Developer profile text
        ↓  (1) text classifier: which repos fit this developer?      ← the ML model, evaluated
Top 5 repos
        ↓  (2) text similarity: which open issues in each repo fit?  ← simple ranking, for display
Top 3 issues per repo + "Why" (shared words)
```

1. **Repo recommendation = text classification.** Input: a developer's text. Output: a probability for
   each repo; the 5 highest are recommended. Trained on the developers in our data.
2. **Issue suggestions = text similarity.** Inside each recommended repo, open issues are ranked by
   TF-IDF cosine similarity to the developer's text, with a small boost for `good first issue` /
   `help wanted`. This step is not trained or evaluated separately.

## 2. Text used

| Text                          | Built from                                                                                                                                                     | Used in                          |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| **Developer text (training)** | the developer's merged-PR titles + descriptions (up to 2,000 chars each, **repo PR-template sentences removed**) + titles of issues they opened; owner names and `owner/repo` strings removed so the label is not given away | classifier training / test       |
| **Developer text (app)**      | the user's GitHub data: bio, own repos (forks skipped: name, description, topics, language), top languages by bytes, merged-PR and issue titles, starred repos | classifier input + issue ranking |
| **Repo text**                 | name, primary language, topics, description, first 5,000 chars of the README                                                                                   | "Why" explanations               |
| **Issue text**                | title + cleaned body (`final_text`) + the repo's name/language/topics/description                                                                              | issue ranking + "Why"            |

Cleaning (see `data-collection-and-processing.md` §6): code blocks, inline code, URLs, images, HTML,
issue-template comments/checklists and markdown syntax removed; lowercase. No stemming — TF-IDF's
stop-word list and `max_df` handle common words.

## 3. Models (all standard, `recommender/models.py`)

| Model                               | How it represents text                                                                     | Classifier                                                 |
| ----------------------------------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| Baseline                            | —                                                                                          | always predicts the most frequent repo (`DummyClassifier`) |
| **TF-IDF + Naive Bayes**            | TF-IDF of words + word pairs (English stop words, `sublinear_tf`, `min_df=2`, `max_df=0.5`) **plus** TF-IDF of character 3–5-grams | `ComplementNB(alpha=0.1)` |
| TF-IDF + Logistic Regression        | same TF-IDF features | `LogisticRegression(C=100)` |
| Sentence-BERT + Logistic Regression | pretrained `all-MiniLM-L6-v2` sentence embeddings (384-d)                                  | `LogisticRegression`                                       |

- **TF-IDF** weights words by how specific they are: rare words like `tokio` or `pydantic` count far
  more than `bug` or `error`.
- **Sentence-BERT** encodes the meaning of a text; it needs no training (pretrained).
- The TF-IDF `max_df=0.5` drops words that appear in more than half of the documents, such as issue-template
  headings ("expected behavior", "steps to reproduce").
- **Word pairs** catch phrases ("async runtime"); **character 3–5-grams** catch code names and their parts
  (`strftime`, `useState`, `webcontents`) even when they are written slightly differently.

## 4. Learning setup

|              |                                                                                   |
| ------------ | --------------------------------------------------------------------------------- |
| One row      | one developer                                                                     |
| Label        | the repo they merged most PRs into                                                |
| Classes      | repos with ≥ 5 developers → **117 repos, 1,724 developers**                       |
| Split        | stratified random **80 / 20** train / test (`random_state = 42`)                  |
| Settings + model choice | 4-fold stratified cross-validation on the training set; small grids (Naive Bayes `alpha` ∈ {0.03, 0.1, 0.3, 1}, Logistic Regression `C` ∈ {10, 30, 100}); chosen by **top-5 accuracy** |
| Final model  | the CV winner (**TF-IDF + Naive Bayes**), retrained on all developers for the app |

Rows are independent (each developer appears once), so a standard random split is valid.

## 5. Evaluation

Standard classification metrics on the test set (`notebooks/classification.ipynb`,
`results/test_results.csv`):

| Model                               | Accuracy | Top-5 accuracy | Macro F1 |
| ----------------------------------- | -------- | -------------- | -------- |
| Most frequent repo (baseline)       | 0.02     | 0.06           | 0.00     |
| **TF-IDF + Naive Bayes**            | 0.75     | **0.88**       | 0.68     |
| TF-IDF + Logistic Regression        | 0.69     | 0.84           | 0.55     |
| Sentence-BERT + Logistic Regression | 0.41     | 0.67           | 0.28     |

- **Accuracy:** the exact repo is the top prediction.
- **Top-5 accuracy:** the true repo is among the 5 recommended — what the app shows.
- **Macro F1:** average quality per repo (small repos count as much as big ones).

**Improvement over the first version** (PR text cut at 500 chars, single words, default settings:
 accuracy 0.51, top-5 0.73, macro F1 0.36): more text per developer, word pairs + character n-grams, and
light tuning. Removing PR-template sentences costs about 5 points of accuracy but keeps the model honest —
it must recognise the developer's work, not the repo's template.

## 6. Issue ranking inside a repo (`recommender/recommend.py`)

```text
score(issue) = cosine(TF-IDF(developer text), TF-IDF(issue text)) + 0.05 × [good first issue or help wanted]
```

Only **open** issues from the 2026-10-01 snapshot are considered; repos without open issues are never
recommended. Titles that are only a template (e.g. "Bug:") are shown with the start of the body.

## 7. Limitations

- Training text (PRs + issue titles) differs from app text (own repos, starred projects), so live recommendations are
  less reliable than the test numbers.
- Only the 117 repos with ≥ 5 developers can be recommended.
- Issue suggestions are not evaluated; they are a convenience step.
- Data is dominated by Python, Go, Rust and JS/TS projects (see `notebooks/eda.ipynb`).

## 8. Timeline

- **Week 1:** Data collection (202 repos, issues, merged PRs).
- **Week 2:** Cleaning, tables, EDA.
- **Week 3:** Classifier dataset, train/test split, models, evaluation; recommender demo with dummy users.
- **Week 4:** Web page; live GitHub fetch (replacing dummy users).
- **Week 5:** Fairness / privacy review, report and presentation.
