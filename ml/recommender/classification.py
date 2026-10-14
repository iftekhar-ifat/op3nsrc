"""Repo recommendation as text classification: developer profile text -> repo.

One row per developer:
    text  = the developer's merged-PR titles + bodies (repo PR-template sentences
            removed) + titles of issues they opened
    label = the repo they merged most PRs into
Rows are independent, so a standard stratified train/test split is used.
"""

import re
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, top_k_accuracy_score
from sklearn.model_selection import train_test_split

MIN_DEVELOPERS = 5     # a repo needs at least this many developers to be a class
BODY_CHARS = 2000      # use (almost) the full PR description; caps very long logs
TEMPLATE_MIN_PRS = 3   # a sentence in >= 3 PRs of the same repo is PR-template boilerplate
TEST_SIZE = 0.2
SEED = 42

_SENTENCE = re.compile(r"(?<=[.!?:])\s+")


def _leak_pattern(repos):
    """Matches 'owner/repo' strings and owner names (e.g. 'facebook', 'tiangolo').

    These would give away the label. Project/technology words such as
    'react' or 'tokio' are kept: a real user's profile contains them too.
    """
    names = set()
    for rid in list(repos["repo_id"]) + list(repos["current_full_name"]):
        owner = rid.split("/")[0].lower()
        names.add(re.escape(rid.lower()))
        names.add(re.escape(owner))
    return re.compile(r"\b(" + "|".join(sorted(names, key=len, reverse=True)) + r")\b")


def _sentences(text):
    return [s.strip() for s in _SENTENCE.split(text) if len(s.strip()) > 15]


def _without_templates(prs):
    """PR bodies with each repo's PR-template sentences removed.

    Repos have PR templates ("Thanks for contributing! Checklist: ...").
    Those sentences identify the repo, not the developer's skills, so they
    would let the model recognise the template instead of the person.
    """
    sents = prs["body_clean"].map(_sentences)
    template = {}
    for repo, grp in sents.groupby(prs["repo_id"]):
        counts = Counter(s for ss in grp for s in set(ss))
        template[repo] = {s for s, n in counts.items() if n >= TEMPLATE_MIN_PRS}
    return pd.Series([" ".join(s for s in ss if s not in template[r]) for ss, r in zip(sents, prs["repo_id"])],
                     index=prs.index)


def build_dataset(tables, min_developers=MIN_DEVELOPERS):
    """DataFrame with one row per developer: developer, text, repo (label), n_prs."""
    prs, repos, issues = tables["pull_requests"], tables["repositories"], tables["issues"]
    leak = _leak_pattern(repos)
    bodies = _without_templates(prs).str[:BODY_CHARS]
    issue_titles = issues.groupby("author_login")["title_clean"].apply(list)

    rows = []
    for login, grp in prs.groupby("author_login"):
        parts = list(grp["title_clean"] + ". " + bodies[grp.index])
        parts += issue_titles.get(login, [])          # issues they opened (any repo in our data)
        text = " | ".join(parts)
        rows.append({
            "developer": login,
            "text": " ".join(leak.sub(" ", text).split()),
            "repo": grp["repo_id"].value_counts().index[0],     # repo with most PRs
            "n_prs": len(grp),
        })
    df = pd.DataFrame(rows)
    counts = df["repo"].value_counts()
    return df[df["repo"].isin(counts[counts >= min_developers].index)].reset_index(drop=True)


def split(df, test_size=TEST_SIZE, seed=SEED):
    """Stratified random split: every repo appears in train and test in the same proportion."""
    return train_test_split(df, test_size=test_size, stratify=df["repo"], random_state=seed)


def scores(model, X, y):
    """Standard classification metrics; top-5 accuracy = true repo among the 5 most likely."""
    proba = model.predict_proba(X)
    pred = model.classes_[np.argmax(proba, axis=1)]
    return pd.Series({
        "accuracy": accuracy_score(y, pred),
        "top-5 accuracy": top_k_accuracy_score(y, proba, k=5, labels=model.classes_),
        "macro F1": f1_score(y, pred, average="macro", zero_division=0),
        "weighted F1": f1_score(y, pred, average="weighted", zero_division=0),
    })
