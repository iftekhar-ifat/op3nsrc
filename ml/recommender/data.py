"""Load the cleaned tables and build the texts that the models compare."""

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "cleaned"

README_CHARS = 5000   # the start of a README is enough; long READMEs would drown the description

JSON_COLUMNS = {
    "repositories": ["topics", "languages"],
    "issues": ["labels", "linked_pr_ids"],
    "pull_requests": ["labels", "closes_issue_ids", "references_issue_ids", "closes_issue_ids_in_data"],
}
TIME_COLUMNS = {
    "repositories": ["created_at", "pushed_at"],
    "issues": ["created_at", "updated_at", "closed_at"],
    "pull_requests": ["created_at", "merged_at"],
}
BOOL_COLUMNS = {"issues": ["is_beginner_friendly", "is_help_wanted", "created_in_window"]}


COMPACT_COLUMNS = {
    # Fields consumed by the serving recommender. Keeping the crawler's raw
    # payloads out of the API process leaves more memory for inference.
    "repositories": ["repo_id", "current_full_name", "primary_language", "topics",
                    "description_clean", "readme_clean", "html_url", "stars"],
    "issues": ["repo_id", "author_login", "title", "title_clean", "body_clean",
               "final_text", "state", "number", "html_url", "labels",
               "is_beginner_friendly", "is_help_wanted", "created_in_window"],
    "pull_requests": ["repo_id", "author_login", "title_clean", "body_clean",
                      "labels", "closes_issue_ids", "references_issue_ids",
                      "closes_issue_ids_in_data"],
}


def load(name, compact=False):
    """Read one table from data/cleaned/ with JSON, time and bool columns parsed."""
    df = pd.read_csv(
        DATA / f"{name}.csv",
        keep_default_na=False,
        usecols=COMPACT_COLUMNS[name] if compact else None,
    )
    for c in JSON_COLUMNS[name]:
        if c not in df:
            continue
        df[c] = df[c].map(json.loads)
    for c in TIME_COLUMNS[name]:
        if c not in df:
            continue
        df[c] = pd.to_datetime(df[c].replace("", None), utc=True)
    for c in BOOL_COLUMNS.get(name, []):
        if c not in df:
            continue
        df[c] = df[c].astype(str) == "True"
    return df


def load_all(compact=False):
    """Load cleaned tables, optionally selecting only serving-time columns."""
    return {name: load(name, compact=compact) for name in JSON_COLUMNS}


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

_CODE = re.compile(r"```.*?(```|\Z)|`[^`\n]+`", re.DOTALL)
_NOISE = re.compile(r"<!--.*?-->|!\[[^\]]*\]\([^)]*\)|<[^>]+>|https?://\S+", re.DOTALL)
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def clean_text(raw):
    """Light cleaning for raw GitHub text (user data): no code, URLs, markdown; lowercase."""
    t = _CODE.sub(" ", raw or "")
    t = _LINK.sub(r"\1", _NOISE.sub(" ", t))
    t = re.sub(r"[#>*_|]", " ", t)
    return " ".join(t.lower().split())


def name_words(full_name):
    """'tiangolo/fastapi' -> 'tiangolo fastapi'; 'react-native' -> 'react native'."""
    return re.sub(r"[/_.-]", " ", full_name.lower())


def repo_context(repos):
    """Short description of each repo: name, language, topics, description."""
    return {r.repo_id: " ".join([name_words(r.repo_id), r.primary_language,
                                 " ".join(r.topics), r.description_clean])
            for r in repos.itertuples()}


def repo_texts(repos):
    """Repo document = context + start of the README (one per row of `repos`)."""
    ctx = repo_context(repos)
    return [f"{ctx[r.repo_id]} {r.readme_clean[:README_CHARS]}" for r in repos.itertuples()]


def issue_texts(issues, repos):
    """Issue document = title + body (final_text) + the context of its repo."""
    ctx = repo_context(repos)
    return list(issues["final_text"] + " | " + issues["repo_id"].map(ctx))
